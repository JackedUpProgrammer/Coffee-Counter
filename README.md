# ☕ Coffee Counter

A Streamlit app with a local SQLite database for tracking in-house coffees per team.

## How it works

1. **Sign up** — create an account with a name and password.
2. **Create or join a team** — start a new team (you'll get an invite code) or join an existing one with a code from a colleague.
3. **Log coffees** — when you make coffee, log it. Your cups are submitted for review.
4. **Review & rate** — every other active team member must approve and rate each coffee (1–5 stars).
5. **Next maker** — the person with the fewest approved cups makes the next round. Ties are broken by lowest average rating.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
streamlit run app.py
```

The app creates `coffee_counter.sqlite3` automatically on first run.

## Admin

- **Username:** `admin`
- **Password:** `admin321`

The admin dashboard lets you view all teams and manage employees (archive/restore).
