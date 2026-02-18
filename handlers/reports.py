from typing import Any

from aiogram import Router, html, F
from aiogram.filters import Command
from aiogram.types import Message
from collections import defaultdict

from databases import get_session, Expense, User
from datetime import datetime, time, timedelta
import pandas as pd
import matplotlib.pyplot as plt

from io import BytesIO
from aiogram.types import BufferedInputFile

from utils.currency import CURRENCY_SYMBOLS

router = Router()

# Get user currency
def get_user_currency(user_id: int) -> tuple[str, str]:
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user and user.currency:
            currency = user.currency
        else:
            currency = "EUR"

        currency_symbol = CURRENCY_SYMBOLS.get(currency, currency)

        return currency, currency_symbol

# Get expenses by period
def get_expenses_by_period(user_id: int, start_date: datetime, end_date: datetime) -> list:
    with get_session() as session:
        expenses = session.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.created_at >= start_date,
            Expense.created_at <= end_date
        ).all()
        return expenses

# Build expense report
def build_expense_report(expenses: list, title: str, currency_symbol: str, largest_expense_title: str) -> str:
    report = html.bold(f"{title}:\n")
    categories = defaultdict(list)
    for expense in expenses:
        categories[expense.category].append(expense)

    for category in sorted(categories):
        cat_expenses = categories[category]

        category_total = sum(e.amount for e in cat_expenses)

        report += html.bold(
            f"\n{category.capitalize()} ({(len(cat_expenses))}) — {category_total:.2f} {currency_symbol}:\n")

        for expense in sorted(cat_expenses, key=lambda e: e.amount, reverse=True):
            if expense.description:
                report += html.bold(
                    f"\n  • {expense.amount:.2f} {currency_symbol} - {expense.description.capitalize()}\n"
                )
            else:
                report += html.bold(
                    f"\n  • {expense.amount:.2f} {currency_symbol}\n"
                )

    total = sum(e.amount for e in expenses)
    report += "━━━━━━━━━━━━━━━\n"
    report += html.bold(f"💰 Total: {total:.2f} {currency_symbol}\n")
    largest_expense = max(expenses, key=lambda e: e.amount)
    report += html.italic(
        html.bold(
            f"\n🏆 {largest_expense_title}: {largest_expense.amount:.2f} {currency_symbol}  — {largest_expense.description.capitalize() if largest_expense.description else ''} ({largest_expense.category.capitalize()})"
        )
    )
    return report

# /today
@router.message(Command("today"))
@router.message(F.text == "📊 Today")
async def daily_report(message: Message):
    today_start = datetime.combine(datetime.now(), time.min)
    today_end = datetime.combine(datetime.now(), time.max)

    currency, currency_symbol = get_user_currency(message.from_user.id)
    expenses = get_expenses_by_period(message.from_user.id, today_start, today_end)

    if not expenses:
        await message.answer("You don't have any expenses today.")
        return

    day_today =datetime.now().strftime("%d %b")
    report = build_expense_report(
        expenses,
        title=f"📊 Today's report ({day_today})",
        currency_symbol=currency_symbol,
        largest_expense_title="Largest expense today"
    )
    await message.answer(report)


# /week
@router.message(Command("week"))
@router.message(F.text == "📅 Week")
async def weekly_report(message: Message):
    week_start = datetime.now() - timedelta(weeks=1)
    week_end =  datetime.now()

    currency, currency_symbol = get_user_currency(message.from_user.id)
    expenses = get_expenses_by_period(message.from_user.id, week_start, week_end)

    if not expenses:
        await message.answer("You don't have any expenses this week.")
        return

    start_date = week_start.strftime("%d.%m")
    end_date = week_end.strftime("%d.%m")
    report = build_expense_report(
        expenses,
        title=f"📊 Weekly report ({start_date} - {end_date})",
        currency_symbol=currency_symbol,
        largest_expense_title="Largest expense this week"
    )
    await message.answer(report)

# /categories
@router.message(Command("categories"))
@router.message(F.text == "📈 Categories")
async def button_categories(message: Message):
    month_start = datetime.now() - timedelta(days=30)
    month_end = datetime.now()

    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        currency = user.currency if user and user.currency else "EUR"
        currency_symbol = CURRENCY_SYMBOLS.get(currency, currency)

        expenses = session.query(Expense).filter(
            Expense.user_id == message.from_user.id,
            Expense.created_at >= month_start,
            Expense.created_at <= month_end
        ).all()

        if not expenses:
            await message.answer("You don't have any expenses on this month.")
            return

        data = [(e.category, e.amount) for e in expenses]

        df_expenses = pd.DataFrame(data, columns=["category", "amount"])
        category_totals = df_expenses.groupby("category")["amount"].sum()

        plt.figure(figsize=(8, 8), dpi=300)

        labels=[f"{cat}: {amount:.0f}{currency_symbol}"
                for cat, amount in category_totals.items()]

        category_totals.plot(
            kind="pie",
            autopct="%1.0f%%",
            colors=["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8"],
            labels=labels
        )

        plt.title("Expenses by Category (Last 30 days)")
        plt.ylabel("")

        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)

        plt.close()

        photo = BufferedInputFile(buffer.read(), filename="categories.png")

        await message.answer("There is your pie chart with all categories for the last 30 days.")
        await message.answer_photo(photo)



