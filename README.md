# 💰 Moneylytics Bot

> **Try it live: [@moneylytics_bot](https://t.me/moneylytics_bot)**

A personal expense tracker for Telegram: log spending from a chat message, browse and analyse it in a built-in Mini App, and import card transactions automatically from Monobank.

## Why I built this

I've always struggled with financial literacy, and existing finance apps never felt convenient to me. Since I spend a lot of time in Telegram, I decided to build a bot that lets me track expenses without leaving the app — just send a message like `500 food pizza` and it's saved. It started as a simple bot and grew into a full Telegram Mini App with bank integration. This project also gave me a chance to explore NLP and ML classification on a real-world problem.

## Features

- **Quick logging** — natural format in chat: `amount category description` (e.g. `500 food pizza`)
- **Telegram Mini App** — a React web app inside Telegram: dashboard, history, analytics, add/edit expenses
- **Monobank auto-import** — connect a Monobank personal token and card spending is imported in real time via webhook; transfers between your own accounts/jars are filtered out, and transfers to other people are categorised separately
- **Analytics** — category donut and 7-day spending chart in the Mini App; category charts in chat (Matplotlib)
- **Budgets** — daily/weekly limits per currency with overspend notifications
- **Multi-currency** — EUR, USD, UAH, GBP, tracked independently (no implicit conversion)
- **Categories** — food, transport, shopping, health, entertainment, beauty, housing, utilities, education, travel, gifts, transfer, other
- **Automatic categorisation** — a rule-based keyword classifier suggests a category from the description
- **Back-dating** — log an expense for a past date
- **Multilingual** — English, Russian, Ukrainian
- **CSV export** of all expenses

## Architecture

Two processes (see `Procfile`):

- **`worker` → `main.py`** — the Telegram bot (aiogram 3): chat commands, expense parsing, reports, budgets, notifications.
- **`web` → `webapp.py`** — a FastAPI app serving the Mini App REST API, the Monobank webhook, and the built React frontend as static files. Mini App requests are JWT-authenticated; Monobank personal tokens are encrypted at rest (Fernet).

Both processes share one database via SQLAlchemy — SQLite locally, PostgreSQL on Heroku.

## Tech Stack

**Backend / bot**
- Python 3.13
- aiogram 3.24 — Telegram Bot API
- FastAPI + Uvicorn — Mini App API & Monobank webhook
- SQLAlchemy 2.0 — ORM (SQLite local / PostgreSQL on Heroku)
- PyJWT, cryptography (Fernet) — Mini App auth & Monobank token encryption
- pandas, Matplotlib / Seaborn — in-chat charts
- scikit-learn, NumPy — category-classification experiments

**Frontend (Telegram Mini App)**
- React 18 + Vite 5
- Recharts — charts
- lucide-react — icons

**Deployment**
- Heroku (web + worker dynos, Postgres add-on)

## Project Structure

```
moneylytics-bot/
├── main.py                 # aiogram bot entrypoint (worker process)
├── webapp.py               # FastAPI: Mini App API, Monobank webhook, static frontend
├── databases/
│   ├── db.py               # Engine/session + schema migrations (SQLite/Postgres)
│   └── models.py           # SQLAlchemy models (User, Expense, FeedbackReport)
├── handlers/
│   ├── start.py            # /start + registration
│   ├── onboarding.py       # New-user onboarding
│   ├── expenses.py         # Expense parsing + rule-based category classifier
│   ├── reports.py          # Daily/weekly/category reports
│   ├── budget.py           # Budget limits & notifications
│   ├── callbacks.py        # Inline buttons, edit/delete, export
│   ├── feedback.py         # User feedback
│   └── admin.py            # Admin utilities
├── utils/                  # i18n, keyboards, currency, analytics, chart generation
├── frontend/               # React + Vite Mini App (built to frontend/dist)
├── moneylytics_baseline_experiment.ipynb
└── expenses_ml_dataset.csv
```

## ML Experiment — Expense Category Classification

One of the interesting parts of this project was trying to automatically classify expense descriptions into categories.

Full experiment: [`moneylytics_baseline_experiment.ipynb`](moneylytics_baseline_experiment.ipynb)

### Problem

Given a transaction description like `"coffee shop"` or `"uber ride"`, predict the category: `food`, `transport`, `housing`, `entertainment`, or `other`.

### What I tried

| Approach | Accuracy |
|---|---|
| Rule-Based v1 (small keyword dict) | 0.54 |
| Rule-Based v2 (expanded keyword dict) | **0.89** |
| TF-IDF + Logistic Regression | 0.47 ± 0.06 |
| CountVectorizer + Logistic Regression | 0.48 ± 0.04 |
| TF-IDF + Naive Bayes (various) | 0.34 – 0.38 |
| Hybrid (Rule-Based v2 + ML fallback) | 0.76 |

### Key finding

Rule-Based v2 outperformed every ML model. The most frustrating part was tuning Naive Bayes parameters — a lot of effort for the worst results. This taught me something important: **on small, structured datasets, simple keyword rules can beat complex ML models**. The bottleneck wasn't the algorithm — it was data. 116 samples is too few for statistical text classification to work reliably.

The hybrid approach (Rule-Based as primary, ML as fallback for unknown descriptions) actually performed *worse* than Rule-Based alone — because the ML fallback had only 7 examples to work with in the test set and achieved 0.29 accuracy on them.

The Rule-Based v2 classifier is what ships in the bot (`handlers/expenses.py`).

### Next steps

- Collect real transaction descriptions from bot users
- Use user corrections as labeled training data
- Retrain ML fallback on 500+ samples per class and compare again

## Installation

### Bot + API

```bash
git clone https://github.com/Astronom2617/moneylytics-telegram-bot.git
cd moneylytics-telegram-bot
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # add your BOT_TOKEN

python main.py                     # Telegram bot (worker)
uvicorn webapp:app --reload        # Mini App API (web) — optional locally
```

### Frontend (Mini App)

```bash
cd frontend
npm install
npm run dev        # local dev server
npm run build      # production build → frontend/dist (served by webapp.py)
```

### Environment

| Variable | Required | Notes |
|---|---|---|
| `BOT_TOKEN` | yes | Telegram bot token |
| `DATABASE_URL` | no | Defaults to local SQLite; set to a Postgres URL in production |
| `JWT_SECRET` | no | Mini App auth; defaults to a value derived from `BOT_TOKEN` |
| `MONO_ENCRYPTION_KEY` | for Monobank | Fernet key used to encrypt stored Monobank tokens |

## Usage

### Chat commands

| Command | Description |
|---|---|
| `/start` | Register and get started |
| `/today` | Daily expense report |
| `/week` | Weekly expense report |
| `/categories` | Spending breakdown with charts |
| `/budget` | Manage budget limits |
| `/settings` | Language and currency settings |
| `/help` | Usage guide |

### Adding expenses

```
500 food pizza
90 housing rent
5 transport
```

Amount and category are required; description is optional. If you omit or mistype the category, one is suggested automatically from the description.

### Monobank auto-import

Connect your Monobank personal token in the Mini App settings. Card spending is then imported automatically via webhook. Transfers between your own accounts and jars are skipped; transfers to other people are saved under the **transfer** category with the recipient kept in a dedicated field.

## License

MIT
