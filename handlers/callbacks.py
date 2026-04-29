from aiogram import Router, html, F
from aiogram.types import CallbackQuery, Message
from datetime import datetime, time, timedelta
from sqlalchemy import func

from databases import get_session, User, Expense
from utils.keyboards import get_main_menu, get_currency_keyboard
from utils.currency import CURRENCY_SYMBOLS
from aiogram.fsm.context import FSMContext
from handlers.budget import BudgetStates

router = Router()

def get_budget_periods() -> tuple[datetime, datetime, datetime, datetime]:
    """Get date ranges for today and the current week."""
    now = datetime.now()
    today_start = datetime.combine(now, time.min)
    today_end = datetime.combine(now, time.max)
    week_start = today_start - timedelta(days=now.weekday())
    week_end = today_end
    return today_start, today_end, week_start, week_end

# Callback for choosing setting
@router.callback_query(F.data.startswith("set:"))
async def process_settings_selection(callback: CallbackQuery):
    """Handle a settings menu selection callback and route to the appropriate setting.

    Args:
        callback: The callback query containing the selected setting identifier.
    """
    settings = callback.data.split(":")[1]
    if settings == "cur":
        await callback.message.edit_text(
            "Choose your currency.",
            reply_markup=get_currency_keyboard()
        )
    elif settings == "lang":
        await callback.message.edit_text("Language is under development 🚧")
    else:
        await callback.message.edit_text("Unknown setting")

# Callback for changing currency
@router.callback_query(F.data.startswith("currency_"))
async def process_currency_selection(callback: CallbackQuery):
    """Handle a currency selection callback and update the user's currency in the database.

    Args:
        callback: The callback query containing the selected currency code.
    """
    currency = callback.data.split("_")[1]
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        was_empty = (user is None) or (user.currency is None) or (user.currency == "")
        if user is None:
            new_user = User(
                id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                currency=currency,
            )
            session.add(new_user)
        else:
            user.currency = currency

        session.commit()

        await callback.message.answer(
        f"✅ Great! Your currency is set to {CURRENCY_SYMBOLS.get(currency)}.",
        reply_markup = get_main_menu()
    )

    if was_empty:
        text_mini_instruction = f"""
            {html.bold('📖 How to add expenses:')}
            Send a message in format:
            {html.code('amount category description')}
            Example: {html.code('500 food pizza')}
            """

        await callback.message.answer(text_mini_instruction)

    await callback.answer()

# Setting Budget
async def set_budget(message: Message, state: FSMContext, field: str, label: str):
    """Set daily or weekly budget for a user.

    Parses the amount from message text, saves it to the database,
    and sends confirmation with currency symbol.

    Args:
        message: Telegram message containing the budget amount.
        state: FSM context to clear after setting budget.
        field: Database field name ("daily_budget" or "weekly_budget").
        label: Display label for the response ("Daily budget" or "Weekly budget").
    """
    raw_text = message.text
    try:
        amount = float(raw_text.replace(",", "."))
    except ValueError:
        await message.answer(f"'{raw_text}' is not a number!")
        return

    if amount <= 0:
        await message.answer("❌ Budget must be positive!")
        return

    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        if user is None:
            user = User(
                id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                currency="EUR",
            )
            session.add(user)
        setattr(user, field, amount)
        session.commit()
        currency = user.currency or "EUR"

    await state.clear()

    await message.answer(html.bold(
        f"{label} set to {amount:.2f} {CURRENCY_SYMBOLS.get(currency, currency)} ✅"
    ))

async def clear_budget(callback: CallbackQuery, field: str, label: str):
    """Clear a budget limit for the user."""
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user is None:
            await callback.message.answer("User not found! Use /start first!")
            await callback.answer()
            return
        setattr(user, field, None)
        session.commit()

    await callback.message.answer(f"{label} cleared ✅")
    await callback.answer()

@router.callback_query(F.data == "budget_view")
async def process_budget_view(callback: CallbackQuery):
    """Show current budget limits and spending totals."""
    today_start, today_end, week_start, week_end = get_budget_periods()

    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user is None:
            await callback.message.answer("User not found! Use /start first!")
            await callback.answer()
            return

        currency = user.currency or "EUR"
        currency_symbol = CURRENCY_SYMBOLS.get(currency, currency)

        daily_total = session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
            Expense.user_id == callback.from_user.id,
            Expense.created_at >= today_start,
            Expense.created_at <= today_end
        ).scalar() or 0.0

        weekly_total = session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
            Expense.user_id == callback.from_user.id,
            Expense.created_at >= week_start,
            Expense.created_at <= week_end
        ).scalar() or 0.0

    daily_limit = f"{user.daily_budget:.2f} {currency_symbol}" if user.daily_budget else "Not set"
    weekly_limit = f"{user.weekly_budget:.2f} {currency_symbol}" if user.weekly_budget else "Not set"

    report = (
        f"{html.bold('💰 Budget overview')}\n\n"
        f"📅 Daily limit: {daily_limit}\n"
        f"Spent today: {daily_total:.2f} {currency_symbol}\n\n"
        f"📆 Weekly limit: {weekly_limit}\n"
        f"Spent this week: {weekly_total:.2f} {currency_symbol}"
    )

    await callback.message.answer(report)
    await callback.answer()

@router.callback_query(F.data == "budget_reset_daily")
async def process_budget_reset_daily(callback: CallbackQuery):
    """Clear the user's daily budget."""
    await clear_budget(callback, "daily_budget", "Daily budget")

@router.callback_query(F.data == "budget_reset_weekly")
async def process_budget_reset_weekly(callback: CallbackQuery):
    """Clear the user's weekly budget."""
    await clear_budget(callback, "weekly_budget", "Weekly budget")

# Setting daily budget
@router.callback_query(F.data.startswith("budget_daily"))
async def process_budget_daily(callback: CallbackQuery, state: FSMContext):
    """Handle the daily budget callback and prompt the user to enter a daily budget amount.

    Args:
        callback: The callback query that triggered the daily budget flow.
        state: The FSM context used to set the waiting state.
    """
    await state.set_state(BudgetStates.waiting_for_daily_budget)
    await callback.message.answer("Enter your daily budget amount:")
    await callback.answer()

@router.message(BudgetStates.waiting_for_daily_budget)
async def process_daily_budget(message: Message, state: FSMContext):
    """Receive and save the daily budget amount entered by the user.

    Args:
        message: The incoming Telegram message containing the budget value.
        state: The FSM context used to clear the waiting state after saving.
    """
    await set_budget(message, state, "daily_budget", "Daily budget")

# Setting weekly budget
@router.callback_query(F.data.startswith("budget_weekly"))
async def process_budget_weekly(callback: CallbackQuery, state: FSMContext):
    """Handle the weekly budget callback and prompt the user to enter a weekly budget amount.

    Args:
        callback: The callback query that triggered the weekly budget flow.
        state: The FSM context used to set the waiting state.
    """
    await state.set_state(BudgetStates.waiting_for_weekly_budget)
    await callback.message.answer("Enter your weekly budget amount:")
    await callback.answer()

@router.message(BudgetStates.waiting_for_weekly_budget)
async def process_weekly_budget(message: Message, state: FSMContext):
    """Receive and save the weekly budget amount entered by the user.

    Args:
        message: The incoming Telegram message containing the budget value.
        state: The FSM context used to clear the waiting state after saving.
    """
    await set_budget(message, state, "weekly_budget", "Weekly budget")
