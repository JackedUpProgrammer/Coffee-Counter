from __future__ import annotations

import hashlib
import hmac
import random
import sqlite3
import string
from contextlib import closing
from datetime import date
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "coffee_counter.sqlite3"
PASSWORD_SALT = b"coffee-counter-admin-v1"
PASSWORD_ITERATIONS = 260000
ADMIN_NAME = "admin"
ADMIN_PASSWORD_HASH = "44a09039f5a01f0c0fbff626c196ef6cd4a58625ceb6b0a7fac4599975b1d691"


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def inject_styles() -> None:
    st.markdown(
        """
<style>
:root {
--coffee-bg: #071018;
--coffee-panel: rgba(12, 25, 36, 0.82);
--coffee-panel-strong: rgba(17, 36, 50, 0.95);
--coffee-ink: #edf7fb;
--coffee-muted: #9db1bf;
--coffee-line: rgba(132, 204, 255, 0.18);
--coffee-accent: #38d9c4;
--coffee-accent-dark: #17a998;
--coffee-warm: #ffc857;
--coffee-danger: #ff6b8a;
}

[data-testid="stAppViewContainer"] {
background:
radial-gradient(circle at 14% 8%, rgba(56, 217, 196, 0.18), transparent 32rem),
radial-gradient(circle at 86% 0%, rgba(255, 200, 87, 0.13), transparent 30rem),
linear-gradient(135deg, #071018 0%, #0b1621 48%, #05080d 100%);
}

[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stDeployButton"] {
display: none;
}

.block-container {
max-width: 1220px;
padding-top: 1.6rem;
padding-bottom: 3rem;
}

h1, h2, h3 {
color: var(--coffee-ink);
letter-spacing: 0;
}

h1 {
font-size: 2.55rem;
font-weight: 800;
margin-bottom: 0.45rem;
text-shadow: 0 0 28px rgba(56, 217, 196, 0.2);
}

h2, h3 {
font-weight: 700;
}

p, label, [data-testid="stMarkdownContainer"] {
color: var(--coffee-muted);
}

[data-testid="stCaptionContainer"] {
color: var(--coffee-muted);
}

div[data-testid="stMetric"] {
background: var(--coffee-panel);
border: 1px solid var(--coffee-line);
border-radius: 8px;
padding: 0.85rem 1rem;
box-shadow: 0 18px 46px rgba(0, 0, 0, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.04);
backdrop-filter: blur(14px);
}

div[data-testid="stMetricLabel"] p {
color: var(--coffee-muted);
font-size: 0.8rem;
text-transform: uppercase;
letter-spacing: 0.04em;
font-weight: 750;
}

div[data-testid="stMetricValue"] {
color: var(--coffee-ink);
font-weight: 750;
}

[data-testid="stVerticalBlockBorderWrapper"] {
border-color: var(--coffee-line);
border-radius: 8px;
background: var(--coffee-panel);
box-shadow: 0 20px 60px rgba(0, 0, 0, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.04);
backdrop-filter: blur(16px);
}

div[data-baseweb="tab-list"] {
gap: 0.35rem;
border-bottom: 1px solid var(--coffee-line);
padding-bottom: 0.65rem;
}

div[data-baseweb="tab-highlight"] {
display: none;
}

button[data-baseweb="tab"] {
border-radius: 7px;
color: var(--coffee-muted);
font-weight: 650;
background: rgba(255, 255, 255, 0.03);
min-width: 5.25rem;
min-height: 2.35rem;
padding: 0.45rem 0.8rem;
display: inline-flex;
align-items: center;
justify-content: center;
border: 1px solid var(--coffee-line);
}

button[data-baseweb="tab"][aria-selected="true"] {
color: #061115 !important;
background: linear-gradient(135deg, var(--coffee-accent), #9df6e7) !important;
border-color: rgba(56, 217, 196, 0.7);
}

.stButton button,
.stFormSubmitButton button {
border-radius: 7px;
font-weight: 650;
border-color: var(--coffee-line);
background: rgba(255, 255, 255, 0.04);
color: var(--coffee-ink);
}

.stButton button[kind="primary"],
.stFormSubmitButton button[kind="primary"] {
background: linear-gradient(135deg, var(--coffee-accent), #a7f6ea);
border-color: var(--coffee-accent);
color: #061115;
box-shadow: 0 12px 34px rgba(56, 217, 196, 0.2);
}

.stButton button[kind="primary"]:hover,
.stFormSubmitButton button[kind="primary"]:hover {
background: linear-gradient(135deg, var(--coffee-accent-dark), #62ead9);
border-color: var(--coffee-accent-dark);
}

input, textarea, [data-baseweb="select"] > div {
background: rgba(255, 255, 255, 0.04) !important;
border-color: var(--coffee-line) !important;
color: var(--coffee-ink) !important;
}

[data-testid="stDataFrame"] {
border: 1px solid var(--coffee-line);
border-radius: 8px;
overflow: hidden;
}

[data-testid="stExpander"] {
border-color: var(--coffee-line);
background: rgba(255, 255, 255, 0.03);
border-radius: 8px;
}

.next-maker {
position: relative;
overflow: hidden;
background:
linear-gradient(135deg, rgba(56, 217, 196, 0.18), rgba(255, 200, 87, 0.08)),
var(--coffee-panel-strong);
border: 1px solid rgba(56, 217, 196, 0.34);
border-radius: 8px;
padding: 1.25rem 1.35rem;
margin-bottom: 1rem;
box-shadow: 0 22px 70px rgba(0, 0, 0, 0.32), 0 0 42px rgba(56, 217, 196, 0.08);
backdrop-filter: blur(16px);
}

.next-maker:before {
content: "";
position: absolute;
inset: 0;
background: linear-gradient(90deg, transparent, rgba(255,255,255,0.09), transparent);
transform: translateX(-70%);
pointer-events: none;
}

.next-maker-label {
color: var(--coffee-accent);
font-size: 0.78rem;
font-weight: 750;
letter-spacing: 0.08em;
text-transform: uppercase;
margin-bottom: 0.2rem;
}

.next-maker-name {
color: var(--coffee-ink);
font-size: 1.8rem;
font-weight: 800;
line-height: 1.15;
margin-bottom: 0.25rem;
}

.next-maker-reason {
color: var(--coffee-muted);
font-size: 0.95rem;
margin: 0;
}

.hero-row {
display: flex;
align-items: flex-end;
justify-content: space-between;
gap: 1rem;
margin-bottom: 1rem;
}

.hero-kicker {
color: var(--coffee-accent);
font-size: 0.78rem;
font-weight: 800;
letter-spacing: 0.12em;
text-transform: uppercase;
margin-bottom: 0.2rem;
}

.hero-copy {
color: var(--coffee-muted);
margin: 0;
max-width: 40rem;
}

.status-pill {
border: 1px solid rgba(56, 217, 196, 0.35);
border-radius: 999px;
color: var(--coffee-accent);
background: rgba(56, 217, 196, 0.08);
padding: 0.45rem 0.75rem;
font-size: 0.8rem;
font-weight: 750;
white-space: nowrap;
}

@media (max-width: 760px) {
.block-container {
padding-top: 1rem;
}

div[data-testid="stMetric"] {
padding: 0.75rem 0.85rem;
}

.hero-row {
display: block;
}

.status-pill {
display: inline-block;
margin-top: 0.8rem;
}

h1 {
font-size: 2rem;
}

button[data-baseweb="tab"] {
min-width: auto;
padding-left: 0.7rem;
padding-right: 0.7rem;
}
}
</style>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        PASSWORD_SALT,
        PASSWORD_ITERATIONS,
    ).hex()


def init_db() -> None:
    with closing(get_connection()) as conn:
        conn.executescript(
            """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1,
    team_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id)
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

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    employee_id INTEGER UNIQUE,
    is_admin INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
