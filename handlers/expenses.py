from aiogram import Router, html, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime, time, timedelta
from sqlalchemy import func

from databases import get_session, Expense, User
from utils.currency import CURRENCY_SYMBOLS
from utils.keyboards import get_expenses_list_keyboard, get_expense_details_keyboard, get_export_keyboard

router = Router()

class ExpenseEditStates(StatesGroup):
    """FSM states for editing expenses."""
    edit_amount = State()
    edit_category = State()
    edit_description = State()

@router.message(Command("myexpenses"))
@router.message(F.text == "📝 My Expenses")
async def list_expenses(message: Message):
    """Show user's recent expenses with selection options.
    
    Args:
        message: The incoming Telegram message.
    """
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        if user is None:
            await message.answer("I couldn't find your profile — please send /start to register.")
            return
        
        # Get last 10 expenses for this user
        expenses = session.query(Expense).filter(
            Expense.user_id == message.from_user.id
        ).order_by(Expense.created_at.desc()).limit(10).all()
        
        if not expenses:
            await message.answer(f"You don't have any expenses yet. Start adding expenses with: {html.code('amount category description')}")
            return
        
        currency_symbol = CURRENCY_SYMBOLS.get(user.currency, "€") if user.currency else "€"
        
        text = f"{html.bold('📝 Your Recent Expenses:')}\n\n"
        for i, exp in enumerate(expenses, 1):
            if exp.description:
                # normalize and escape description for safe display
                norm_desc = exp.description.strip().replace("\n", " ")
                desc_text = f" - {html.quote(norm_desc)}"
            else:
                desc_text = ""
            text += f"{i}. {exp.amount:.2f}{currency_symbol} {exp.category.capitalize()}{desc_text}\n"
        
        text += f"\n{html.italic('Select an expense to edit or delete:')}"
        
        await message.answer(text, reply_markup=get_expenses_list_keyboard(expenses))

@router.message(Command("export"))
@router.message(F.text == "📤 Export")
async def export_menu(message: Message):
    """Show export options for the user as inline buttons."""
    await message.answer("Choose export option:", reply_markup=get_export_keyboard())

@router.message()
async def add_expenses(message: Message):
    """Parse an incoming message and save a new expense for the user.

    Args:
        message: The incoming Telegram message in the format 'amount category [description]'.
    """
    text = message.text
    parts = text.split()

    if len(parts) < 2:
        await message.answer("You must provide at least an amount and a category")
        return

    try:
        amount = float(parts[0].replace(",", "."))
        category = parts[1].lower().strip()
        description = " ".join(parts[2:]) if len(parts) > 2 else None
    except ValueError:
        await message.answer(f"'{parts[0]}' is not a number!")
        return

    if amount <= 0:
        await message.answer("❌ Amount must be positive!")
        return

    if amount > 1_000_000:
        await message.answer("⚠️ Are you sure? That's over 1,000,000!")
        return

    with get_session() as session:
        new_expense = Expense(user_id=message.from_user.id,
                            amount=amount,
                            category=category,
                            description=description)
        session.add(new_expense)
        session.commit()

        user = session.query(User).filter(User.id == message.from_user.id).first()
        currency_symbol = CURRENCY_SYMBOLS.get(user.currency, "€") if user else "€"
        desc_text = f" ({description.capitalize()})" if description else ""
        await message.answer(html.bold(f"✅ Saved: {amount:.2f}{currency_symbol} — {category}{desc_text}"))

        if user and (user.daily_budget or user.weekly_budget):
            now = datetime.now()
            today_start = datetime.combine(now, time.min)
            today_end = datetime.combine(now, time.max)
            week_start = today_start - timedelta(days=now.weekday())
            week_end = today_end

            daily_total = session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
                Expense.user_id == message.from_user.id,
                Expense.created_at >= today_start,
                Expense.created_at <= today_end
            ).scalar() or 0.0

            weekly_total = session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
                Expense.user_id == message.from_user.id,
                Expense.created_at >= week_start,
                Expense.created_at <= week_end
            ).scalar() or 0.0

            warnings = []
            if user.daily_budget and daily_total > user.daily_budget:
                warnings.append(
                    f"⚠️ Daily budget exceeded: {daily_total:.2f} {currency_symbol} / {user.daily_budget:.2f} {currency_symbol}"
                )
            if user.weekly_budget and weekly_total > user.weekly_budget:
                warnings.append(
                    f"⚠️ Weekly budget exceeded: {weekly_total:.2f} {currency_symbol} / {user.weekly_budget:.2f} {currency_symbol}"
                )

            if warnings:
                await message.answer("\n".join(warnings))
