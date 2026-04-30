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
from utils.translations import detect_language, get_user_language, text_options, t, t_category

router = Router()

def get_currency_symbol(currency: str | None) -> str:
    code = currency or "EUR"
    return CURRENCY_SYMBOLS.get(code, code)

# Get expenses by period
def get_expenses_by_period(user_id: int, start_date: datetime, end_date: datetime) -> list:
    """Get all user expenses within a date range.

    Args:
        user_id: Telegram user ID.
        start_date: Start of the period (inclusive).
        end_date: End of the period (inclusive).

    Returns:
        List of Expense objects for the given period.
    """
    with get_session() as session:
        expenses = session.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.created_at >= start_date,
            Expense.created_at <= end_date
        ).all()
        return expenses

# Build expense report
def build_expense_report(expenses: list, title: str, largest_expense_title: str, lang: str) -> str:
    """Build formatted HTML expense report grouped by category.

    Groups expenses by category, calculates totals per category
    and overall, and highlights the largest expense.

    Args:
        expenses: List of Expense objects to include in the report.
        title: Report header, e.g. "📊 Today's report (20 Feb)".
        largest_expense_title: Label for largest expense, e.g. "Largest expense today".

    Returns:
        Formatted HTML string ready to send via Telegram.
    """
    report = html.bold(f"{title}:\n")
    expenses_by_currency = defaultdict(list)
    for expense in expenses:
        expenses_by_currency[expense.currency or "EUR"].append(expense)

    for currency in sorted(expenses_by_currency):
        currency_symbol = get_currency_symbol(currency)
        report += html.bold(f"\n{t(lang, 'reports.currency_section', currency=currency)}\n")
        categories = defaultdict(list)
        for expense in expenses_by_currency[currency]:
            categories[expense.category].append(expense)

        for category in sorted(categories):
            cat_expenses = categories[category]
            category_total = sum(e.amount for e in cat_expenses)
            category_label = t_category(lang, category)
            report += html.bold(
                f"\n{category_label} ({len(cat_expenses)}) - {category_total:.2f} {currency_symbol}:\n"
            )
            for expense in sorted(cat_expenses, key=lambda e: e.amount, reverse=True):
                if expense.description:
                    report += html.bold(
                        f"\n  • {expense.amount:.2f} {currency_symbol} - {expense.description.capitalize()}\n"
                    )
                else:
                    report += html.bold(f"\n  • {expense.amount:.2f} {currency_symbol}\n")

    totals_by_currency = {
        currency: sum(exp.amount for exp in currency_expenses)
        for currency, currency_expenses in expenses_by_currency.items()
    }
    report += "━━━━━━━━━━━━━━━\n"
    if len(totals_by_currency) == 1:
        currency, total = next(iter(totals_by_currency.items()))
        currency_symbol = get_currency_symbol(currency)
        report += html.bold(t(lang, "reports.total_label", total=f"{total:.2f}", currency=currency_symbol) + "\n")
    else:
        report += html.bold(t(lang, "reports.totals_by_currency") + "\n")
        for currency in sorted(totals_by_currency):
            currency_symbol = get_currency_symbol(currency)
            total = totals_by_currency[currency]
            report += html.bold(t(lang, "reports.total_currency_line", total=f"{total:.2f}", currency=f"{currency_symbol} ({currency})") + "\n")

    for currency in sorted(expenses_by_currency):
        currency_symbol = get_currency_symbol(currency)
        largest_expense = max(expenses_by_currency[currency], key=lambda e: e.amount)
        report += html.italic(
            html.bold(
                f"\n🏆 {largest_expense_title} ({currency}): {largest_expense.amount:.2f} {currency_symbol}  - {largest_expense.description.capitalize() if largest_expense.description else ''} ({t_category(lang, largest_expense.category)})"
            )
        )
    return report

# /today
@router.message(Command("today"))
@router.message(F.text.in_(text_options("menu.today")))
async def daily_report(message: Message):
    """Handle the /today command or Today button, sending a report of today's expenses.

    Args:
        message: The incoming Telegram message.
    """
    today_start = datetime.combine(datetime.now(), time.min)
    today_end = datetime.combine(datetime.now(), time.max)

    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))
    expenses = get_expenses_by_period(message.from_user.id, today_start, today_end)

    if not expenses:
        await message.answer(t(lang, "reports.no_today"))
        return

    day_today =datetime.now().strftime("%d %b")
    report = build_expense_report(
        expenses,
        title=t(lang, "reports.title_today", date=day_today),
        largest_expense_title=t(lang, "reports.largest_today"),
        lang=lang
    )
    await message.answer(report)


# /week
@router.message(Command("week"))
@router.message(F.text.in_(text_options("menu.week")))
async def weekly_report(message: Message):
    """Handle the /week command or Week button, sending a report of the past week's expenses.

    Args:
        message: The incoming Telegram message.
    """

    today_start = datetime.combine(datetime.now(), time.min)
    week_start = today_start - timedelta(days=datetime.now().weekday())
    week_end = datetime.combine(datetime.now(), time.max)

    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))
    expenses = get_expenses_by_period(message.from_user.id, week_start, week_end)

    if not expenses:
        await message.answer(t(lang, "reports.no_week"))
        return

    start_date = week_start.strftime("%d.%m")
    end_date = week_end.strftime("%d.%m")
    report = build_expense_report(
        expenses,
        title=t(lang, "reports.title_week", start=start_date, end=end_date),
        largest_expense_title=t(lang, "reports.largest_week"),
        lang=lang
    )
    await message.answer(report)

# /categories
@router.message(Command("categories"))
@router.message(F.text.in_(text_options("menu.categories")))
async def button_categories(message: Message):
    """Handle the /categories command or Categories button, sending a pie chart of monthly expenses.

    Args:
        message: The incoming Telegram message.
    """
    month_start = datetime.combine(datetime.now().replace(day=1), time.min)
    month_end = datetime.now()
    start_str = month_start.strftime("%d.%m")
    end_str = month_end.strftime("%d.%m")

    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))
        expenses = session.query(Expense).filter(
            Expense.user_id == message.from_user.id,
            Expense.created_at >= month_start,
            Expense.created_at <= month_end
        ).all()

        if not expenses:
            await message.answer(t(lang, "reports.no_month"))
            return

        expenses_by_currency = defaultdict(list)
        for expense in expenses:
            expenses_by_currency[expense.currency or "EUR"].append(expense)

        await message.answer(t(lang, "reports.chart_caption", start=start_str, end=end_str))

        for currency in sorted(expenses_by_currency):
            currency_symbol = get_currency_symbol(currency)
            currency_expenses = expenses_by_currency[currency]
            data = [(e.category, e.amount) for e in currency_expenses]

            df_expenses = pd.DataFrame(data, columns=["category", "amount"])
            category_totals = df_expenses.groupby("category")["amount"].sum()

            plt.figure(figsize=(8, 8), dpi=300)
            labels = [
                f"{t_category(lang, cat)}: {amount:.0f}{currency_symbol}"
                for cat, amount in category_totals.items()
            ]

            category_totals.plot(
                kind="pie",
                autopct="%1.0f%%",
                colors=["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8"],
                labels=labels
            )

            plt.title(t(lang, "reports.chart_title_currency", start=start_str, end=end_str, currency=currency))
            plt.ylabel("")

            buffer = BytesIO()
            plt.savefig(buffer, format="png")
            buffer.seek(0)
            plt.close()

            photo = BufferedInputFile(buffer.read(), filename=f"categories_{currency}.png")
            await message.answer_photo(photo)
