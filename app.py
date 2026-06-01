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


def delete_coffee(entry_id: int) -> None:
    with closing(get_connection()) as conn:
        conn.execute("DELETE FROM coffees WHERE id = ?", (entry_id,))
        conn.commit()


def get_totals() -> pd.DataFrame:
    with closing(get_connection()) as conn:
        return pd.read_sql_query(
            """
            SELECT
                e.name AS employee,
                COALESCE(SUM(c.cups), 0) AS total_cups,
                COALESCE(SUM(CASE WHEN c.coffee_date = DATE('now', 'localtime') THEN c.cups ELSE 0 END), 0) AS today_cups,
                COALESCE(SUM(CASE WHEN c.coffee_date >= DATE('now', 'localtime', '-6 days') THEN c.cups ELSE 0 END), 0) AS last_7_days
            FROM employees e
            LEFT JOIN coffees c ON c.employee_id = e.id
            WHERE e.active = 1
            GROUP BY e.id, e.name
            ORDER BY total_cups DESC, e.name
            """,
            conn,
        )


def get_recent_entries(limit: int = 100) -> pd.DataFrame:
    with closing(get_connection()) as conn:
        return pd.read_sql_query(
            """
            SELECT
                c.id,
                c.coffee_date AS date,
                e.name AS employee,
                c.cups,
                COALESCE(c.note, '') AS note,
                c.created_at
            FROM coffees c
            JOIN employees e ON e.id = c.employee_id
            ORDER BY c.coffee_date DESC, c.created_at DESC
            LIMIT ?
            """,
            conn,
            params=(limit,),
        )


def get_total_cups() -> int:
    with closing(get_connection()) as conn:
        row = conn.execute("SELECT COALESCE(SUM(cups), 0) AS total FROM coffees").fetchone()
        return int(row["total"])


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
        selected_name = st.selectbox("Employee", employee_options.keys())
        cups = st.number_input("Cups", min_value=1, max_value=20, value=1, step=1)
        coffee_date = st.date_input("Date", value=date.today())
        note = st.text_input("Note", placeholder="Optional")
        submitted = st.form_submit_button("Record coffee", type="primary")

    if submitted:
        add_coffee(employee_options[selected_name], int(cups), coffee_date, note)
        st.success(f"Recorded {cups} cup{'s' if cups != 1 else ''} for {selected_name}.")
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
    st.subheader("Coffee totals")
    if totals.empty:
        st.caption("No active employees yet.")
        return

    st.dataframe(
        totals.rename(
            columns={
                "employee": "Employee",
                "total_cups": "Total cups",
                "today_cups": "Today",
                "last_7_days": "Last 7 days",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    chart_data = totals.set_index("employee")["total_cups"]
    if int(chart_data.sum()) > 0:
        st.bar_chart(chart_data)


def render_recent_entries() -> None:
    st.subheader("Recent entries")
    entries = get_recent_entries()
    if entries.empty:
        st.caption("No coffees recorded yet.")
        return

    st.dataframe(
        entries.drop(columns=["id", "created_at"]).rename(
            columns={
                "date": "Date",
                "employee": "Employee",
                "cups": "Cups",
                "note": "Note",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    with st.expander("Fix a mistaken entry"):
        entry_labels = {
            f"{row.date} - {row.employee} - {row.cups} cup{'s' if row.cups != 1 else ''}": row.id
            for row in entries.itertuples(index=False)
        }
        selected = st.selectbox("Entry to delete", entry_labels.keys())
        if st.button("Delete selected entry", type="secondary"):
            delete_coffee(entry_labels[selected])
            st.success("Entry deleted.")
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="Coffee Counter", layout="wide")
    init_db()

    st.title("Coffee Counter")
    st.caption("Track in-house coffees by employee and keep the tally honest.")

    employees = get_employees()
    totals = get_totals()

    total_cups = get_total_cups()
    active_employees = len(employees)
    top_drinker = totals.iloc[0]["employee"] if not totals.empty and totals.iloc[0]["total_cups"] > 0 else "None yet"

    metric_cols = st.columns(3)
    metric_cols[0].metric("Total cups", total_cups)
    metric_cols[1].metric("Active employees", active_employees)
    metric_cols[2].metric("Top counter", top_drinker)

    st.divider()

    left, right = st.columns([1, 2])
    with left:
        st.subheader("Record coffee")
        render_record_coffee(employees)
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
