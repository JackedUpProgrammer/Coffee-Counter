# Coffee Counter

A small Streamlit app with a local SQLite database for tracking in-house coffees per employee.

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
