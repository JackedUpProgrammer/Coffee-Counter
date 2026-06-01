from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "coffee_counter.sqlite3"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_connection()) as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS coffees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                cups INTEGER NOT NULL CHECK (cups > 0),
                coffee_date TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );

            CREATE TABLE IF NOT EXISTS coffee_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coffee_id INTEGER NOT NULL,
                reviewer_id INTEGER NOT NULL,
                approved INTEGER NOT NULL CHECK (approved IN (0, 1)),
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (coffee_id, reviewer_id),
                FOREIGN KEY (coffee_id) REFERENCES coffees(id),
                FOREIGN KEY (reviewer_id) REFERENCES employees(id)
            );
            """
        )
        conn.commit()


def add_employee(name: str) -> tuple[bool, str]:
    cleaned_name = " ".join(name.strip().split())
    if not cleaned_name:
        return False, "Enter an employee name."

    try:
        with closing(get_connection()) as conn:
            conn.execute("INSERT INTO employees (name) VALUES (?)", (cleaned_name,))
            conn.commit()
        return True, f"Added {cleaned_name}."
    except sqlite3.IntegrityError:
        return False, f"{cleaned_name} already exists."


def get_employees(active_only: bool = True) -> pd.DataFrame:
    query = "SELECT id, name, active FROM employees"
    params: tuple[int, ...] = ()
    if active_only:
        query += " WHERE active = ?"
        params = (1,)
    query += " ORDER BY name"

    with closing(get_connection()) as conn:
        return pd.read_sql_query(query, conn, params=params)


def set_employee_active(employee_id: int, active: bool) -> None:
    with closing(get_connection()) as conn:
        conn.execute(
            "UPDATE employees SET active = ? WHERE id = ?",
            (1 if active else 0, employee_id),
        )
        conn.commit()


def add_coffee(employee_id: int, cups: int, coffee_date: date, note: str) -> None:
    with closing(get_connection()) as conn:
        conn.execute(
            """
            INSERT INTO coffees (employee_id, cups, coffee_date, note)
            VALUES (?, ?, ?, ?)
            """,
            (employee_id, cups, coffee_date.isoformat(), note.strip() or None),
        )
        conn.commit()


def add_review(coffee_id: int, reviewer_id: int, approved: bool, rating: int) -> None:
    with closing(get_connection()) as conn:
        conn.execute(
            """
            INSERT INTO coffee_reviews (coffee_id, reviewer_id, approved, rating)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(coffee_id, reviewer_id)
            DO UPDATE SET
                approved = excluded.approved,
                rating = excluded.rating,
                created_at = CURRENT_TIMESTAMP
            """,
            (coffee_id, reviewer_id, 1 if approved else 0, rating),
        )
        conn.commit()


def get_reviewed_coffee_ids() -> set[int]:
    with closing(get_connection()) as conn:
        rows = conn.execute(
            """
            SELECT c.id
            FROM coffees c
            LEFT JOIN employees maker ON maker.id = c.employee_id
            LEFT JOIN employees reviewer ON reviewer.active = 1 AND reviewer.id != c.employee_id
            LEFT JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.reviewer_id = reviewer.id
            GROUP BY c.id
            HAVING
                COUNT(reviewer.id) = COUNT(cr.id)
                AND COALESCE(MIN(cr.approved), 1) = 1
            """
        ).fetchall()
        return {int(row["id"]) for row in rows}


def get_rejected_coffee_ids() -> set[int]:
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT DISTINCT coffee_id FROM coffee_reviews WHERE approved = 0"
        ).fetchall()
        return {int(row["coffee_id"]) for row in rows}


def get_totals() -> pd.DataFrame:
    approved_ids = get_reviewed_coffee_ids()
    id_filter = ",".join("?" for _ in approved_ids) or "NULL"
    params = tuple(approved_ids) + tuple(approved_ids)

    with closing(get_connection()) as conn:
        return pd.read_sql_query(
            f"""
            SELECT
                e.id AS employee_id,
                e.name AS employee,
                COALESCE(cup_stats.approved_cups, 0) AS approved_cups,
                COALESCE(cup_stats.today_cups, 0) AS today_cups,
                COALESCE(cup_stats.last_7_days, 0) AS last_7_days,
                rating_stats.average_rating
            FROM employees e
            LEFT JOIN (
                SELECT
                    employee_id,
                    SUM(cups) AS approved_cups,
                    SUM(CASE WHEN coffee_date = DATE('now', 'localtime') THEN cups ELSE 0 END) AS today_cups,
                    SUM(CASE WHEN coffee_date >= DATE('now', 'localtime', '-6 days') THEN cups ELSE 0 END) AS last_7_days
                FROM coffees
                WHERE id IN ({id_filter})
                GROUP BY employee_id
            ) cup_stats ON cup_stats.employee_id = e.id
            LEFT JOIN (
                SELECT
                    c.employee_id,
                    ROUND(AVG(cr.rating), 2) AS average_rating
                FROM coffees c
                JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.approved = 1
                WHERE c.id IN ({id_filter})
                GROUP BY c.employee_id
            ) rating_stats ON rating_stats.employee_id = e.id
            WHERE e.active = 1
            GROUP BY e.id, e.name
            ORDER BY approved_cups DESC, e.name
            """,
            conn,
            params=params,
        )


def get_pending_review_count() -> int:
    with closing(get_connection()) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS pending
            FROM coffees c
            JOIN employees maker ON maker.id = c.employee_id AND maker.active = 1
            JOIN employees reviewer ON reviewer.active = 1 AND reviewer.id != c.employee_id
            LEFT JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.reviewer_id = reviewer.id
            WHERE cr.id IS NULL
            """
        ).fetchone()
        return int(row["pending"])


