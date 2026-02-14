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

# /today
@router.message(Command("today"))
@router.message(F.text == "📊 Today")
async def daily_report(message: Message):
    today_start = datetime.combine(datetime.now(), time.min)
    today_end = datetime.combine(datetime.now(), time.max)

    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()

        currency = user.currency if user and user.currency else "EUR"
        currency_symbol = CURRENCY_SYMBOLS.get(currency, currency)

        expenses = session.query(Expense).filter(
            Expense.user_id == message.from_user.id,
            Expense.created_at >= today_start,
            Expense.created_at <= today_end
        ).all()

        if not expenses:
            await message.answer("You don't have any expenses today")
            return

        day_today = datetime.now().strftime("%d %b")
        report_today = html.bold(f"📊 Today's report ({day_today}):\n")

        categories_d = defaultdict(list)
        for expense in expenses:
            categories_d[expense.category].append(expense)

        for category in sorted(categories_d):
            cat_expenses = categories_d[category]

            category_total = sum(e.amount for e in cat_expenses)

            report_today += html.bold(f"\n{category.capitalize()} ({(len(cat_expenses))}) — {category_total:.2f} {currency_symbol}:\n")

            for expense in sorted(cat_expenses, key=lambda e: e.amount, reverse=True):
                if expense.description:
                    report_today += html.bold(
                        f"\n  • {expense.amount:.2f} {currency_symbol} - {expense.description.capitalize()}\n"
                    )
                else:
                    report_today += html.bold(
                        f"\n  • {expense.amount:.2f} {currency_symbol}\n"
                    )

        total = sum(e.amount for e in expenses)
        report_today += "━━━━━━━━━━━━━━━\n"
        report_today += html.bold(f"💰 Total: {total:.2f} {currency_symbol}\n")
        largest_expense = max(expenses, key=lambda e: e.amount)
        report_today += html.italic(
            html.bold(
                f"\n🏆 Largest expense today: {largest_expense.amount:.2f} {currency_symbol}  — {largest_expense.description.capitalize() if largest_expense.description else ''} ({largest_expense.category.capitalize()})"
            )
        )
        await message.answer(report_today)


# /week
@router.message(Command("week"))
@router.message(F.text == "📅 Week")
async def weekly_report(message: Message):
    week_start = datetime.now() - timedelta(weeks=1)
    week_end =  datetime.now()
    start_date = week_start.strftime("%d.%m")
    end_date = week_end.strftime("%d.%m")

    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()

        currency = user.currency if user and user.currency else "EUR"
        currency_symbol = CURRENCY_SYMBOLS.get(currency, currency)

        expenses = session.query(Expense).filter(
            Expense.user_id == message.from_user.id,
            Expense.created_at >= week_start,
            Expense.created_at <= week_end
        ).all()

        if not expenses:
            await message.answer("You don't have any expenses on this week.")
            return

        report_week = html.bold(f"📊 Weekly report ({start_date} - {end_date}):\n")

        categories_w = defaultdict(list)
        for expense in expenses:
            categories_w[expense.category].append(expense)

        for category in sorted(categories_w):
            cat_expenses = categories_w[category]

            category_total = sum(e.amount for e in cat_expenses)

            report_week += html.bold(f"\n{category.capitalize()} ({(len(cat_expenses))}) — {category_total:.2f} {currency_symbol}:\n")

            for expense in sorted(cat_expenses, key=lambda e: e.amount, reverse=True):
                if expense.description:
                    report_week += html.bold(
                        f"\n  • {expense.amount:.2f} {currency_symbol} - {expense.description.capitalize()}\n"
                    )
                else:
                    report_week += html.bold(
                        f"\n  • {expense.amount:.2f} {currency_symbol}\n"
                    )

        total = sum(e.amount for e in expenses)
        report_week += "━━━━━━━━━━━━━━━\n"
        report_week += html.bold(f"💰 Total: {total:.2f} {currency_symbol}\n")
        largest_expense = max(expenses, key=lambda e: e.amount)
        report_week += html.italic(
            html.bold(
                f"\n🏆 Largest expense this week: {largest_expense.amount:.2f} {currency_symbol}  — {largest_expense.description.capitalize() if largest_expense.description else ''} ({largest_expense.category.capitalize()})"
            )
        )

        await message.answer(report_week)

# /categories
@router.message(Command("/categories"))
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



