# ☕ Coffee Counter

A Streamlit app with a local SQLite database for tracking in-house coffees per team — with ranks, badges, weekly challenges, and more.

## How it works

1. **Sign up** — create an account with a name and password.
2. **Create or join a team** — start a new team (get an invite code) or join with a colleague's code.
3. **Log coffees** — pick a coffee type, enter cups, and submit for review.
4. **Review & rate** — teammates approve, rate (1–5 ⭐), and leave optional comments.
5. **Next maker** — fewest approved cups = you're up. Ties broken by lowest avg rating.
6. **Earn ranks & badges** — climb from Intern Brewer 🫘 to Supreme Bean Lord 👑.
7. **Weekly challenges** — fun rotating goals to keep things interesting.

## Features

- ☕ **10 coffee types** (Filter, Espresso, Cappuccino, Flat White, Latte, Americano, Mocha, Pour Over, French Press, Other)
- 💬 **Review comments** for office banter
- 🎖️ **6 ranks** based on approved cups
- 🏆 **8 achievement badges** to unlock
- 🔥 **Streak tracker** (consecutive days)
- 👑 **Barista of the Week** (highest avg rating)
- 😤 **Wall of Shame** (who's behind on cups)
- 🎯 **10 weekly challenges** (rotate automatically)
- 📊 **Weekly recap** with fun stats
- ⚙️ **Team admin** (team creator) can manage members, change passwords, promote admins, disband team
- 🔐 **Global admin** dashboard to manage all teams and users

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

- **Global admin:** `admin` / `admin321` — manage all teams, users, and data.
- **Team admins:** the team creator is auto-promoted. They can manage their own team members, change passwords, and promote others.