"""
        )

        # Migration: add team_id column if upgrading from older schema
        cols = [
            row["name"]
            for row in conn.execute("PRAGMA table_info(employees)").fetchall()
        ]
        if "team_id" not in cols:
            conn.execute("ALTER TABLE employees ADD COLUMN team_id INTEGER REFERENCES teams(id)")

        # Ensure admin user exists
        conn.execute(
            """
INSERT INTO users (name, password_hash, is_admin)
VALUES (?, ?, 1)
ON CONFLICT(name) DO UPDATE SET
    password_hash = excluded.password_hash,
    is_admin = 1
""",
            (ADMIN_NAME, ADMIN_PASSWORD_HASH),
        )
        # Revoke admin from everyone else
        conn.execute("UPDATE users SET is_admin = 0 WHERE name != ?", (ADMIN_NAME,))
        conn.commit()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def authenticate_user(name: str, password: str) -> sqlite3.Row | None:
    cleaned_name = " ".join(name.strip().split())
    if not cleaned_name or not password:
        return None

    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT id, name, password_hash, employee_id, is_admin FROM users WHERE name = ?",
            (cleaned_name,),
        ).fetchone()

    if row and hmac.compare_digest(row["password_hash"], hash_password(password)):
        return row
    return None


def register_user(name: str, password: str) -> tuple[bool, str]:
    cleaned_name = " ".join(name.strip().split())
    if not cleaned_name:
        return False, "Enter your name."
    if cleaned_name.lower() == ADMIN_NAME.lower():
        return False, "That name is reserved."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    try:
        with closing(get_connection()) as conn:
            cursor = conn.execute(
                "INSERT INTO employees (name) VALUES (?)", (cleaned_name,)
            )
            employee_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO users (name, password_hash, employee_id) VALUES (?, ?, ?)",
                (cleaned_name, hash_password(password), employee_id),
            )
            conn.commit()
        return True, f"Account created! Sign in as {cleaned_name}."
    except sqlite3.IntegrityError:
        return False, f"{cleaned_name} already exists."


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------

def generate_team_code() -> str:
    with closing(get_connection()) as conn:
        for _ in range(100):
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            exists = conn.execute(
                "SELECT 1 FROM teams WHERE code = ?", (code,)
            ).fetchone()
            if not exists:
                return code
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def create_team(name: str, employee_id: int) -> tuple[bool, str]:
    cleaned_name = " ".join(name.strip().split())
    if not cleaned_name:
        return False, "Enter a team name."

    code = generate_team_code()
    try:
        with closing(get_connection()) as conn:
            cursor = conn.execute(
                "INSERT INTO teams (name, code) VALUES (?, ?)", (cleaned_name, code)
            )
            team_id = cursor.lastrowid
            conn.execute(
                "UPDATE employees SET team_id = ? WHERE id = ?", (team_id, employee_id)
            )
            conn.commit()
        return True, f"Team **{cleaned_name}** created! Invite code: **{code}**"
    except sqlite3.IntegrityError:
        return False, "Could not create team. Try again."


def join_team(code: str, employee_id: int) -> tuple[bool, str]:
    cleaned_code = code.strip().upper()
    if not cleaned_code:
        return False, "Enter an invite code."

    with closing(get_connection()) as conn:
        team = conn.execute(
            "SELECT id, name FROM teams WHERE code = ?", (cleaned_code,)
        ).fetchone()
        if not team:
            return False, "No team found with that code."
        conn.execute(
            "UPDATE employees SET team_id = ? WHERE id = ?", (team["id"], employee_id)
        )
        conn.commit()
    return True, f"Joined **{team['name']}**!"


def get_user_team(employee_id: int | None) -> dict | None:
    if employee_id is None:
        return None
    with closing(get_connection()) as conn:
        row = conn.execute(
            """