def get_total_approved_cups() -> int:
    approved_ids = get_reviewed_coffee_ids()
    if not approved_ids:
        return 0

    placeholders = ",".join("?" for _ in approved_ids)
    with closing(get_connection()) as conn:
        row = conn.execute(
            f"SELECT COALESCE(SUM(cups), 0) AS total FROM coffees WHERE id IN ({placeholders})",
            tuple(approved_ids),
        ).fetchone()
        return int(row["total"])


def get_recent_entries(limit: int = 100) -> pd.DataFrame:
    approved_ids = get_reviewed_coffee_ids()
    rejected_ids = get_rejected_coffee_ids()

    with closing(get_connection()) as conn:
        entries = pd.read_sql_query(
            """
            SELECT
                c.id,
                c.coffee_date AS date,
                e.name AS employee,
                c.cups,
                COALESCE(c.note, '') AS note,
                c.created_at,
                COUNT(reviewer.id) AS required_reviews,
                COUNT(cr.id) AS completed_reviews,
                ROUND(AVG(cr.rating), 2) AS average_rating
            FROM coffees c
            JOIN employees e ON e.id = c.employee_id
            LEFT JOIN employees reviewer ON reviewer.active = 1 AND reviewer.id != c.employee_id
            LEFT JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.reviewer_id = reviewer.id
            GROUP BY c.id, c.coffee_date, e.name, c.cups, c.note, c.created_at
            ORDER BY c.coffee_date DESC, c.created_at DESC
            LIMIT ?
            """,
            conn,
            params=(limit,),
        )

    if entries.empty:
        return entries

    def status_for(entry_id: int) -> str:
        if entry_id in rejected_ids:
            return "Rejected"
        if entry_id in approved_ids:
            return "Approved"
        return "Pending"

    entries["status"] = entries["id"].apply(status_for)
    return entries


def get_review_queue(reviewer_id: int) -> pd.DataFrame:
    with closing(get_connection()) as conn:
        return pd.read_sql_query(
            """
            SELECT
                c.id,
                c.coffee_date AS date,
                e.name AS employee,
                c.cups,
                COALESCE(c.note, '') AS note
            FROM coffees c
            JOIN employees e ON e.id = c.employee_id
            LEFT JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.reviewer_id = ?
            WHERE c.employee_id != ?
                AND e.active = 1
                AND cr.id IS NULL
                AND c.id NOT IN (SELECT coffee_id FROM coffee_reviews WHERE approved = 0)
            ORDER BY c.coffee_date ASC, c.created_at ASC
            """,
            conn,
            params=(reviewer_id, reviewer_id),
        )


def choose_next_maker(totals: pd.DataFrame) -> tuple[str, str]:
    if totals.empty:
        return "None yet", "Add active employees first."

    ranked = totals.copy()
    ranked["approved_cups"] = ranked["approved_cups"].fillna(0).astype(int)
    ranked["average_rating"] = ranked["average_rating"].fillna(0.0).astype(float)
    ranked = ranked.sort_values(
        by=["approved_cups", "average_rating", "employee"],
        ascending=[True, True, True],
    )
    next_maker = ranked.iloc[0]
    lowest_cups = int(next_maker["approved_cups"])
    tied_on_cups = ranked[ranked["approved_cups"] == lowest_cups]

    if len(tied_on_cups) == len(ranked):
        reason = "Everyone is tied on approved cups, so the lowest average rating breaks the tie."
    elif len(tied_on_cups) > 1:
        reason = "These employees are behind on approved cups, so the lowest average rating breaks the tie."
    else:
        reason = "This employee is behind on approved cups."

    return str(next_maker["employee"]), reason


def render_add_employee() -> None:
    with st.form("add_employee", clear_on_submit=True):
        name = st.text_input("Employee name")
        submitted = st.form_submit_button("Add employee", type="primary")

    if submitted:
        ok, message = add_employee(name)
        if ok:
            st.success(message)
            st.rerun()
        else:
            st.warning(message)


