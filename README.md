# 💰 Moneylytics Bot

A Telegram bot for personal expense tracking with automatic financial analytics and reporting.

## Why I built this

I've always struggled with financial literacy, and existing finance apps never felt convenient to me. Since I spend a lot of time in Telegram, I decided to build a bot that lets me track expenses without leaving the app — just send a message like `500 food pizza` and it's saved. This project also gave me a chance to explore NLP and ML classification on a real-world problem.

## Features

- **Expense tracking** — add expenses in natural format: `amount category description`
- **Daily & weekly reports** — grouped by category with totals
- **Category analytics** — pie charts generated with Matplotlib
- **Budget limits** — set daily/weekly limits with notifications
- **Multi-currency** — EUR, USD, UAH, GBP
- **Multilingual** — English, Russian, Ukrainian
- **Data export** — CSV export of all expenses

## Tech Stack

- **Python** 3.11
- **aiogram** 3.24.0 — Telegram Bot API framework
- **SQLAlchemy** 2.0 — ORM for database operations
- **SQLite** — local database
- **Pandas** — data analysis
- **Matplotlib / Seaborn** — data visualization
- **scikit-learn** — ML experiments

## Project Structure

```
moneylytics-bot/
├── databases/
│   ├── db.py          # Database connection and session management
│   └── models.py      # SQLAlchemy models (User, Expense)
├── handlers/
│   ├── start.py       # /start + registration
│   ├── onboarding.py  # New user onboarding
│   ├── expenses.py    # Expense input parsing
│   ├── reports.py     # Daily/weekly/category reports
│   ├── budget.py      # Budget limits and notifications
│   └── callbacks.py   # Inline buttons, edit/delete, export
├── utils/
│   ├── translations.py  # i18n (EN/RU/UK)
│   ├── keyboards.py     # Reply and inline keyboards
│   ├── currency.py      # Currency mappings
│   ├── analytics.py     # Analytics helpers
│   └── charts.py        # Chart generation
└── main.py
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

### Next steps

- Collect real transaction descriptions from bot users
- Use user corrections as labeled training data
- Retrain ML fallback on 500+ samples per class and compare again

## Installation

```bash
git clone https://github.com/Astronom2617/moneylytics-bot.git
cd moneylytics-bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your BOT_TOKEN to .env
python main.py
```

## Usage

### Commands

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

Amount is required. Category is required. Description is optional.

## License

MIT