SELECT t.id, t.name, t.code
FROM teams t
JOIN employees e ON e.team_id = t.id
WHERE e.id = ?
""",
            (employee_id,),
        ).fetchone()
    if row:
        return {"id": row["id"], "name": row["name"], "code": row["code"]}
    return None


# ---------------------------------------------------------------------------
# Employee helpers
# ---------------------------------------------------------------------------

def get_team_employees(team_id: int, active_only: bool = True) -> pd.DataFrame:
    query = "SELECT id, name, active FROM employees WHERE team_id = ?"
    params: list = [team_id]
    if active_only:
        query += " AND active = 1"
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


# ---------------------------------------------------------------------------
# Coffee & review helpers
# ---------------------------------------------------------------------------

def add_coffee(employee_id: int, cups: int, coffee_date: date, note: str) -> None:
    with closing(get_connection()) as conn:
        conn.execute(
            "INSERT INTO coffees (employee_id, cups, coffee_date, note) VALUES (?, ?, ?, ?)",
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


def get_reviewed_coffee_ids(team_id: int) -> set[int]:
    with closing(get_connection()) as conn:
        rows = conn.execute(
            """
SELECT c.id
FROM coffees c
JOIN employees maker ON maker.id = c.employee_id AND maker.team_id = ?
LEFT JOIN employees reviewer ON reviewer.active = 1
    AND reviewer.team_id = ? AND reviewer.id != c.employee_id
