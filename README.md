# 💰 Moneylytics Bot

A Telegram bot for personal expense tracking with automatic financial analytics and reporting.

## 📋 Description

Moneylytics Bot helps you track your daily expenses directly in Telegram. Simply send a message with the amount, category, and description, and the bot will save it to the database. Get daily and weekly reports, view spending by categories, and set budget limits.

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

4. Create `.env` file in the root directory:
```env
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
- `/week` - Get weekly expense report (coming soon)
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
│   ├── __init__.py
│   ├── models.py      # SQLAlchemy models (User, Expense)
│   └── db.py          # Database connection and session management
├── handlers/
│   ├── start.py       # /start command handler
│   ├── expenses.py    # Expense input handler
│   └── reports.py     # Analytics and reports handlers
├── utils/             # Utility functions (planned)
├── main.py            # Bot entry point
├── requirements.txt   # Project dependencies
├── .env              # Environment variables (not in repo)
├── .gitignore
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
- [ ] Weekly reports
- [ ] Category-based analytics with charts
- [ ] Budget management (set limits, notifications)
- [ ] Edit/delete expenses
- [ ] Data export

## 📝 License

MIT

## 👤 Author

astro2617 - [@astro2617](https://t.me/qqastro)