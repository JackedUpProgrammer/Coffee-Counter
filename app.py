## 📄 `app.py`

from __future__ import annotations

import hashlib
import hmac
import random
import sqlite3
import string
from contextlib import closing
from datetime import date, timedelta
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "coffee_counter.sqlite3"
PASSWORD_SALT = b"coffee-counter-admin-v1"
PASSWORD_ITERATIONS = 260000
ADMIN_NAME = "admin"
ADMIN_PASSWORD_HASH = (
    "44a09039f5a01f0c0fbff626c196ef6cd4a58625ceb6b0a7fac4599975b1d691"
)

COFFEE_TYPES = [
    "Filter", "Espresso", "Cappuccino", "Flat White", "Latte",
    "Americano", "Mocha", "Pour Over", "French Press", "Other",
]

RANKS = [
    (0,   "Intern Brewer",    "🫘"),
    (11,  "Caffeine Cadet",   "☕"),
    (26,  "Espresso Engineer", "⚙️"),
    (51,  "Latte Legend",      "🏅"),
    (101, "Coffee Commander",  "🏆"),
    (201, "Supreme Bean Lord", "👑"),
]

BADGE_DEFS = [
    {"key": "first_brew",   "icon": "☕",  "name": "First Brew",     "desc": "Logged your first coffee"},
    {"key": "ten_club",     "icon": "🔟", "name": "10 Cup Club",    "desc": "10 approved cups"},
    {"key": "fifty_club",   "icon": "⭐",  "name": "Half Century",   "desc": "50 approved cups"},
    {"key": "century",      "icon": "💯",  "name": "Century Brewer", "desc": "100 approved cups"},
    {"key": "perfect_brew", "icon": "🌟",  "name": "Perfect Brew",   "desc": "Got a perfect 5-star rating"},
    {"key": "streak_7",     "icon": "🔥",  "name": "Week Warrior",   "desc": "7-day coffee streak"},
    {"key": "review_25",    "icon": "📝",  "name": "Review Pro",     "desc": "Completed 25 reviews"},
    {"key": "variety_5",    "icon": "🎨",  "name": "Variety Brewer", "desc": "Made 5 different coffee types"},
]

CHALLENGES = [
    {"title": "The Experimenter",  "desc": "Make a coffee type you've never tried before."},
    {"title": "Latte Art Star",    "desc": "Attempt latte art — bonus if anyone recognises it!"},
    {"title": "Team Round",        "desc": "Make coffee for every teammate in one go."},
    {"title": "The Perfectionist", "desc": "Aim for a perfect 5-star rating this week."},
    {"title": "Speed Brew",        "desc": "Be the first to log coffee 3 mornings this week."},
    {"title": "Flavour Twist",     "desc": "Add something new — cinnamon, vanilla, oat milk!"},
    {"title": "The Mentor",        "desc": "Teach someone your best coffee technique."},
    {"title": "Double Down",       "desc": "Log at least 2 coffees every day this week."},
    {"title": "Comeback Kid",      "desc": "If you're behind on the board, catch up this week!"},
    {"title": "Review Blitz",      "desc": "Review every pending coffee the same day it's logged."},
]


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

h2, h3 { font-weight: 700; }

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

div[data-baseweb="tab-highlight"] { display: none; }

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

/* ---- New: shame banner ---- */
.shame-banner {
position: relative;
overflow: hidden;
background:
linear-gradient(135deg, rgba(255, 107, 138, 0.18), rgba(255, 200, 87, 0.08)),
var(--coffee-panel-strong);
border: 1px solid rgba(255, 107, 138, 0.34);
border-radius: 8px;
padding: 1rem 1.35rem;
margin-bottom: 1rem;
box-shadow: 0 22px 70px rgba(0, 0, 0, 0.32), 0 0 42px rgba(255, 107, 138, 0.08);
backdrop-filter: blur(16px);
}
.shame-label {
color: var(--coffee-danger);
font-size: 0.78rem;
font-weight: 750;
letter-spacing: 0.08em;
text-transform: uppercase;
margin-bottom: 0.2rem;
}
.shame-name {
color: var(--coffee-ink);
font-size: 1.4rem;
font-weight: 800;
line-height: 1.15;
}
.shame-msg {
color: var(--coffee-muted);
font-size: 0.95rem;
margin: 0;
}

/* ---- New: badges ---- */
.badge-grid {
display: flex;
flex-wrap: wrap;
gap: 0.75rem;
margin: 0.5rem 0;
}
.badge-card {
background: var(--coffee-panel);
border: 1px solid var(--coffee-line);
border-radius: 8px;
padding: 0.75rem;
text-align: center;
min-width: 100px;
flex: 0 0 auto;
}
.badge-card.earned {
border-color: var(--coffee-accent);
box-shadow: 0 0 12px rgba(56, 217, 196, 0.15);
}
.badge-card.locked { opacity: 0.35; }
.badge-icon { font-size: 1.8rem; margin-bottom: 0.3rem; }
.badge-name { color: var(--coffee-ink); font-size: 0.8rem; font-weight: 700; }
.badge-desc { color: var(--coffee-muted); font-size: 0.7rem; }

/* ---- New: rank card ---- */
.rank-card {
background:
linear-gradient(135deg, rgba(255, 200, 87, 0.12), rgba(56, 217, 196, 0.08)),
var(--coffee-panel-strong);
border: 1px solid rgba(255, 200, 87, 0.3);
border-radius: 8px;
padding: 1.25rem;
margin-bottom: 1rem;
text-align: center;
}
.rank-icon { font-size: 2.5rem; }
.rank-title { color: var(--coffee-warm); font-size: 1.2rem; font-weight: 800; margin-top: 0.3rem; }
.rank-cups { color: var(--coffee-muted); font-size: 0.85rem; }

/* ---- New: challenge card ---- */
.challenge-card {
background:
linear-gradient(135deg, rgba(255, 200, 87, 0.15), rgba(56, 217, 196, 0.05)),
var(--coffee-panel-strong);
border: 1px solid rgba(255, 200, 87, 0.3);
border-radius: 8px;
padding: 1.25rem;
margin-bottom: 1rem;
}
.challenge-label {
color: var(--coffee-warm);
font-size: 0.78rem;
font-weight: 750;
letter-spacing: 0.08em;
text-transform: uppercase;
margin-bottom: 0.2rem;
}
.challenge-title { color: var(--coffee-ink); font-size: 1.2rem; font-weight: 700; margin-bottom: 0.25rem; }
.challenge-desc { color: var(--coffee-muted); font-size: 0.95rem; margin: 0; }