LEFT JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.reviewer_id = reviewer.id
GROUP BY c.id
HAVING COUNT(reviewer.id) > 0
    AND COUNT(reviewer.id) = COUNT(cr.id)
    AND MIN(cr.approved) = 1
""",
            (team_id, team_id),
        ).fetchall()
    return {int(row["id"]) for row in rows}


def get_rejected_coffee_ids(team_id: int) -> set[int]:
    with closing(get_connection()) as conn:
        rows = conn.execute(
            """
SELECT DISTINCT cr.coffee_id
FROM coffee_reviews cr
JOIN coffees c ON c.id = cr.coffee_id
JOIN employees e ON e.id = c.employee_id AND e.team_id = ?
WHERE cr.approved = 0
""",
            (team_id,),
        ).fetchall()
    return {int(row["coffee_id"]) for row in rows}


def get_totals(team_id: int) -> pd.DataFrame:
    approved_ids = get_reviewed_coffee_ids(team_id)

    if not approved_ids:
        with closing(get_connection()) as conn:
            employees = pd.read_sql_query(
                "SELECT id AS employee_id, name AS employee FROM employees WHERE team_id = ? AND active = 1 ORDER BY name",
                conn,
                params=(team_id,),
            )
        if employees.empty:
            return pd.DataFrame(
                columns=["employee_id", "employee", "approved_cups", "today_cups", "last_7_days", "average_rating"]
            )
        employees["approved_cups"] = 0
        employees["today_cups"] = 0
        employees["last_7_days"] = 0
        employees["average_rating"] = None
        return employees

    id_filter = ",".join("?" for _ in approved_ids)
    params = tuple(approved_ids) + tuple(approved_ids) + (team_id,)

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
WHERE e.active = 1 AND e.team_id = ?
GROUP BY e.id, e.name
ORDER BY approved_cups DESC, e.name
""",
            conn,
            params=params,
        )


def get_total_approved_cups(team_id: int) -> int:
    approved_ids = get_reviewed_coffee_ids(team_id)
    if not approved_ids:
        return 0
    placeholders = ",".join("?" for _ in approved_ids)
    with closing(get_connection()) as conn:
        row = conn.execute(
            f"SELECT COALESCE(SUM(cups), 0) AS total FROM coffees WHERE id IN ({placeholders})",
            tuple(approved_ids),
        ).fetchone()
    return int(row["total"])


def get_pending_review_count_for_user(employee_id: int, team_id: int) -> int:
    with closing(get_connection()) as conn:
        row = conn.execute(
            """
SELECT COUNT(*) AS pending
FROM coffees c
JOIN employees maker ON maker.id = c.employee_id AND maker.active = 1 AND maker.team_id = ?
LEFT JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.reviewer_id = ?
WHERE c.employee_id != ?
    AND cr.id IS NULL
    AND c.id NOT IN (SELECT coffee_id FROM coffee_reviews WHERE approved = 0)
""",
            (team_id, employee_id, employee_id),
        ).fetchone()
    return int(row["pending"])