def render_record_coffee(employees: pd.DataFrame) -> None:
    if employees.empty:
        st.info("Add at least one employee before recording coffees.")
        return

    employee_options = dict(zip(employees["name"], employees["id"]))

    with st.form("record_coffee", clear_on_submit=True):
        selected_name = st.selectbox("Employee who made coffee", employee_options.keys())
        cups = st.number_input("Cups made", min_value=1, max_value=50, value=1, step=1)
        coffee_date = st.date_input("Date", value=date.today())
        note = st.text_input("Note", placeholder="Optional")
        submitted = st.form_submit_button("Submit for approval", type="primary")

    if submitted:
        add_coffee(employee_options[selected_name], int(cups), coffee_date, note)
        st.success("Coffee logged. It will count after all other active employees approve and rate it.")
        st.rerun()


def render_review_queue(employees: pd.DataFrame) -> None:
    st.subheader("Approve and rate coffees")
    if len(employees) < 2:
        st.caption("At least two active employees are needed for approvals.")
        return

    employee_options = dict(zip(employees["name"], employees["id"]))
    reviewer_name = st.selectbox("Reviewer", employee_options.keys(), key="reviewer")
    queue = get_review_queue(employee_options[reviewer_name])

    if queue.empty:
        st.caption("No coffees waiting for this reviewer.")
        return

    labels = {
        f"{row.date} - {row.employee} - {row.cups} cup{'s' if row.cups != 1 else ''}": row.id
        for row in queue.itertuples(index=False)
    }

    with st.form("review_coffee"):
        selected = st.selectbox("Coffee to review", labels.keys())
        approved = st.checkbox("Approve this coffee", value=True)
        rating = st.slider("Rating", min_value=1, max_value=5, value=3)
        submitted = st.form_submit_button("Save review", type="primary")

    if submitted:
        add_review(labels[selected], employee_options[reviewer_name], approved, rating)
        st.success("Review saved.")
        st.rerun()


def render_employee_management() -> None:
    employees = get_employees(active_only=False)
    if employees.empty:
        st.caption("No employees yet.")
        return

    st.subheader("Employees")
    for employee in employees.itertuples(index=False):
        cols = st.columns([3, 1])
        status = "Active" if employee.active else "Archived"
        cols[0].write(f"{employee.name} - {status}")
        button_label = "Archive" if employee.active else "Restore"
        if cols[1].button(button_label, key=f"toggle_{employee.id}"):
            set_employee_active(employee.id, not bool(employee.active))
            st.rerun()


def render_leaderboard(totals: pd.DataFrame) -> None:
    st.subheader("Approved coffee totals")
    if totals.empty:
        st.caption("No active employees yet.")
        return

    display = totals.rename(
        columns={
            "employee": "Employee",
            "approved_cups": "Approved cups",
            "today_cups": "Today",
            "last_7_days": "Last 7 days",
            "average_rating": "Average rating",
        }
    ).drop(columns=["employee_id"])

    st.dataframe(display, hide_index=True, use_container_width=True)

    chart_data = totals.set_index("employee")["approved_cups"]
    if int(chart_data.sum()) > 0:
        st.bar_chart(chart_data)


def render_recent_entries() -> None:
    st.subheader("Recent coffee logs")
    entries = get_recent_entries()
    if entries.empty:
        st.caption("No coffees recorded yet.")
        return

    display = entries.rename(
        columns={
            "date": "Date",
            "employee": "Employee",
            "cups": "Cups",
            "note": "Note",
            "required_reviews": "Required reviews",
            "completed_reviews": "Completed reviews",
            "average_rating": "Average rating",
            "status": "Status",
        }
    ).drop(columns=["id", "created_at"])

    st.dataframe(display, hide_index=True, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Coffee Counter", layout="wide")
    init_db()

    st.title("Coffee Counter")
    st.caption("Track in-house coffees by employee, with peer approval before anything counts.")

    employees = get_employees()
    totals = get_totals()
    next_maker, next_reason = choose_next_maker(totals)

    metric_cols = st.columns(4)
    metric_cols[0].metric("Approved cups", get_total_approved_cups())
    metric_cols[1].metric("Active employees", len(employees))
    metric_cols[2].metric("Pending reviews", get_pending_review_count())
    metric_cols[3].metric("Next coffee maker", next_maker)
    st.caption(next_reason)

    st.divider()

    left, right = st.columns([1, 2])
    with left:
        st.subheader("Record coffee")
        render_record_coffee(employees)
        st.divider()
        render_review_queue(employees)
        st.divider()
        st.subheader("Add employee")
        render_add_employee()
        st.divider()
        render_employee_management()

    with right:
        render_leaderboard(totals)
        st.divider()
        render_recent_entries()


if __name__ == "__main__":
    main()