/* ---- New: recap grid ---- */
.recap-grid {
display: grid;
grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
gap: 0.75rem;
margin: 0.5rem 0;
}
.recap-item {
background: var(--coffee-panel);
border: 1px solid var(--coffee-line);
border-radius: 8px;
padding: 0.85rem;
text-align: center;
}
.recap-value { color: var(--coffee-ink); font-size: 1.4rem; font-weight: 800; }
.recap-label {
color: var(--coffee-muted);
font-size: 0.75rem;
text-transform: uppercase;
letter-spacing: 0.04em;
font-weight: 650;
}

/* ---- New: barista of week ---- */
.barista-week {
background:
linear-gradient(135deg, rgba(255, 200, 87, 0.2), rgba(56, 217, 196, 0.1)),
var(--coffee-panel-strong);
border: 1px solid rgba(255, 200, 87, 0.4);
border-radius: 8px;
padding: 1rem 1.35rem;
margin-bottom: 1rem;
text-align: center;
}
.barista-week-label {
color: var(--coffee-warm);
font-size: 0.78rem;
font-weight: 750;
letter-spacing: 0.08em;
text-transform: uppercase;
}
.barista-week-name { color: var(--coffee-ink); font-size: 1.5rem; font-weight: 800; }
.barista-week-rating { color: var(--coffee-muted); font-size: 0.95rem; }