def get_review_queue(reviewer_id: int, team_id: int) -> pd.DataFrame:
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
    AND e.team_id = ?
    AND cr.id IS NULL
    AND c.id NOT IN (SELECT coffee_id FROM coffee_reviews WHERE approved = 0)
ORDER BY c.coffee_date ASC, c.created_at ASC
""",
            conn,
            params=(reviewer_id, reviewer_id, team_id),
        )


def get_recent_entries(team_id: int, limit: int = 100) -> pd.DataFrame:
    approved_ids = get_reviewed_coffee_ids(team_id)
    rejected_ids = get_rejected_coffee_ids(team_id)

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
JOIN employees e ON e.id = c.employee_id AND e.team_id = ?
LEFT JOIN employees reviewer ON reviewer.active = 1
    AND reviewer.team_id = ? AND reviewer.id != c.employee_id
LEFT JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.reviewer_id = reviewer.id
GROUP BY c.id, c.coffee_date, e.name, c.cups, c.note, c.created_at
ORDER BY c.coffee_date DESC, c.created_at DESC
LIMIT ?
""",
            conn,
            params=(team_id, team_id, limit),
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


def choose_next_maker(totals: pd.DataFrame) -> tuple[str, str]:
    if totals.empty:
        return "No one yet", "Add teammates first."

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
        reason = "Everyone is tied — lowest average rating breaks the tie."
    elif len(tied_on_cups) > 1:
        reason = "Tied on fewest cups — lowest average rating breaks the tie."
    else:
        reason = "Fewest approved cups on the team."

    return str(next_maker["employee"]), reason


# ---------------------------------------------------------------------------
# UI components
# ---------------------------------------------------------------------------

