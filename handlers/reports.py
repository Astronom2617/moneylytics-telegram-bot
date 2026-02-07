from aiogram import Router, html, F
from aiogram.filters import Command
from aiogram.types import Message
from collections import defaultdict

from databases import get_session, Expense, User
from datetime import datetime, time, timedelta

from handlers.start import CURRENCY_SYMBOLS

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

        categories_d = defaultdict(float)
        for expense in expenses:
            categories_d[expense.category] += expense.amount

        sum_expenses = sum(expense.amount for expense in expenses)

        report_today = html.bold("📊 Today's report:\n\n")

        for category, total in categories_d.items():
            report_today += html.bold(f"💰 {category.capitalize()}: {total:.2f} {currency_symbol}\n")

        report_today += "\n━━━━━━━━━━━━━━━\n"
        report_today += html.bold(f"Total: {sum_expenses:.2f} {currency_symbol}")

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
            await message.answer("You don't have any expenses on this week")
            return

        categories_w = defaultdict(float)
        for expense in expenses:
            categories_w[expense.category] += expense.amount

        sum_expenses = sum(expense.amount for expense in expenses)

        report_week = html.bold(f"📊 Weekly report ({start_date} - {end_date}):\n\n")

        for category, total in categories_w.items():
            report_week += html.bold(f"💰 {category.capitalize()}: {total:.2f} {currency_symbol}\n")

        report_week += "\n━━━━━━━━━━━━━━━\n"
        report_week += html.bold(f"Total: {sum_expenses:.2f} {currency_symbol}")

        await message.answer(report_week)

# /categories
@router.message(Command("/categories"))
@router.message(F.text == "📈 Categories")
async def button_categories(message: Message):
    await message.answer("📈 Categories report is under development 🚧")