from aiogram import Router, html, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime, time, timedelta
from sqlalchemy import func

from databases import get_session, Expense, User
from utils.currency import CURRENCY_SYMBOLS
from utils.keyboards import get_expenses_list_keyboard, get_expense_details_keyboard, get_export_keyboard, EXPENSE_CATEGORIES, get_pending_expense_category_keyboard
from utils.translations import detect_language, get_user_language, text_options, t, t_category, normalize_category

router = Router()

class ExpenseEditStates(StatesGroup):
    """FSM states for editing expenses."""
    edit_amount = State()
    edit_category = State()
    edit_description = State()


class AddExpenseStates(StatesGroup):
    waiting_for_category = State()


def get_currency_symbol(currency: str | None) -> str:
    code = currency or "EUR"
    return CURRENCY_SYMBOLS.get(code, code)


async def save_expense_from_data(user_id: int, amount: float, category: str, description: str | None, fallback_currency: str | None = None) -> Expense:
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        currency = (user.currency if user and user.currency else fallback_currency) or "EUR"
        new_expense = Expense(
            user_id=user_id,
            amount=amount,
            category=category,
            currency=currency,
            description=description,
        )
        session.add(new_expense)
        session.commit()
        session.refresh(new_expense)
        return new_expense

@router.message(Command("myexpenses"))
@router.message(F.text.in_(text_options("menu.my_expenses")))
async def list_expenses(message: Message):
    """Show user's recent expenses with selection options.
    
    Args:
        message: The incoming Telegram message.
    """
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        if user is None:
            lang = detect_language(message.from_user.language_code)
            await message.answer(t(lang, "common.profile_missing"))
            return

        lang = get_user_language(user, detect_language(message.from_user.language_code))
        
        # Get last 10 expenses for this user
        expenses = session.query(Expense).filter(
            Expense.user_id == message.from_user.id
        ).order_by(Expense.created_at.desc()).limit(10).all()
        
        if not expenses:
            await message.answer(t(lang, "expenses.empty"))
            return
        
        text = f"{html.bold(t(lang, 'expenses.title'))}\n\n"
        for i, exp in enumerate(expenses, 1):
            if exp.description:
                # normalize and escape description for safe display
                norm_desc = exp.description.strip().replace("\n", " ")
                desc_text = f" - {html.quote(norm_desc)}"
            else:
                desc_text = ""
            expense_currency_symbol = get_currency_symbol(exp.currency)
            text += f"{i}. {exp.amount:.2f}{expense_currency_symbol} {t_category(lang, exp.category)}{desc_text}\n"
        
        text += f"\n{html.italic(t(lang, 'expenses.select_prompt'))}"
        
        await message.answer(text, reply_markup=get_expenses_list_keyboard(expenses, lang))

@router.message(Command("export"))
@router.message(F.text.in_(text_options("menu.export")))
async def export_menu(message: Message):
    """Show export options for the user as inline buttons."""
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))

    await message.answer(t(lang, "export.menu_title"), reply_markup=get_export_keyboard(lang))

