# Coffee Counter

A small Streamlit app with a local SQLite database for tracking in-house coffees per employee.

Coffee logs are not counted immediately. Every other active employee must approve and rate the coffee first. The next coffee maker is the active employee with the fewest approved cups; if everyone is tied, the lowest average rating breaks the tie.

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