def render_header(team_name: str | None = None) -> None:
    kicker = escape(f"☕ {team_name}") if team_name else "Office brew ledger"
    st.markdown(
        f"""
<div class="hero-row">
<div>
<div class="hero-kicker">{kicker}</div>
<h1>Coffee Counter</h1>
<p class="hero-copy">Track coffee duty, peer ratings, and who makes the next round.</p>
</div>
<div class="status-pill">SQLite local system</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_account_bar() -> None:
    user = st.session_state["user"]
    cols = st.columns([4, 1])
    cols[0].caption(f"Signed in as **{user['name']}**")
    if cols[1].button("Sign out"):
        del st.session_state["user"]
        st.rerun()


# ---------------------------------------------------------------------------
# Login / Register
# ---------------------------------------------------------------------------

def render_login() -> None:
    render_header()
    left, right = st.columns([1, 1])

    with left:
        with st.container(border=True):
            st.subheader("Sign in")
            with st.form("login_form"):
                name = st.text_input("Name")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign in", type="primary")

            if submitted:
                user = authenticate_user(name, password)
                if user:
                    st.session_state["user"] = {
                        "id": int(user["id"]),
                        "name": user["name"],
                        "employee_id": user["employee_id"],
                        "is_admin": bool(user["is_admin"]),
                    }
                    st.rerun()
                else:
                    st.error("Name or password is incorrect.")

    with right:
        with st.container(border=True):
            st.subheader("Create account")
            st.caption("Sign up to start tracking coffees with your team.")
            with st.form("register_form"):
                new_name = st.text_input("Choose a name")
                new_password = st.text_input("Choose a password", type="password")
                reg_submitted = st.form_submit_button("Create account", type="primary")

            if reg_submitted:
                ok, msg = register_user(new_name, new_password)
                if ok:
                    st.success(msg)
                else:
                    st.warning(msg)


# ---------------------------------------------------------------------------
# Team setup (first-time flow)
# ---------------------------------------------------------------------------

def render_team_setup() -> None:
    render_header()
    render_account_bar()

    st.subheader("Get started — join or create a team")
    st.caption("You need a team before you can log coffees.")

    left, right = st.columns([1, 1])

    with left:
        with st.container(border=True):
            st.markdown("### Create a team")
            st.caption("Start a new team and invite your colleagues.")
            with st.form("create_team_form"):
                team_name = st.text_input("Team name")
                create_submitted = st.form_submit_button("Create team", type="primary")

            if create_submitted:
                ok, msg = create_team(team_name, st.session_state["user"]["employee_id"])
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.warning(msg)

    with right:
        with st.container(border=True):
            st.markdown("### Join a team")
            st.caption("Got an invite code? Enter it below.")
            with st.form("join_team_form"):
                code = st.text_input("Invite code")
                join_submitted = st.form_submit_button("Join team", type="primary")

            if join_submitted:
                ok, msg = join_team(code, st.session_state["user"]["employee_id"])
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.warning(msg)


# ---------------------------------------------------------------------------
# Main app (team member view)
# ---------------------------------------------------------------------------

def render_main_app(team: dict) -> None:
    user = st.session_state["user"]
    employee_id: int = user["employee_id"]
    team_id: int = team["id"]

    render_header(team_name=team["name"])
    render_account_bar()

    employees = get_team_employees(team_id)
    totals = get_totals(team_id)
    next_maker, next_reason = choose_next_maker(totals)

    # Next maker banner
    st.markdown(
        f"""
<div class="next-maker">
<div class="next-maker-label">Next coffee maker</div>
<div class="next-maker-name">{escape(next_maker)}</div>
<p class="next-maker-reason">{escape(next_reason)}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    # Metrics
    mcols = st.columns(3)
    mcols[0].metric("Approved cups", get_total_approved_cups(team_id))
    mcols[1].metric("Your pending reviews", get_pending_review_count_for_user(employee_id, team_id))
    mcols[2].metric("Team members", len(employees))

    # Tabs
    tab_log, tab_review, tab_totals, tab_logbook, tab_team = st.tabs(
        ["☕ Log", "📋 Review", "📊 Totals", "📒 Logbook", "👥 Team"]
    )

    # ---- Log tab ----
    with tab_log:
        st.subheader("I made coffee ☕")
        st.caption(f"Logging as **{user['name']}**")

        with st.form("log_coffee", clear_on_submit=True):
            cups = st.number_input("Cups made", min_value=1, max_value=50, value=1, step=1)
            coffee_date = st.date_input("Date", value=date.today())
            note = st.text_input("Note", placeholder="Optional")
            submitted = st.form_submit_button("Log coffee", type="primary")

        if submitted:
            add_coffee(employee_id, int(cups), coffee_date, note)
            st.success("Coffee logged! Your teammates will review it.")
            st.rerun()

        st.info(
            "**How it works:** Log your coffee → teammates approve & rate it → "
            "approved cups count towards the tally. The person with the fewest "
            "approved cups makes the next round!"
        )

    # ---- Review tab ----
    with tab_review:
        st.subheader("Review coffees")

        if len(employees) < 2:
            st.caption("At least two team members are needed for reviews.")
        else:
            queue = get_review_queue(employee_id, team_id)
            if queue.empty:
                st.success("✅ Nothing to review — you're all caught up!")
            else:
                for row in queue.itertuples(index=False):
                    cup_word = "cup" if row.cups == 1 else "cups"
                    label = f"{row.date}  •  {row.employee}  •  {row.cups} {cup_word}"
                    with st.expander(label):
                        with st.form(f"review_{row.id}"):
                            approved = st.checkbox("Approve", value=True, key=f"appr_{row.id}")
                            rating = st.slider("Rating", 1, 5, 3, key=f"rate_{row.id}")
                            if st.form_submit_button("Submit review", type="primary"):
                                add_review(row.id, employee_id, approved, rating)
                                st.success("Review saved!")
                                st.rerun()

    # ---- Totals tab ----
    with tab_totals:
        st.subheader("Team leaderboard")
        if totals.empty:
            st.caption("No data yet.")
        else:
            display = totals.rename(
                columns={
                    "employee": "Employee",
                    "approved_cups": "Approved cups",
                    "today_cups": "Today",
                    "last_7_days": "Last 7 days",
                    "average_rating": "Avg rating",
                }
            ).drop(columns=["employee_id"])
            st.dataframe(
                display,
                hide_index=True,
                use_container_width=True,
                height=280,
                column_config={
                    "Avg rating": st.column_config.NumberColumn(format="%.2f"),
                },
            )
            chart = totals.set_index("employee")["approved_cups"]
            if int(chart.sum()) > 0:
                st.bar_chart(chart)

    # ---- Logbook tab ----
    with tab_logbook:
        st.subheader("Recent coffee logs")
        entries = get_recent_entries(team_id)
        if entries.empty:
            st.caption("No coffees recorded yet.")
        else:
            display = entries.rename(
                columns={
                    "date": "Date",
                    "employee": "Employee",
                    "cups": "Cups",
                    "note": "Note",
                    "required_reviews": "Required",
                    "completed_reviews": "Done",
                    "average_rating": "Avg rating",
                    "status": "Status",
                }
            ).drop(columns=["id", "created_at"])
            st.dataframe(
                display,
                hide_index=True,
                use_container_width=True,
                height=330,
                column_config={
                    "Avg rating": st.column_config.NumberColumn(format="%.2f"),
                },
            )

    # ---- Team tab ----
    with tab_team:
        st.subheader(f"Team: {team['name']}")
        st.code(team["code"], language=None)
        st.caption("Share this invite code with colleagues so they can join.")
        st.divider()

        all_members = get_team_employees(team_id, active_only=False)
        if len(all_members) < 2:
            st.info("You're the only one here! Share the invite code above to get started.")

        for emp in all_members.itertuples(index=False):
            icon = "🟢" if emp.active else "⚪"
            st.write(f"{icon} {emp.name}")


# ---------------------------------------------------------------------------
# Admin dashboard
# ---------------------------------------------------------------------------

def render_admin_dashboard() -> None:
    render_header()
    render_account_bar()
    st.subheader("Admin Dashboard")

    tab_teams, tab_employees = st.tabs(["👥 Teams", "🧑‍💼 Employees"])

    with tab_teams:
        with closing(get_connection()) as conn:
            teams_df = pd.read_sql_query(
                """
SELECT
    t.id AS ID,
    t.name AS Team,
    t.code AS Code,
    COUNT(e.id) AS Members,
    t.created_at AS Created
FROM teams t
LEFT JOIN employees e ON e.team_id = t.id
GROUP BY t.id, t.name, t.code, t.created_at
ORDER BY t.name
""",
                conn,
            )
        if teams_df.empty:
            st.caption("No teams created yet.")
        else:
            st.dataframe(teams_df, hide_index=True, use_container_width=True)

    with tab_employees:
        with closing(get_connection()) as conn:
            all_employees = pd.read_sql_query(
                """
SELECT e.id, e.name, COALESCE(t.name, '—') AS team, e.active
FROM employees e
LEFT JOIN teams t ON t.id = e.team_id
ORDER BY e.name
""",
                conn,
            )
        if all_employees.empty:
            st.caption("No employees yet.")
        else:
            for emp in all_employees.itertuples(index=False):
                cols = st.columns([2, 1, 1])
                status = "Active" if emp.active else "Archived"
                cols[0].write(f"**{emp.name}** — {emp.team}")
                cols[1].write(status)
                button_label = "Archive" if emp.active else "Restore"
                if cols[2].button(button_label, key=f"admin_toggle_{emp.id}"):
                    set_employee_active(emp.id, not bool(emp.active))
                    st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="Coffee Counter", layout="wide")
    inject_styles()
    init_db()

    # Not logged in
    if "user" not in st.session_state:
        render_login()
        return

    user = st.session_state["user"]

    # Admin
    if user["is_admin"]:
        render_admin_dashboard()
        return

    # Regular user — check team
    team = get_user_team(user["employee_id"])
    if not team:
        render_team_setup()
        return

    render_main_app(team)


if __name__ == "__main__":
    main()
