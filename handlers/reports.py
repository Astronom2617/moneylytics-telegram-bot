from aiogram import Router, html
from aiogram.filters import Command
from aiogram.types import Message
from collections import defaultdict

from databases import get_session, Expense
from datetime import datetime, time, timedelta

router = Router()

@router.message(Command("today"))
async def daily_report(message: Message):
    today_start = datetime.combine(datetime.now(), time.min)
    today_end = datetime.combine(datetime.now(), time.max)

    with get_session() as session:
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
            report_today += html.bold(f"💰 {category.capitalize()}: {total:.2f}€\n")

        report_today += "\n━━━━━━━━━━━━━━━\n"
        report_today += html.bold(f"Total: {sum_expenses:.2f}€")

        await message.answer(report_today)



@router.message(Command("week"))
async def weekly_report(message: Message):
    week_start = datetime.now() - timedelta(weeks=1)
    week_end =  datetime.now()
    start_date = week_start.strftime("%d.%m")
    end_date = week_end.strftime("%d.%m")

    with get_session() as session:
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
            report_week += html.bold(f"💰 {category.capitalize()}: {total:.2f}€\n")

        report_week += "\n━━━━━━━━━━━━━━━\n"
        report_week += html.bold(f"Total: {sum_expenses:.2f}€")

        await message.answer(report_week)

@router.message(Command("category"))
async def category_report(message: Message):
    pass