@media (max-width: 760px) {
.block-container { padding-top: 1rem; }
div[data-testid="stMetric"] { padding: 0.75rem 0.85rem; }
.hero-row { display: block; }
.status-pill { display: inline-block; margin-top: 0.8rem; }
h1 { font-size: 2rem; }
button[data-baseweb="tab"] { min-width: auto; padding-left: 0.7rem; padding-right: 0.7rem; }
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
    created_by INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1,
    team_id INTEGER,
    is_team_admin INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

CREATE TABLE IF NOT EXISTS coffees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    cups INTEGER NOT NULL CHECK (cups > 0),
    coffee_type TEXT NOT NULL DEFAULT 'Filter',
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
    comment TEXT,
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

CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    badge TEXT NOT NULL,
    earned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (employee_id, badge),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
"""
        )

        # Migrations for older schemas
        def _has(table: str, col: str) -> bool:
            return col in [
                r["name"]
                for r in conn.execute(f"PRAGMA table_info({table})").fetchall()
            ]

        if not _has("employees", "team_id"):
            conn.execute("ALTER TABLE employees ADD COLUMN team_id INTEGER REFERENCES teams(id)")
        if not _has("employees", "is_team_admin"):
            conn.execute("ALTER TABLE employees ADD COLUMN is_team_admin INTEGER NOT NULL DEFAULT 0")
        if not _has("coffees", "coffee_type"):
            conn.execute("ALTER TABLE coffees ADD COLUMN coffee_type TEXT NOT NULL DEFAULT 'Filter'")
        if not _has("coffee_reviews", "comment"):
            conn.execute("ALTER TABLE coffee_reviews ADD COLUMN comment TEXT")
        if not _has("teams", "created_by"):
            conn.execute("ALTER TABLE teams ADD COLUMN created_by INTEGER")

        # Admin user — don't overwrite password if already exists
        admin = conn.execute(
            "SELECT 1 FROM users WHERE name = ?", (ADMIN_NAME,)
        ).fetchone()
        if admin:
            conn.execute("UPDATE users SET is_admin = 1 WHERE name = ?", (ADMIN_NAME,))
        else:
            conn.execute(
                "INSERT INTO users (name, password_hash, is_admin) VALUES (?, ?, 1)",
                (ADMIN_NAME, ADMIN_PASSWORD_HASH),
            )
        conn.execute("UPDATE users SET is_admin = 0 WHERE name != ?", (ADMIN_NAME,))
        conn.commit()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def authenticate_user(name: str, password: str) -> sqlite3.Row | None:
    cleaned = " ".join(name.strip().split())
    if not cleaned or not password:
        return None
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT id, name, password_hash, employee_id, is_admin FROM users WHERE name = ?",
            (cleaned,),
        ).fetchone()
    if row and hmac.compare_digest(row["password_hash"], hash_password(password)):
        return row
    return None


def register_user(name: str, password: str) -> tuple[bool, str]:
    cleaned = " ".join(name.strip().split())
    if not cleaned:
        return False, "Enter your name."
    if cleaned.lower() == ADMIN_NAME.lower():
        return False, "That name is reserved."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    try:
        with closing(get_connection()) as conn:
            cur = conn.execute("INSERT INTO employees (name) VALUES (?)", (cleaned,))
            eid = cur.lastrowid
            conn.execute(
                "INSERT INTO users (name, password_hash, employee_id) VALUES (?, ?, ?)",
                (cleaned, hash_password(password), eid),
            )
            conn.commit()
        return True, f"Account created! Sign in as **{cleaned}**."
    except sqlite3.IntegrityError:
        return False, f"{cleaned} already exists."


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------

def generate_team_code() -> str:
    with closing(get_connection()) as conn:
        for _ in range(100):
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not conn.execute("SELECT 1 FROM teams WHERE code = ?", (code,)).fetchone():
                return code
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def create_team(name: str, employee_id: int) -> tuple[bool, str]:
    cleaned = " ".join(name.strip().split())
    if not cleaned:
        return False, "Enter a team name."
    code = generate_team_code()
    try:
        with closing(get_connection()) as conn:
            conn.execute(
                "INSERT INTO teams (name, code, created_by) VALUES (?, ?, ?)",
                (cleaned, code, employee_id),
            )
            tid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "UPDATE employees SET team_id = ?, is_team_admin = 1 WHERE id = ?",
                (tid, employee_id),
            )
            conn.commit()
        return True, f"Team **{cleaned}** created! Invite code: **{code}**"
    except sqlite3.IntegrityError:
        return False, "Could not create team. Try again."


def join_team(code: str, employee_id: int) -> tuple[bool, str]:
    cleaned = code.strip().upper()
    if not cleaned:
        return False, "Enter an invite code."
    with closing(get_connection()) as conn:
        team = conn.execute(
            "SELECT id, name FROM teams WHERE code = ?", (cleaned,)
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
            "SELECT t.id, t.name, t.code FROM teams t JOIN employees e ON e.team_id = t.id WHERE e.id = ?",
            (employee_id,),
        ).fetchone()
    return {"id": row["id"], "name": row["name"], "code": row["code"]} if row else None


def is_user_team_admin(employee_id: int) -> bool:
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT is_team_admin FROM employees WHERE id = ?", (employee_id,)
        ).fetchone()
    return bool(row["is_team_admin"]) if row else False


# ---------------------------------------------------------------------------
# Employee helpers
# ---------------------------------------------------------------------------

def get_team_employees(team_id: int, active_only: bool = True) -> pd.DataFrame:
    q = "SELECT id, name, active, is_team_admin FROM employees WHERE team_id = ?"
    p: list = [team_id]
    if active_only:
        q += " AND active = 1"
    q += " ORDER BY name"
    with closing(get_connection()) as conn:
        return pd.read_sql_query(q, conn, params=p)


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

def add_coffee(employee_id: int, cups: int, coffee_type: str, coffee_date: date, note: str) -> None:
    with closing(get_connection()) as conn:
        conn.execute(
            "INSERT INTO coffees (employee_id, cups, coffee_type, coffee_date, note) VALUES (?, ?, ?, ?, ?)",
            (employee_id, cups, coffee_type, coffee_date.isoformat(), note.strip() or None),
        )
        conn.commit()


def add_review(coffee_id: int, reviewer_id: int, approved: bool, rating: int, comment: str = "") -> None:
    with closing(get_connection()) as conn:
        conn.execute(
            """
INSERT INTO coffee_reviews (coffee_id, reviewer_id, approved, rating, comment)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT(coffee_id, reviewer_id) DO UPDATE SET
    approved = excluded.approved, rating = excluded.rating,
    comment = excluded.comment, created_at = CURRENT_TIMESTAMP
""",
            (coffee_id, reviewer_id, 1 if approved else 0, rating, comment.strip() or None),
        )
        conn.commit()


def get_reviewed_coffee_ids(team_id: int) -> set[int]:
    with closing(get_connection()) as conn:
        rows = conn.execute(
            """
SELECT c.id
FROM coffees c
JOIN employees maker ON maker.id = c.employee_id AND maker.team_id = ?
LEFT JOIN employees reviewer ON reviewer.active = 1 AND reviewer.team_id = ? AND reviewer.id != c.employee_id
LEFT JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.reviewer_id = reviewer.id
GROUP BY c.id
HAVING COUNT(reviewer.id) > 0 AND COUNT(reviewer.id) = COUNT(cr.id) AND MIN(cr.approved) = 1
""",
            (team_id, team_id),
        ).fetchall()
    return {int(r["id"]) for r in rows}


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
    return {int(r["coffee_id"]) for r in rows}


def get_totals(team_id: int) -> pd.DataFrame:
    approved = get_reviewed_coffee_ids(team_id)
    if not approved:
        with closing(get_connection()) as conn:
            df = pd.read_sql_query(
                "SELECT id AS employee_id, name AS employee FROM employees WHERE team_id = ? AND active = 1 ORDER BY name",
                conn, params=(team_id,),
            )
        for c in ("approved_cups", "today_cups", "last_7_days"):
            df[c] = 0
        df["average_rating"] = None
        return df

    ph = ",".join("?" for _ in approved)
    p = tuple(approved) + tuple(approved) + (team_id,)
    with closing(get_connection()) as conn:
        return pd.read_sql_query(
            f"""
SELECT e.id AS employee_id, e.name AS employee,
    COALESCE(cs.ac, 0) AS approved_cups,
    COALESCE(cs.tc, 0) AS today_cups,
    COALESCE(cs.wc, 0) AS last_7_days,
    rs.average_rating
FROM employees e
LEFT JOIN (
    SELECT employee_id,
        SUM(cups) AS ac,
        SUM(CASE WHEN coffee_date = DATE('now','localtime') THEN cups ELSE 0 END) AS tc,
        SUM(CASE WHEN coffee_date >= DATE('now','localtime','-6 days') THEN cups ELSE 0 END) AS wc
    FROM coffees WHERE id IN ({ph}) GROUP BY employee_id
) cs ON cs.employee_id = e.id
LEFT JOIN (
    SELECT c.employee_id, ROUND(AVG(cr.rating), 2) AS average_rating
    FROM coffees c JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.approved = 1
    WHERE c.id IN ({ph}) GROUP BY c.employee_id
) rs ON rs.employee_id = e.id
WHERE e.active = 1 AND e.team_id = ?
ORDER BY approved_cups DESC, e.name
""",
            conn, params=p,
        )


def get_total_approved_cups(team_id: int) -> int:
    ids = get_reviewed_coffee_ids(team_id)
    if not ids:
        return 0
    ph = ",".join("?" for _ in ids)
    with closing(get_connection()) as conn:
        r = conn.execute(
            f"SELECT COALESCE(SUM(cups),0) AS t FROM coffees WHERE id IN ({ph})",
            tuple(ids),
        ).fetchone()
    return int(r["t"])


def get_pending_review_count_for_user(employee_id: int, team_id: int) -> int:
    with closing(get_connection()) as conn:
        r = conn.execute(
            """
SELECT COUNT(*) AS p FROM coffees c
JOIN employees m ON m.id = c.employee_id AND m.active = 1 AND m.team_id = ?
LEFT JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.reviewer_id = ?
WHERE c.employee_id != ? AND cr.id IS NULL
    AND c.id NOT IN (SELECT coffee_id FROM coffee_reviews WHERE approved = 0)
""",
            (team_id, employee_id, employee_id),
        ).fetchone()
    return int(r["p"])


def get_review_queue(reviewer_id: int, team_id: int) -> pd.DataFrame:
    with closing(get_connection()) as conn:
        return pd.read_sql_query(
            """
SELECT c.id, c.coffee_date AS date, e.name AS employee, c.cups,
       c.coffee_type, COALESCE(c.note, '') AS note
FROM coffees c
JOIN employees e ON e.id = c.employee_id
LEFT JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.reviewer_id = ?
WHERE c.employee_id != ? AND e.active = 1 AND e.team_id = ?
    AND cr.id IS NULL
    AND c.id NOT IN (SELECT coffee_id FROM coffee_reviews WHERE approved = 0)
ORDER BY c.coffee_date ASC, c.created_at ASC
""",
            conn, params=(reviewer_id, reviewer_id, team_id),
        )


def get_recent_entries(team_id: int, limit: int = 100) -> pd.DataFrame:
    approved = get_reviewed_coffee_ids(team_id)
    rejected = get_rejected_coffee_ids(team_id)
    with closing(get_connection()) as conn:
        df = pd.read_sql_query(
            """
SELECT c.id, c.coffee_date AS date, e.name AS employee, c.cups,
    c.coffee_type, COALESCE(c.note, '') AS note, c.created_at,
    COUNT(rv.id) AS required_reviews, COUNT(cr.id) AS completed_reviews,
    ROUND(AVG(cr.rating), 2) AS average_rating
FROM coffees c
JOIN employees e ON e.id = c.employee_id AND e.team_id = ?
LEFT JOIN employees rv ON rv.active = 1 AND rv.team_id = ? AND rv.id != c.employee_id
LEFT JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.reviewer_id = rv.id
GROUP BY c.id ORDER BY c.coffee_date DESC, c.created_at DESC LIMIT ?
""",
            conn, params=(team_id, team_id, limit),
        )
    if df.empty:
        return df

    def _status(eid: int) -> str:
        if eid in rejected:
            return "Rejected"
        return "Approved" if eid in approved else "Pending"

    df["status"] = df["id"].apply(_status)
    return df


def get_coffee_reviews(coffee_id: int) -> pd.DataFrame:
    with closing(get_connection()) as conn:
        return pd.read_sql_query(
            """
SELECT e.name AS reviewer, cr.approved, cr.rating, COALESCE(cr.comment, '') AS comment
FROM coffee_reviews cr JOIN employees e ON e.id = cr.reviewer_id
WHERE cr.coffee_id = ? ORDER BY cr.created_at
""",
            conn, params=(coffee_id,),
        )


def choose_next_maker(totals: pd.DataFrame) -> tuple[str, str]:
    if totals.empty:
        return "No one yet", "Add teammates first."
    rk = totals.copy()
    rk["approved_cups"] = rk["approved_cups"].fillna(0).astype(int)
    rk["average_rating"] = rk["average_rating"].fillna(0.0).astype(float)
    rk = rk.sort_values(["approved_cups", "average_rating", "employee"], ascending=[True, True, True])
    nxt = rk.iloc[0]
    low = int(nxt["approved_cups"])
    tied = rk[rk["approved_cups"] == low]
    if len(tied) == len(rk):
        reason = "Everyone is tied — lowest average rating breaks the tie."
    elif len(tied) > 1:
        reason = "Tied on fewest cups — lowest average rating breaks the tie."
    else:
        reason = "Fewest approved cups on the team."
    return str(nxt["employee"]), reason


# ---------------------------------------------------------------------------
# Achievements
# ---------------------------------------------------------------------------

def get_earned_badges(employee_id: int) -> set[str]:
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT badge FROM achievements WHERE employee_id = ?", (employee_id,)
        ).fetchall()
    return {r["badge"] for r in rows}


def award_badge(employee_id: int, badge: str) -> None:
    try:
        with closing(get_connection()) as conn:
            conn.execute(
                "INSERT INTO achievements (employee_id, badge) VALUES (?, ?)",
                (employee_id, badge),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        pass


def check_achievements(employee_id: int, team_id: int) -> list[str]:
    earned = get_earned_badges(employee_id)
    new: list[str] = []

    with closing(get_connection()) as conn:
        if "first_brew" not in earned:
            c = conn.execute("SELECT COUNT(*) AS c FROM coffees WHERE employee_id = ?", (employee_id,)).fetchone()["c"]
            if c > 0:
                award_badge(employee_id, "first_brew"); new.append("first_brew")

        approved = get_reviewed_coffee_ids(team_id)
        cups = 0
        if approved:
            ph = ",".join("?" for _ in approved)
            cups = conn.execute(
                f"SELECT COALESCE(SUM(cups),0) AS c FROM coffees WHERE employee_id = ? AND id IN ({ph})",
                (employee_id,) + tuple(approved),
            ).fetchone()["c"]
        for thr, key in [(10, "ten_club"), (50, "fifty_club"), (100, "century")]:
            if key not in earned and cups >= thr:
                award_badge(employee_id, key); new.append(key)

        if "perfect_brew" not in earned:
            pf = conn.execute("""
                SELECT 1 FROM coffees c JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.approved = 1
                WHERE c.employee_id = ? GROUP BY c.id HAVING ROUND(AVG(cr.rating),2) >= 5.0 LIMIT 1
            """, (employee_id,)).fetchone()
            if pf:
                award_badge(employee_id, "perfect_brew"); new.append("perfect_brew")

        if "streak_7" not in earned and compute_streak(employee_id) >= 7:
            award_badge(employee_id, "streak_7"); new.append("streak_7")

        if "review_25" not in earned:
            rc = conn.execute("SELECT COUNT(*) AS c FROM coffee_reviews WHERE reviewer_id = ?", (employee_id,)).fetchone()["c"]
            if rc >= 25:
                award_badge(employee_id, "review_25"); new.append("review_25")

        if "variety_5" not in earned:
            vc = conn.execute(
                "SELECT COUNT(DISTINCT coffee_type) AS c FROM coffees WHERE employee_id = ? AND coffee_type IS NOT NULL",
                (employee_id,),
            ).fetchone()["c"]
            if vc >= 5:
                award_badge(employee_id, "variety_5"); new.append("variety_5")

    return new


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def compute_streak(employee_id: int) -> int:
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT DISTINCT coffee_date FROM coffees WHERE employee_id = ? ORDER BY coffee_date DESC",
            (employee_id,),
        ).fetchall()
    if not rows:
        return 0
    dates = [date.fromisoformat(r["coffee_date"]) for r in rows]
    today = date.today()
    if dates[0] != today and dates[0] != today - timedelta(days=1):
        return 0
    streak = 1
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            streak += 1
        else:
            break
    return streak


def get_rank(cups: int) -> tuple[str, str, int | None]:
    icon, title, nxt = RANKS[0][2], RANKS[0][1], RANKS[1][0] if len(RANKS) > 1 else None
    for i, (thr, t, ic) in enumerate(RANKS):
        if cups >= thr:
            icon, title = ic, t
            nxt = RANKS[i + 1][0] if i + 1 < len(RANKS) else None
    return icon, title, nxt


def get_barista_of_week(team_id: int) -> tuple[str, float] | None:
    today = date.today()
    mon = today - timedelta(days=today.weekday())
    sun = mon + timedelta(days=6)
    approved = get_reviewed_coffee_ids(team_id)
    if not approved:
        return None
    ph = ",".join("?" for _ in approved)
    with closing(get_connection()) as conn:
        r = conn.execute(
            f"""
SELECT e.name, ROUND(AVG(cr.rating),2) AS ar
FROM coffees c
JOIN employees e ON e.id = c.employee_id AND e.team_id = ?
JOIN coffee_reviews cr ON cr.coffee_id = c.id AND cr.approved = 1
WHERE c.id IN ({ph}) AND c.coffee_date BETWEEN ? AND ?
GROUP BY e.id HAVING COUNT(cr.id) > 0 ORDER BY ar DESC LIMIT 1
""",
            (team_id,) + tuple(approved) + (mon.isoformat(), sun.isoformat()),
        ).fetchone()
    return (r["name"], float(r["ar"])) if r else None


def get_weekly_recap(team_id: int) -> dict:
    today = date.today()
    mon = today - timedelta(days=today.weekday())
    sun = mon + timedelta(days=6)
    with closing(get_connection()) as conn:
        total = conn.execute(
            "SELECT COALESCE(SUM(c.cups),0) AS t FROM coffees c JOIN employees e ON e.id=c.employee_id AND e.team_id=? WHERE c.coffee_date BETWEEN ? AND ?",
            (team_id, mon.isoformat(), sun.isoformat()),
        ).fetchone()["t"]
        pop = conn.execute(
            "SELECT c.coffee_type, COUNT(*) AS n FROM coffees c JOIN employees e ON e.id=c.employee_id AND e.team_id=? WHERE c.coffee_date BETWEEN ? AND ? GROUP BY c.coffee_type ORDER BY n DESC LIMIT 1",
            (team_id, mon.isoformat(), sun.isoformat()),
        ).fetchone()
        top = conn.execute(
            "SELECT e.name, SUM(c.cups) AS t FROM coffees c JOIN employees e ON e.id=c.employee_id AND e.team_id=? WHERE c.coffee_date BETWEEN ? AND ? GROUP BY e.id ORDER BY t DESC LIMIT 1",
            (team_id, mon.isoformat(), sun.isoformat()),
        ).fetchone()
        revs = conn.execute(
            "SELECT COUNT(*) AS c FROM coffee_reviews cr JOIN coffees co ON co.id=cr.coffee_id JOIN employees e ON e.id=co.employee_id AND e.team_id=? WHERE cr.created_at >= ?",
            (team_id, mon.isoformat()),
        ).fetchone()["c"]
    return {
        "total_cups": int(total),
        "popular_type": pop["coffee_type"] if pop else "—",
        "top_brewer": top["name"] if top else "—",
        "top_cups": int(top["t"]) if top else 0,
        "reviews": int(revs),
    }


def get_coffee_type_stats(team_id: int) -> pd.DataFrame:
    with closing(get_connection()) as conn:
        return pd.read_sql_query(
            "SELECT c.coffee_type AS type, COUNT(*) AS count FROM coffees c JOIN employees e ON e.id=c.employee_id AND e.team_id=? GROUP BY c.coffee_type ORDER BY count DESC",
            conn, params=(team_id,),
        )


def get_shame_info(totals: pd.DataFrame) -> tuple[str, str] | None:
    if totals.empty or len(totals) < 2:
        return None
    cups = totals["approved_cups"].fillna(0).astype(int)
    avg = cups.mean()
    mn = cups.min()
    if avg - mn < 3:
        return None
    row = totals[cups == mn].iloc[0]
    diff = int(round(avg - mn))
    return str(row["employee"]), f"Owes the office about {diff} coffees! Time to brew! ☕😤"


# ---------------------------------------------------------------------------
# Admin operations
# ---------------------------------------------------------------------------

def delete_employee_data(employee_id: int) -> None:
    with closing(get_connection()) as conn:
        conn.execute("DELETE FROM achievements WHERE employee_id = ?", (employee_id,))
        conn.execute("DELETE FROM coffee_reviews WHERE reviewer_id = ?", (employee_id,))
        conn.execute("DELETE FROM coffee_reviews WHERE coffee_id IN (SELECT id FROM coffees WHERE employee_id = ?)", (employee_id,))
        conn.execute("DELETE FROM coffees WHERE employee_id = ?", (employee_id,))
        conn.execute("DELETE FROM users WHERE employee_id = ?", (employee_id,))
        conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        conn.commit()


def delete_team_data(team_id: int) -> None:
    with closing(get_connection()) as conn:
        for emp in conn.execute("SELECT id FROM employees WHERE team_id = ?", (team_id,)).fetchall():
            eid = emp["id"]
            conn.execute("DELETE FROM achievements WHERE employee_id = ?", (eid,))
            conn.execute("DELETE FROM coffee_reviews WHERE reviewer_id = ?", (eid,))
            conn.execute("DELETE FROM coffee_reviews WHERE coffee_id IN (SELECT id FROM coffees WHERE employee_id = ?)", (eid,))
            conn.execute("DELETE FROM coffees WHERE employee_id = ?", (eid,))
            conn.execute("DELETE FROM users WHERE employee_id = ?", (eid,))
            conn.execute("DELETE FROM employees WHERE id = ?", (eid,))
        conn.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        conn.commit()


def disband_team(team_id: int) -> None:
    """Remove team + coffee data but keep user accounts."""
    with closing(get_connection()) as conn:
        for emp in conn.execute("SELECT id FROM employees WHERE team_id = ?", (team_id,)).fetchall():
            eid = emp["id"]
            conn.execute("DELETE FROM achievements WHERE employee_id = ?", (eid,))
            conn.execute("DELETE FROM coffee_reviews WHERE reviewer_id = ?", (eid,))
            conn.execute("DELETE FROM coffee_reviews WHERE coffee_id IN (SELECT id FROM coffees WHERE employee_id = ?)", (eid,))
            conn.execute("DELETE FROM coffees WHERE employee_id = ?", (eid,))
        conn.execute("UPDATE employees SET team_id = NULL, is_team_admin = 0 WHERE team_id = ?", (team_id,))
        conn.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        conn.commit()


def change_username(employee_id: int, new_name: str) -> tuple[bool, str]:
    cleaned = " ".join(new_name.strip().split())
    if not cleaned:
        return False, "Enter a name."
    if cleaned.lower() == ADMIN_NAME.lower():
        return False, "That name is reserved."
    try:
        with closing(get_connection()) as conn:
            conn.execute("UPDATE employees SET name = ? WHERE id = ?", (cleaned, employee_id))
            conn.execute("UPDATE users SET name = ? WHERE employee_id = ?", (cleaned, employee_id))
            conn.commit()
        return True, f"Name changed to **{cleaned}**."
    except sqlite3.IntegrityError:
        return False, "That name is already taken."


def change_user_password(employee_id: int, new_pw: str) -> tuple[bool, str]:
    if len(new_pw) < 6:
        return False, "Password must be at least 6 characters."
    with closing(get_connection()) as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE employee_id = ?", (hash_password(new_pw), employee_id))
        conn.commit()
    return True, "Password changed."


def change_admin_password(new_pw: str) -> tuple[bool, str]:
    if len(new_pw) < 6:
        return False, "Password must be at least 6 characters."
    with closing(get_connection()) as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE name = ?", (hash_password(new_pw), ADMIN_NAME))
        conn.commit()
    return True, "Admin password changed."


def clear_all_data() -> None:
    with closing(get_connection()) as conn:
        conn.execute("DELETE FROM achievements")
        conn.execute("DELETE FROM coffee_reviews")
        conn.execute("DELETE FROM coffees")
        conn.execute("DELETE FROM users WHERE is_admin = 0")
        conn.execute("DELETE FROM employees")
        conn.execute("DELETE FROM teams")
        conn.commit()


def promote_team_admin(employee_id: int, promote: bool) -> None:
    with closing(get_connection()) as conn:
        conn.execute("UPDATE employees SET is_team_admin = ? WHERE id = ?", (1 if promote else 0, employee_id))
        conn.commit()


def remove_from_team(employee_id: int) -> None:
    with closing(get_connection()) as conn:
        conn.execute("UPDATE employees SET team_id = NULL, is_team_admin = 0 WHERE id = ?", (employee_id,))
        conn.commit()


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
<p class="hero-copy">Track coffee duty, peer ratings, ranks, and who makes the next round.</p>
</div>
<div class="status-pill">SQLite local system</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_account_bar() -> None:
    user = st.session_state["user"]
    cols = st.columns([4, 1, 1])
    cols[0].caption(f"Signed in as **{user['name']}**")
    if cols[1].button("🔄 Refresh"):
        st.rerun()
    if cols[2].button("Sign out"):
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
                pw = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign in", type="primary")
            if submitted:
                user = authenticate_user(name, pw)
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
                nn = st.text_input("Choose a name")
                np = st.text_input("Choose a password", type="password")
                reg = st.form_submit_button("Create account", type="primary")
            if reg:
                ok, msg = register_user(nn, np)
                (st.success if ok else st.warning)(msg)


# ---------------------------------------------------------------------------
# Team setup
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
            with st.form("create_team"):
                tn = st.text_input("Team name")
                cs = st.form_submit_button("Create team", type="primary")
            if cs:
                ok, msg = create_team(tn, st.session_state["user"]["employee_id"])
                if ok:
                    st.success(msg); st.rerun()
                else:
                    st.warning(msg)
    with right:
        with st.container(border=True):
            st.markdown("### Join a team")
            st.caption("Got an invite code? Enter it below.")
            with st.form("join_team"):
                tc = st.text_input("Invite code")
                js = st.form_submit_button("Join team", type="primary")
            if js:
                ok, msg = join_team(tc, st.session_state["user"]["employee_id"])
                if ok:
                    st.success(msg); st.rerun()
                else:
                    st.warning(msg)


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def render_main_app(team: dict) -> None:
    user = st.session_state["user"]
    eid: int = user["employee_id"]
    tid: int = team["id"]
    ta = is_user_team_admin(eid)

    render_header(team_name=team["name"])
    render_account_bar()

    # Check achievements
    new_badges = check_achievements(eid, tid)
    if new_badges:
        for bk in new_badges:
            bd = next((b for b in BADGE_DEFS if b["key"] == bk), None)
            if bd:
                st.toast(f"{bd['icon']} Badge earned: **{bd['name']}**!")
        st.balloons()

    employees = get_team_employees(tid)
    totals = get_totals(tid)
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

    # Wall of shame
    shame = get_shame_info(totals)
    if shame:
        st.markdown(
            f"""
<div class="shame-banner">
<div class="shame-label">😤 Wall of shame</div>
<div class="shame-name">{escape(shame[0])}</div>
<p class="shame-msg">{escape(shame[1])}</p>
</div>
""",
            unsafe_allow_html=True,
        )

    # Metrics
    mc = st.columns(3)
    mc[0].metric("Approved cups", get_total_approved_cups(tid))
    mc[1].metric("Your pending reviews", get_pending_review_count_for_user(eid, tid))
    mc[2].metric("🔥 Streak", f"{compute_streak(eid)} days")

    # Tabs
    tab_names = ["☕ Log", "📋 Review", "🏆 Board", "🎯 Fun", "📒 History", "👥 Team"]
    if ta:
        tab_names.append("⚙️ Manage")
    tabs = st.tabs(tab_names)

    # ---- ☕ Log ----
    with tabs[0]:
        st.subheader("I made coffee ☕")
        st.caption(f"Logging as **{user['name']}**")
        with st.form("log_coffee", clear_on_submit=True):
            ctype = st.selectbox("Coffee type", COFFEE_TYPES)
            cups = st.number_input("Cups made", min_value=1, max_value=50, value=1, step=1)
            cdate = st.date_input("Date", value=date.today())
            note = st.text_input("Note", placeholder="Optional")
            if st.form_submit_button("Log coffee", type="primary"):
                add_coffee(eid, int(cups), ctype, cdate, note)
                st.success("Coffee logged! Your teammates will review it.")
                st.rerun()
        st.info(
            "**How it works:** Log your coffee → teammates approve & rate it → "
            "approved cups count towards the tally. The person with the fewest "
            "approved cups makes the next round!"
        )

    # ---- 📋 Review ----
    with tabs[1]:
        st.subheader("Review coffees")
        if len(employees) < 2:
            st.caption("At least two team members needed for reviews.")
        else:
            queue = get_review_queue(eid, tid)
            if queue.empty:
                st.success("✅ Nothing to review — you're all caught up!")
            else:
                for row in queue.itertuples(index=False):
                    cw = "cup" if row.cups == 1 else "cups"
                    label = f"{row.date}  •  {row.employee}  •  {row.coffee_type}  •  {row.cups} {cw}"
                    with st.expander(label):
                        with st.form(f"rev_{row.id}"):
                            appr = st.checkbox("Approve", value=True, key=f"a_{row.id}")
                            rating = st.slider("Rating", 1, 5, 3, key=f"r_{row.id}")
                            comment = st.text_input("Comment", placeholder="Optional", key=f"c_{row.id}")
                            if st.form_submit_button("Submit review", type="primary"):
                                add_review(row.id, eid, appr, rating, comment)
                                st.success("Review saved!")
                                st.rerun()

    # ---- 🏆 Board ----
    with tabs[2]:
        bow = get_barista_of_week(tid)
        if bow:
            stars = "⭐" * round(bow[1])
            st.markdown(
                f"""
<div class="barista-week">
<div class="barista-week-label">👑 Barista of the week</div>
<div class="barista-week-name">{escape(bow[0])}</div>
<div class="barista-week-rating">{stars} ({bow[1]:.2f})</div>
</div>
""",
                unsafe_allow_html=True,
            )

        st.subheader("Team leaderboard")
        if totals.empty:
            st.caption("No data yet.")
        else:
            disp = totals.copy()
            disp["Rank"] = disp["approved_cups"].apply(
                lambda c: f"{get_rank(int(c))[0]} {get_rank(int(c))[1]}"
            )
            disp = disp.rename(columns={
                "employee": "Employee", "approved_cups": "Cups",
                "today_cups": "Today", "last_7_days": "7 Days",
                "average_rating": "Avg ⭐",
            }).drop(columns=["employee_id"])
            disp = disp[["Rank", "Employee", "Cups", "Today", "7 Days", "Avg ⭐"]]
            st.dataframe(disp, hide_index=True, use_container_width=True, height=280,
                         column_config={"Avg ⭐": st.column_config.NumberColumn(format="%.2f")})
            chart = totals.set_index("employee")["approved_cups"]
            if int(chart.sum()) > 0:
                st.bar_chart(chart)

    # ---- 🎯 Fun ----
    with tabs[3]:
        user_row = totals[totals["employee_id"] == eid]
        user_cups = int(user_row["approved_cups"].iloc[0]) if not user_row.empty else 0
        icon, title, nxt = get_rank(user_cups)
        progress = f"{user_cups} cups"
        if nxt:
            progress += f" — {nxt - user_cups} more to next rank"

        fl, fr = st.columns(2)
        with fl:
            st.markdown(
                f"""
<div class="rank-card">
<div class="rank-icon">{icon}</div>
<div class="rank-title">{escape(title)}</div>
<div class="rank-cups">{escape(progress)}</div>
</div>
""",
                unsafe_allow_html=True,
            )
        with fr:
            streak = compute_streak(eid)
            st.markdown(
                f"""
<div class="rank-card">
<div class="rank-icon">🔥</div>
<div class="rank-title">{streak} day{'s' if streak != 1 else ''}</div>
<div class="rank-cups">Current coffee streak</div>
</div>
""",
                unsafe_allow_html=True,
            )

        st.subheader("Your badges")
        earned = get_earned_badges(eid)
        if not earned:
            st.caption("No achievements unlocked yet — start brewing! ☕")
        else:
            badge_html = ['<div class="badge-grid">']
            for b in BADGE_DEFS:
                if b["key"] not in earned:
                    continue
                badge_html.append(
                    f'<div class="badge-card earned"><div class="badge-icon">{b["icon"]}</div>'
                    f'<div class="badge-name">{escape(b["name"])}</div>'
                    f'<div class="badge-desc">{escape(b["desc"])}</div></div>'
                )
            badge_html.append("</div>")
            st.markdown("".join(badge_html), unsafe_allow_html=True)

        wn = date.today().isocalendar()[1]
        ch = CHALLENGES[wn % len(CHALLENGES)]
        st.markdown(
            f"""
<div class="challenge-card">
<div class="challenge-label">🎯 This week's challenge</div>
<div class="challenge-title">{escape(ch['title'])}</div>
<p class="challenge-desc">{escape(ch['desc'])}</p>
</div>
""",
            unsafe_allow_html=True,
        )

        st.subheader("This week's recap")
        recap = get_weekly_recap(tid)
        st.markdown(
            f"""
<div class="recap-grid">
<div class="recap-item"><div class="recap-value">{recap['total_cups']}</div><div class="recap-label">Cups this week</div></div>
<div class="recap-item"><div class="recap-value">{escape(recap['top_brewer'])}</div><div class="recap-label">Top brewer</div></div>
<div class="recap-item"><div class="recap-value">{escape(recap['popular_type'])}</div><div class="recap-label">Favourite brew</div></div>
<div class="recap-item"><div class="recap-value">{recap['reviews']}</div><div class="recap-label">Reviews done</div></div>
</div>
""",
            unsafe_allow_html=True,
        )

        cts = get_coffee_type_stats(tid)
        if not cts.empty:
            st.subheader("Coffee type breakdown")
            st.bar_chart(cts.set_index("type")["count"])

    # ---- 📒 History ----
    with tabs[4]:
        st.subheader("Recent coffee logs")
        entries = get_recent_entries(tid)
        if entries.empty:
            st.caption("No coffees recorded yet.")
        else:
            disp = entries.rename(columns={
                "date": "Date", "employee": "Employee", "coffee_type": "Type",
                "cups": "Cups", "note": "Note",
                "required_reviews": "Required", "completed_reviews": "Done",
                "average_rating": "Avg ⭐", "status": "Status",
            }).drop(columns=["id", "created_at"])
            st.dataframe(disp, hide_index=True, use_container_width=True, height=330,
                         column_config={"Avg ⭐": st.column_config.NumberColumn(format="%.2f")})

            st.divider()
            st.caption("View reviews for a specific coffee")
            labels = {
                f"{r.date} • {r.employee} • {r.cups} cups ({r.status})": r.id
                for r in entries.itertuples(index=False)
            }
            sel = st.selectbox("Select a coffee", labels.keys(), key="hist_detail")
            if sel:
                revs = get_coffee_reviews(labels[sel])
                if revs.empty:
                    st.caption("No reviews yet.")
                else:
                    for rv in revs.itertuples(index=False):
                        ic = "✅" if rv.approved else "❌"
                        stars = "⭐" * rv.rating
                        cmt = f" — *{rv.comment}*" if rv.comment else ""
                        st.write(f"{ic} **{rv.reviewer}** rated {stars}{cmt}")

    # ---- 👥 Team ----
    with tabs[5]:
        st.subheader(f"Team: {team['name']}")
        st.code(team["code"], language=None)
        st.caption("Share this invite code with colleagues so they can join.")
        st.divider()
        all_members = get_team_employees(tid, active_only=False)
        if len(all_members) < 2:
            st.info("You're the only one here! Share the invite code above to get started.")
        for m in all_members.itertuples(index=False):
            ic = "🟢" if m.active else "⚪"
            admin_badge = " 👑" if m.is_team_admin else ""
            st.write(f"{ic} {m.name}{admin_badge}")

    # ---- ⚙️ Manage (team admin) ----
    if ta and len(tabs) > 6:
        with tabs[6]:
            st.subheader("Team management")
            members = get_team_employees(tid, active_only=False)
            for m in members.itertuples(index=False):
                if m.id == eid:
                    continue
                with st.expander(f"{'🟢' if m.active else '⚪'} {m.name}{'  👑' if m.is_team_admin else ''}"):
                    npw = st.text_input("New password", type="password", key=f"tp_{m.id}")
                    if st.button("Save password", key=f"tps_{m.id}"):
                        ok, msg = change_user_password(m.id, npw)
                        (st.success if ok else st.warning)(msg)
                    c1, c2 = st.columns(2)
                    bl = "Archive" if m.active else "Restore"
                    if c1.button(bl, key=f"tt_{m.id}"):
                        set_employee_active(m.id, not bool(m.active)); st.rerun()
                    al = "Remove admin" if m.is_team_admin else "Make admin"
                    if c2.button(al, key=f"ta_{m.id}"):
                        promote_team_admin(m.id, not bool(m.is_team_admin)); st.rerun()
                    st.divider()
                    if st.button(f"Remove {m.name} from team", key=f"tr_{m.id}"):
                        remove_from_team(m.id); st.success(f"Removed {m.name}."); st.rerun()

            st.divider()
            st.warning("⚠️ Disbanding deletes all coffee data but keeps user accounts.")
            if st.button("🗑️ Disband this team", type="primary"):
                disband_team(tid)
                st.success("Team disbanded.")
                st.rerun()


# ---------------------------------------------------------------------------
# Admin dashboard
# ---------------------------------------------------------------------------

def render_admin_dashboard() -> None:
    render_header()
    render_account_bar()
    st.subheader("Admin Dashboard")

    t_teams, t_users, t_settings = st.tabs(["👥 Teams", "🧑‍💼 Users", "⚙️ Settings"])

    with t_teams:
        with closing(get_connection()) as conn:
            teams = conn.execute(
                "SELECT t.id, t.name, t.code, COUNT(e.id) AS members, t.created_at FROM teams t LEFT JOIN employees e ON e.team_id = t.id GROUP BY t.id ORDER BY t.name"
            ).fetchall()
        if not teams:
            st.caption("No teams created yet.")
        else:
            for tm in teams:
                with st.expander(f"{tm['name']} — {tm['members']} members — Code: {tm['code']}"):
                    if st.button(f"🗑️ Delete team and ALL data", key=f"adt_{tm['id']}"):
                        delete_team_data(tm["id"])
                        st.success(f"Deleted team {tm['name']}."); st.rerun()

    with t_users:
        with closing(get_connection()) as conn:
            emps = conn.execute(
                "SELECT e.id, e.name, COALESCE(t.name, '—') AS team, e.active FROM employees e LEFT JOIN teams t ON t.id = e.team_id ORDER BY e.name"
            ).fetchall()
        if not emps:
            st.caption("No users yet.")
        else:
            for em in emps:
                with st.expander(f"{em['name']} — {em['team']} — {'Active' if em['active'] else 'Archived'}"):
                    nn = st.text_input("New name", value=em["name"], key=f"an_{em['id']}")
                    if st.button("Save name", key=f"ans_{em['id']}"):
                        ok, msg = change_username(em["id"], nn)
                        (st.success if ok else st.warning)(msg)
                    npw = st.text_input("New password", type="password", key=f"ap_{em['id']}")
                    if st.button("Save password", key=f"aps_{em['id']}"):
                        ok, msg = change_user_password(em["id"], npw)
                        (st.success if ok else st.warning)(msg)
                    bl = "Archive" if em["active"] else "Restore"
                    if st.button(bl, key=f"at_{em['id']}"):
                        set_employee_active(em["id"], not bool(em["active"])); st.rerun()
                    st.divider()
                    if st.button(f"🗑️ Delete {em['name']} and all data", key=f"ad_{em['id']}"):
                        delete_employee_data(em["id"])
                        st.success(f"Deleted {em['name']}."); st.rerun()

    with t_settings:
        st.markdown("### Change admin password")
        with st.form("admin_pw"):
            npw = st.text_input("New admin password", type="password")
            if st.form_submit_button("Change password", type="primary"):
                ok, msg = change_admin_password(npw)
                (st.success if ok else st.warning)(msg)
        st.divider()
        st.markdown("### ☢️ Nuclear option")
        st.warning("⚠️ This deletes ALL teams, employees, coffees, reviews, and achievements. Only the admin account survives.")
        if st.button("🗑️ Clear all data", type="primary"):
            clear_all_data()
            st.success("All data cleared."); st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="Coffee Counter", layout="wide")
    inject_styles()
    init_db()

    if "user" not in st.session_state:
        render_login()
        return

    user = st.session_state["user"]

    if user["is_admin"]:
        render_admin_dashboard()
        return

    if user["employee_id"] is None:
        render_admin_dashboard()
        return

    team = get_user_team(user["employee_id"])
    if not team:
        render_team_setup()
        return

    render_main_app(team)


if __name__ == "__main__":
    main()
