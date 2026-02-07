# 💰 Moneylytics Bot

A Telegram bot for personal expense tracking with automatic financial analytics and reporting.

## 📋 Description

Moneylytics Bot helps you track your daily expenses directly in Telegram. Simply send a message with the amount, category, and description, and the bot will save it to the database. Get daily and weekly reports, view spending by categories, and set budget limits. Users can select their preferred currency, and all reports display the corresponding currency symbol automatically.


## 🚀 Tech Stack

- **Python** 3.11
- **aiogram** 3.24.0 - Telegram Bot API framework
- **SQLAlchemy** 2.0.46 - ORM for database operations
- **SQLite** - Database
- **Pandas** 3.0.0 - Data analysis
- **Matplotlib** 3.10.8 & **Seaborn** 0.13.2 - Data visualization

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/Astronom2617/moneylytics-bot.git
cd moneylytics-bot
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment file from example:  

Copy `.env.example` and rename it to `.env`:  

### ***Linux/MacOS***
```bash
cp .env.example .env 
```
### ***Windows (PowerShell)***
```bash
copy .env.example .env
```
Then open .env and add your Telegram bot token:
```bash
BOT_TOKEN=your_telegram_bot_token_here
```
5. Run the bot:
```bash
python main.py
```

## 💡 Usage

### Available Commands

- `/start` - Register in the bot and get welcome message
- `/today` - Get daily expense report with category breakdown
- `/week` - Get weekly expense report with category breakdown
- `/setcurrency` - Set preferred currency
- `/categories` - View spending distribution by categories with charts (coming soon)

### Adding Expenses

Simply send a message in the format:
```
<amount> <category> <description>
```

**Examples:**
- `500 food pizza`
- `90 healthcare dental cleaning`
- `150 transport metro card`

The description is optional:
- `50 coffee`

## 📁 Project Structure
```
moneylytics-bot/
├── databases/
│ ├── init.py
│ ├── db.py # Database connection and session management
│ └── models.py # SQLAlchemy models (User, Expense)
├── handlers/
│ ├── init.py
│ ├── start.py # /start + basic commands
│ ├── onboarding.py # New user onboarding (currency setup)
│ ├── callbacks.py # Inline callbacks (settings, currency selection)
│ ├── expenses.py # Expense input handler
│ ├── reports.py # Analytics and reports handlers
│ └── budget.py # Budget features (in progress)
├── utils/
│ ├── init.py
│ ├── keyboards.py # Reply/Inline keyboards
│ ├── currency.py # Currency mappings and symbols
│ ├── analytics.py # Analytics helpers
│ └── charts.py # Charts generation (matplotlib)
├── main.py # Bot entry point
├── requirements.txt # Project dependencies
├── .env # Environment variables (not in repo)
├── .env.example # Example env file
├── .gitignore
├── moneylytics_bot.db # SQLite database (local)
└── README.md
```

## 🗄️ Database Schema

### Users Table
- `id` - Telegram user ID (primary key)
- `username` - Telegram username
- `first_name` - User's first name
- `created_at` - Registration timestamp
- `daily_budget` - Daily spending limit (optional)
- `weekly_budget` - Weekly spending limit (optional)
- `currency` - User preferred currency (EUR/USD/UAH/GBP etc.)

### Expenses Table
- `id` - Auto-increment primary key
- `user_id` - Foreign key to users table
- `amount` - Expense amount
- `category` - Expense category
- `description` - Optional description
- `created_at` - Timestamp

## 🔮 Roadmap

- [x] User registration
- [x] Expense tracking
- [x] Daily reports
- [x] Weekly reports
- [ ] Category-based analytics with charts
- [ ] Budget management (set limits, notifications)
- [ ] Edit/delete expenses
- [ ] Data export

## 📝 License

MIT

## 👤 Author

astro2617 - [@astro2617](https://t.me/qqastro)