@router.message()
async def add_expenses(message: Message, state: FSMContext):
    """Parse an incoming message and save a new expense for the user.

    Args:
        message: The incoming Telegram message in the format 'amount category [description]'.
    """
    lang = detect_language(message.from_user.language_code)
    text = message.text or ""
    parts = text.split()

    if len(parts) < 1:
        await message.answer(t(lang, "expenses.missing_fields"))
        return

    try:
        amount = float(parts[0].replace(",", "."))
        parsed_category = normalize_category(parts[1]) if len(parts) > 1 else None
    except ValueError:
        await message.answer(t(lang, "expenses.invalid_number", value=html.quote(parts[0])))
        return

    if amount <= 0:
        await message.answer(t(lang, "expenses.amount_positive"))
        return

    if amount > 1_000_000:
        await message.answer(t(lang, "expenses.amount_too_large"))
        return

    category = parsed_category if parsed_category in EXPENSE_CATEGORIES else None

    if category:
        description = " ".join(parts[2:]) if len(parts) > 2 else None
    else:
        description = " ".join(parts[1:]) if len(parts) > 1 else None

    if not category:
        await state.set_state(AddExpenseStates.waiting_for_category)
        with get_session() as session:
            user = session.query(User).filter(User.id == message.from_user.id).first()
            lang = get_user_language(user, detect_language(message.from_user.language_code))
            fallback_currency = user.currency if user and user.currency else "EUR"
        await state.update_data(
            pending_amount=amount,
            pending_description=description,
            pending_currency=fallback_currency,
        )
        await message.answer(
            t(lang, "expenses.invalid_or_missing_category") + "\n" + t(lang, "expenses.choose_category_to_save"),
            reply_markup=get_pending_expense_category_keyboard(lang)
        )
        return

    saved_expense = await save_expense_from_data(
        user_id=message.from_user.id,
        amount=amount,
        category=category,
        description=description,
    )

    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))
        currency_symbol = get_currency_symbol(saved_expense.currency)
        if description:
            clean_description = description.strip().replace("\n", " ")
            desc_text = " (" + html.quote(clean_description) + ")"
        else:
            desc_text = ""
        await message.answer(html.bold(t(lang, "expense.saved", amount=f"{amount:.2f}", currency=currency_symbol, category=html.quote(t_category(lang, category)), description=desc_text)))

        if user and (user.daily_budget or user.weekly_budget):
            now = datetime.now()
            today_start = datetime.combine(now, time.min)
            today_end = datetime.combine(now, time.max)
            week_start = today_start - timedelta(days=now.weekday())
            week_end = today_end

            daily_total = session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
                Expense.user_id == message.from_user.id,
                Expense.currency == saved_expense.currency,
                Expense.created_at >= today_start,
                Expense.created_at <= today_end
            ).scalar() or 0.0

            weekly_total = session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
                Expense.user_id == message.from_user.id,
                Expense.currency == saved_expense.currency,
                Expense.created_at >= week_start,
                Expense.created_at <= week_end
            ).scalar() or 0.0

            warnings = []
            if user.daily_budget and daily_total > user.daily_budget:
                warnings.append(
                    t(lang, "budget.daily_exceeded", total=f"{daily_total:.2f}", currency=currency_symbol, limit=f"{user.daily_budget:.2f}")
                )
            if user.weekly_budget and weekly_total > user.weekly_budget:
                warnings.append(
                    t(lang, "budget.weekly_exceeded", total=f"{weekly_total:.2f}", currency=currency_symbol, limit=f"{user.weekly_budget:.2f}")
                )

            if warnings:
                await message.answer("\n".join(warnings))


@router.callback_query(F.data.startswith("pending_expense_category:"))
async def pending_expense_category_selected(callback: CallbackQuery, state: FSMContext):
    """Handle category selection for a pending (not yet saved) expense."""
    new_category = callback.data.split(":", 1)[1]
    if new_category not in EXPENSE_CATEGORIES:
        await callback.answer()
        return

    data = await state.get_data()
    amount = data.get("pending_amount")
    description = data.get("pending_description")
    fallback_currency = data.get("pending_currency")

    if amount is None:
        with get_session() as session:
            user = session.query(User).filter(User.id == callback.from_user.id).first()
            lang = get_user_language(user, detect_language(callback.from_user.language_code))
        await callback.message.edit_text(t(lang, "expense.cancelled"))
        await state.clear()
        await callback.answer()
        return

    saved_expense = await save_expense_from_data(
        user_id=callback.from_user.id,
        amount=float(amount),
        category=new_category,
        description=description,
        fallback_currency=fallback_currency,
    )

    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))

    currency_symbol = get_currency_symbol(saved_expense.currency)
    if description:
        clean_description = description.strip().replace("\n", " ")
        desc_text = " (" + html.quote(clean_description) + ")"
    else:
        desc_text = ""

    await callback.message.edit_text(
        html.bold(
            t(
                lang,
                "expense.saved",
                amount=f"{saved_expense.amount:.2f}",
                currency=currency_symbol,
                category=html.quote(t_category(lang, new_category)),
                description=desc_text,
            )
        )
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "pending_expense_cancel")
async def pending_expense_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel pending new expense category clarification."""
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
    await state.clear()
    await callback.message.edit_text(t(lang, "expenses.add_cancelled"))
    await callback.answer()


