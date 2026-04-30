from aiogram import Router, html, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from datetime import datetime, time, timedelta
from sqlalchemy import func
import csv
from io import StringIO, BytesIO

from databases import get_session, User, Expense
from utils.keyboards import (get_main_menu, get_currency_keyboard, get_expenses_list_keyboard,
                             get_expense_details_keyboard, get_edit_field_keyboard,
                             get_category_keyboard, get_delete_confirmation_keyboard,
                             get_description_edit_keyboard,
                             EXPENSE_CATEGORIES, get_language_keyboard)
from utils.currency import CURRENCY_SYMBOLS
from aiogram.fsm.context import FSMContext
from handlers.budget import BudgetStates
from handlers.expenses import ExpenseEditStates
from utils.translations import detect_language, get_user_language, t, t_category

router = Router()


def get_currency_symbol(currency: str | None) -> str:
    code = currency or "EUR"
    return CURRENCY_SYMBOLS.get(code, code)

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
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
    if settings == "cur":
        await callback.message.edit_text(
            t(lang, "settings.currency"),
            reply_markup=get_currency_keyboard()
        )
    elif settings == "lang":
        await callback.message.edit_text(
            t(lang, "settings.language"),
            reply_markup=get_language_keyboard(lang),
        )
    else:
        await callback.message.edit_text(t(lang, "common.unknown_setting"))

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
            language = detect_language(callback.from_user.language_code)
            new_user = User(
                id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                currency=currency,
                language=language,
            )
            session.add(new_user)
            lang = language
        else:
            user.currency = currency
            if not getattr(user, "language", None):
                user.language = detect_language(callback.from_user.language_code)
            lang = get_user_language(user, detect_language(callback.from_user.language_code))

        session.commit()

        await callback.message.answer(
            t(lang, "currency.updated", currency=CURRENCY_SYMBOLS.get(currency, currency)),
            reply_markup=get_main_menu(lang)
        )

    if was_empty:
        text_mini_instruction = t(lang, "start.add_expenses_hint")

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
    lang = detect_language(message.from_user.language_code)
    try:
        amount = float(raw_text.replace(",", "."))
    except ValueError:
        await message.answer(t(lang, "budget.invalid_number", value=html.quote(raw_text)))
        return

    if amount <= 0:
        await message.answer(t(lang, "budget.amount_positive"))
        return

    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        if user is None:
            language = detect_language(message.from_user.language_code)
            user = User(
                id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                currency="EUR",
                language=language,
            )
            session.add(user)
        setattr(user, field, amount)
        session.commit()
        currency = user.currency or "EUR"
        lang = get_user_language(user, detect_language(message.from_user.language_code))

    await state.clear()

    await message.answer(html.bold(
        t(lang, "budget.set", label=label, amount=f"{amount:.2f}", currency=CURRENCY_SYMBOLS.get(currency, currency))
    ))

async def clear_budget(callback: CallbackQuery, field: str, label: str):
    """Clear a budget limit for the user."""
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user is None:
            await callback.message.answer(t(detect_language(callback.from_user.language_code), "common.profile_missing"))
            await callback.answer()
            return
        setattr(user, field, None)
        session.commit()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))

    await callback.message.answer(t(lang, "budget.cleared", label=label))
    await callback.answer()

@router.callback_query(F.data == "budget_view")
async def process_budget_view(callback: CallbackQuery):
    """Show current budget limits and spending totals."""
    today_start, today_end, week_start, week_end = get_budget_periods()

    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user is None:
            await callback.message.answer(t(detect_language(callback.from_user.language_code), "common.profile_missing"))
            await callback.answer()
            return

        lang = get_user_language(user, detect_language(callback.from_user.language_code))
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

    daily_limit = f"{user.daily_budget:.2f} {currency_symbol}" if user.daily_budget else t(lang, "budget.not_set")
    weekly_limit = f"{user.weekly_budget:.2f} {currency_symbol}" if user.weekly_budget else t(lang, "budget.not_set")

    report = (
        f"{html.bold(t(lang, 'budget.overview_title'))}\n\n"
        f"{t(lang, 'budget.daily_limit_label')}: {daily_limit}\n"
        f"{t(lang, 'budget.spent_today_label')}: {daily_total:.2f} {currency_symbol}\n\n"
        f"{t(lang, 'budget.weekly_limit_label')}: {weekly_limit}\n"
        f"{t(lang, 'budget.spent_week_label')}: {weekly_total:.2f} {currency_symbol}"
    )

    await callback.message.answer(report)
    await callback.answer()

@router.callback_query(F.data == "budget_reset_daily")
async def process_budget_reset_daily(callback: CallbackQuery):
    """Clear the user's daily budget."""
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
    await clear_budget(callback, "daily_budget", t(lang, "budget.daily"))

@router.callback_query(F.data == "budget_reset_weekly")
async def process_budget_reset_weekly(callback: CallbackQuery):
    """Clear the user's weekly budget."""
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
    await clear_budget(callback, "weekly_budget", t(lang, "budget.weekly"))

# Setting daily budget
@router.callback_query(F.data.startswith("budget_daily"))
async def process_budget_daily(callback: CallbackQuery, state: FSMContext):
    """Handle the daily budget callback and prompt the user to enter a daily budget amount.

    Args:
        callback: The callback query that triggered the daily budget flow.
        state: The FSM context used to set the waiting state.
    """
    await state.set_state(BudgetStates.waiting_for_daily_budget)
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
    await callback.message.answer(t(lang, "budget.enter_daily"))
    await callback.answer()

@router.message(BudgetStates.waiting_for_daily_budget)
async def process_daily_budget(message: Message, state: FSMContext):
    """Receive and save the daily budget amount entered by the user.

    Args:
        message: The incoming Telegram message containing the budget value.
        state: The FSM context used to clear the waiting state after saving.
    """
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))

    await set_budget(message, state, "daily_budget", t(lang, "budget.daily"))

# Setting weekly budget
@router.callback_query(F.data.startswith("budget_weekly"))
async def process_budget_weekly(callback: CallbackQuery, state: FSMContext):
    """Handle the weekly budget callback and prompt the user to enter a weekly budget amount.

    Args:
        callback: The callback query that triggered the weekly budget flow.
        state: The FSM context used to set the waiting state.
    """
    await state.set_state(BudgetStates.waiting_for_weekly_budget)
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
    await callback.message.answer(t(lang, "budget.enter_weekly"))
    await callback.answer()

@router.message(BudgetStates.waiting_for_weekly_budget)
async def process_weekly_budget(message: Message, state: FSMContext):
    """Receive and save the weekly budget amount entered by the user.

    Args:
        message: The incoming Telegram message containing the budget value.
        state: The FSM context used to clear the waiting state after saving.
    """
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))

    await set_budget(message, state, "weekly_budget", t(lang, "budget.weekly"))

@router.callback_query(F.data == "lang_en")
@router.callback_query(F.data == "lang_ru")
@router.callback_query(F.data == "lang_uk")
async def process_language_selection(callback: CallbackQuery):
    """Store the selected language and refresh the main menu."""
    new_lang = callback.data.split("_")[1]
    if new_lang not in ("en", "ru", "uk"):
        await callback.answer()
        return

    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user is None:
            user = User(
                id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                currency="EUR",
                language=new_lang,
            )
            session.add(user)
        else:
            user.language = new_lang
        session.commit()

    await callback.message.edit_text(t(new_lang, "language.updated"))
    await callback.message.answer(t(new_lang, "settings.choose"), reply_markup=get_main_menu(new_lang))
    await callback.answer()

# Expense Management Callbacks

@router.callback_query(F.data == "expense_cancel")
async def cancel_expense_flow(callback: CallbackQuery, state: FSMContext):
    """Cancel any ongoing expense edit flow."""
    await state.clear()
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
    await callback.message.edit_text(t(lang, "expense.cancelled"))
    await callback.answer()

@router.callback_query(F.data == "expense_back")
async def back_to_expense_list(callback: CallbackQuery):
    """Go back to expense list."""
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user is None:
            await callback.message.edit_text(t(detect_language(callback.from_user.language_code), "common.profile_missing"))
            await callback.answer()
            return
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
        
        expenses = session.query(Expense).filter(
            Expense.user_id == callback.from_user.id
        ).order_by(Expense.created_at.desc()).limit(10).all()
        
        if not expenses:
            await callback.message.edit_text(t(lang, "expenses.empty"))
            await callback.answer()
            return
        
        text = f"{html.bold(t(lang, 'expenses.title'))}\n\n"
        for i, exp in enumerate(expenses, 1):
            if exp.description:
                norm_desc = exp.description.strip().replace("\n", " ")
                desc_text = f" - {html.quote(norm_desc)}"
            else:
                desc_text = ""
            text += f"{i}. {exp.amount:.2f}{get_currency_symbol(exp.currency)} {t_category(lang, exp.category)}{desc_text}\n"
        
        text += f"\n{html.italic(t(lang, 'expenses.select_prompt'))}"
        
        await callback.message.edit_text(text, reply_markup=get_expenses_list_keyboard(expenses, lang))
    await callback.answer()

@router.callback_query(F.data.startswith("expense_select:"))
async def select_expense(callback: CallbackQuery):
    """Show details of selected expense with edit/delete options."""
    expense_id = int(callback.data.split(":")[1])
    
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text(t(lang, "expense.not_found_permission"))
            await callback.answer()
            return
        
        currency_symbol = get_currency_symbol(expense.currency)
        
        if expense.description:
            norm_desc = expense.description.strip().replace("\n", " ")
            desc_text = f"\n{t(lang, 'expense.description_label')}: {html.quote(norm_desc)}"
        else:
            desc_text = ""
        
        text = (
            f"{html.bold(t(lang, 'expense.details_title'))}\n\n"
            f"{t(lang, 'expense.amount_label')}: {expense.amount:.2f} {currency_symbol}\n"
            f"{t(lang, 'expense.category_label')}: {t_category(lang, expense.category)}{desc_text}\n"
            f"{t(lang, 'expense.date_label')}: {expense.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        
        await callback.message.edit_text(text, reply_markup=get_expense_details_keyboard(expense_id, lang))
    await callback.answer()

@router.callback_query(F.data.startswith("expense_edit:"))
async def edit_expense(callback: CallbackQuery):
    """Show menu to choose which field to edit."""
    expense_id = int(callback.data.split(":")[1])
    
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text(t(lang, "expense.not_found_permission"))
            await callback.answer()
            return
        
        text = f"{html.bold(t(lang, 'expense.choose_edit_field'))}"
        await callback.message.edit_text(text, reply_markup=get_edit_field_keyboard(expense_id, lang))
    await callback.answer()

@router.callback_query(F.data.startswith("expense_edit_amount:"))
async def edit_amount_start(callback: CallbackQuery, state: FSMContext):
    """Start editing amount - prompt user to enter new value."""
    expense_id = int(callback.data.split(":")[1])
    
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text(t(lang, "expense.not_found"))
            await callback.answer()
            return
        
        currency_symbol = get_currency_symbol(expense.currency)
        
        text = t(lang, "expense.current_amount_prompt", amount=f"{expense.amount:.2f}", currency=currency_symbol)
        await callback.message.edit_text(text)
        await state.set_state(ExpenseEditStates.edit_amount)
        await state.update_data(expense_id=expense_id)
    await callback.answer()

@router.message(ExpenseEditStates.edit_amount)
async def process_edit_amount(message: Message, state: FSMContext):
    """Receive and save the new amount."""
    data = await state.get_data()
    expense_id = data.get("expense_id")
    
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))
    
    raw_text = message.text or ""
    try:
        new_amount = float(raw_text.replace(",", "."))
    except ValueError:
        await message.answer(t(lang, "expense.invalid_number", value=html.quote(raw_text)))
        return
    
    if new_amount <= 0:
        await message.answer(t(lang, "expense.amount_positive"))
        return
    
    if new_amount > 1_000_000:
        await message.answer(t(lang, "expense.amount_too_large"))
        return
    
    with get_session() as session:
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == message.from_user.id
        ).first()
        
        if expense is None:
            await message.answer(t(lang, "expense.not_found"))
            await state.clear()
            return
        
        expense.amount = new_amount
        session.commit()
        
        currency_symbol = get_currency_symbol(expense.currency)
    
    await state.clear()
    # Confirm and show updated expense details
    await message.answer(t(lang, "expense.amount_updated", amount=f"{new_amount:.2f}", currency=currency_symbol))
    with get_session() as session:
        updated = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == message.from_user.id
        ).first()
        if updated:
            if updated.description:
                norm_desc = updated.description.strip().replace("\n", " ")
                desc_text = f"\n{t(lang, 'expense.description_label')}: {html.quote(norm_desc)}"
            else:
                desc_text = ""
            currency_symbol = get_currency_symbol(updated.currency)
            details = (
                f"{html.bold(t(lang, 'expense.details_title'))}\n\n"
                f"{t(lang, 'expense.amount_label')}: {updated.amount:.2f} {currency_symbol}\n"
                f"{t(lang, 'expense.category_label')}: {t_category(lang, updated.category)}{desc_text}\n"
                f"{t(lang, 'expense.date_label')}: {updated.created_at.strftime('%d.%m.%Y %H:%M')}"
            )
            await message.answer(details, reply_markup=get_expense_details_keyboard(expense_id, lang))

@router.callback_query(F.data.startswith("expense_edit_category:"))
async def edit_category_start(callback: CallbackQuery, state: FSMContext):
    """Start editing category - show category selection buttons."""
    expense_id = int(callback.data.split(":")[1])
    
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text(t(lang, "expense.not_found"))
            await callback.answer()
            return
        
        text = t(lang, "expense.current_category_prompt", category=t_category(lang, expense.category))
        await callback.message.edit_text(text, reply_markup=get_category_keyboard(expense_id, lang))
        await state.set_state(ExpenseEditStates.edit_category)
        await state.update_data(expense_id=expense_id)
    await callback.answer()

@router.callback_query(F.data.startswith("expense_category_select:"))
async def process_category_select(callback: CallbackQuery, state: FSMContext):
    """Receive and save the new category."""
    new_category = callback.data.split(":")[1]
    data = await state.get_data()
    expense_id = data.get("expense_id")
    
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
    
    if new_category not in EXPENSE_CATEGORIES:
        await callback.message.edit_text(t(lang, "expense.invalid_category"))
        await callback.answer()
        return
    
    with get_session() as session:
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text(t(lang, "expense.not_found"))
            await callback.answer()
            await state.clear()
            return
        
        expense.category = new_category
        session.commit()
    
    await state.clear()
    # Confirmation and show updated details
    await callback.message.answer(t(lang, "expense.category_updated", category=t_category(lang, new_category)))
    with get_session() as session:
        updated = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        if updated:
            if updated.description:
                norm_desc = updated.description.strip().replace("\n", " ")
                desc_text = f"\n{t(lang, 'expense.description_label')}: {html.quote(norm_desc)}"
            else:
                desc_text = ""
            currency_symbol = get_currency_symbol(updated.currency)
            details = (
                f"{html.bold(t(lang, 'expense.details_title'))}\n\n"
                f"{t(lang, 'expense.amount_label')}: {updated.amount:.2f} {currency_symbol}\n"
                f"{t(lang, 'expense.category_label')}: {t_category(lang, updated.category)}{desc_text}\n"
                f"{t(lang, 'expense.date_label')}: {updated.created_at.strftime('%d.%m.%Y %H:%M')}"
            )
            # Edit the original message to show details with inline keyboard
            await callback.message.edit_text(details, reply_markup=get_expense_details_keyboard(expense_id, lang))
    await callback.answer()

@router.callback_query(F.data.startswith("expense_edit_description:"))
async def edit_description_start(callback: CallbackQuery, state: FSMContext):
    """Start editing description - prompt user to enter new value."""
    expense_id = int(callback.data.split(":")[1])
    
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text(t(lang, "expense.not_found"))
            await callback.answer()
            return
        
        if expense.description:
            norm_desc = expense.description.strip().replace("\n", " ")
            current_desc = html.quote(norm_desc)
        else:
            current_desc = t(lang, "expense.none_label")
        text = t(lang, "expense.current_description_prompt", description=current_desc)
        await callback.message.edit_text(text, reply_markup=get_description_edit_keyboard(expense_id, lang))
        await state.set_state(ExpenseEditStates.edit_description)
        await state.update_data(expense_id=expense_id)
    await callback.answer()


@router.callback_query(F.data.startswith("expense_clear_description:"))
async def clear_description_callback(callback: CallbackQuery, state: FSMContext):
    """Clear the description of the expense and show updated details."""
    expense_id = int(callback.data.split(":")[1])

    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()

        if expense is None:
            await callback.message.edit_text(t(lang, "expense.not_found"))
            await callback.answer()
            return

        expense.description = None
        session.commit()

        # Clear any FSM state related to editing
        await state.clear()

        # Confirmation and show updated details
        currency_symbol = get_currency_symbol(expense.currency)
        details = (
            f"{html.bold(t(lang, 'expense.details_title'))}\n\n"
            f"{t(lang, 'expense.amount_label')}: {expense.amount:.2f} {currency_symbol}\n"
            f"{t(lang, 'expense.category_label')}: {t_category(lang, expense.category)}\n"
            f"{t(lang, 'expense.date_label')}: {expense.created_at.strftime('%d.%m.%Y %H:%M')}"
        )

        await callback.message.edit_text(t(lang, "expense.description_cleared"))
        await callback.message.answer(details, reply_markup=get_expense_details_keyboard(expense_id, lang))
    await callback.answer()

@router.message(ExpenseEditStates.edit_description)
async def process_edit_description(message: Message, state: FSMContext):
    """Receive and save the new description."""
    data = await state.get_data()
    expense_id = data.get("expense_id")
    
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))
    
    # Safely handle text: strip whitespace, set to None if empty
    raw_text = message.text or ""
    stripped_text = raw_text.strip()
    new_description = stripped_text if stripped_text else None
    
    with get_session() as session:
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == message.from_user.id
        ).first()
        
        if expense is None:
            await message.answer(t(lang, "expense.not_found"))
            await state.clear()
            return
        
        expense.description = new_description
        session.commit()
    
    await state.clear()
    # Confirmation and show updated details
    if new_description:
        await message.answer(t(lang, "expense.description_updated", description=html.quote(new_description)))
    else:
        await message.answer(t(lang, "expense.description_cleared"))

    with get_session() as session:
        updated = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == message.from_user.id
        ).first()
        if updated:
            if updated.description:
                norm_desc = updated.description.strip().replace("\n", " ")
                desc_text = f"\n{t(lang, 'expense.description_label')}: {html.quote(norm_desc)}"
            else:
                desc_text = ""
            currency_symbol = get_currency_symbol(updated.currency)
            details = (
                f"{html.bold(t(lang, 'expense.details_title'))}\n\n"
                f"{t(lang, 'expense.amount_label')}: {updated.amount:.2f} {currency_symbol}\n"
                f"{t(lang, 'expense.category_label')}: {t_category(lang, updated.category)}{desc_text}\n"
                f"{t(lang, 'expense.date_label')}: {updated.created_at.strftime('%d.%m.%Y %H:%M')}"
            )
            await message.answer(details, reply_markup=get_expense_details_keyboard(expense_id, lang))

@router.callback_query(F.data.startswith("expense_delete:"))
async def delete_expense(callback: CallbackQuery):
    """Show delete confirmation dialog."""
    expense_id = int(callback.data.split(":")[1])
    
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text(t(lang, "expense.not_found_permission"))
            await callback.answer()
            return
        
        currency_symbol = get_currency_symbol(expense.currency)
        
        if expense.description:
            norm_desc = expense.description.strip().replace("\n", " ")
            desc_text = f" - {html.quote(norm_desc)}"
        else:
            desc_text = ""
        text = (
            f"{html.bold(t(lang, 'expense.delete_title'))}\n\n"
            f"{expense.amount:.2f} {currency_symbol} {t_category(lang, expense.category)}{desc_text}\n\n"
            f"{t(lang, 'expense.delete_warning')}"
        )
        
        await callback.message.edit_text(text, reply_markup=get_delete_confirmation_keyboard(expense_id, lang))
    await callback.answer()

@router.callback_query(F.data.startswith("expense_confirm_delete:"))
async def confirm_delete_expense(callback: CallbackQuery):
    """Delete the expense."""
    expense_id = int(callback.data.split(":")[1])
    
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text(t(lang, "expense.not_found"))
            await callback.answer()
            return
        
        amount = expense.amount
        category = expense.category
        
        session.delete(expense)
        session.commit()
    
    await callback.message.edit_text(t(lang, "expense.deleted", amount=f"{amount:.2f}", category=t_category(lang, category)))
    await callback.answer()


# Export callbacks
@router.callback_query(F.data == 'export_cancel')
async def export_cancel(callback: CallbackQuery):
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))

    await callback.message.edit_text(t(lang, 'export.cancelled'))
    await callback.answer()


def build_csv_bytes(expenses: list) -> bytes:
    """Build CSV bytes for given expenses preserving row currency."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'amount', 'category', 'description', 'created_at', 'currency'])
    for e in expenses:
        desc = e.description.strip().replace('\n', ' ') if e.description else ''
        row_currency = e.currency if e.currency else 'EUR'
        writer.writerow([e.id, f"{e.amount:.2f}", e.category, desc, e.created_at.strftime('%Y-%m-%d %H:%M:%S'), row_currency])
    # Encode with UTF-8 with BOM (utf-8-sig) for better Excel compatibility with non-English text
    return output.getvalue().encode('utf-8-sig')


@router.callback_query(F.data == 'export_all')
async def export_all(callback: CallbackQuery):
    """Export all user expenses as CSV and send as document."""
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user is None:
            await callback.message.answer(t(detect_language(callback.from_user.language_code), "common.profile_missing"))
            await callback.answer()
            return

        expenses = session.query(Expense).filter(Expense.user_id == callback.from_user.id).order_by(Expense.created_at.desc()).all()

        if not expenses:
            await callback.message.answer(t(get_user_language(user, detect_language(callback.from_user.language_code)), "export.no_all"))
            await callback.answer()
            return

        csv_bytes = build_csv_bytes(expenses)
        bio = BytesIO(csv_bytes)
        bio.seek(0)
        filename = f"expenses_all_{callback.from_user.id}.csv"
        file = BufferedInputFile(bio.read(), filename=filename)
        await callback.message.answer_document(file)
    await callback.answer(t(get_user_language(user, detect_language(callback.from_user.language_code)), "export.ready"))


@router.callback_query(F.data == 'export_current_month')
async def export_current_month(callback: CallbackQuery):
    """Export current month's expenses as CSV and send as document."""
    now = datetime.now()
    # Start of current month at 00:00:00
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_end = now

    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user is None:
            await callback.message.answer(t(detect_language(callback.from_user.language_code), "common.profile_missing"))
            await callback.answer()
            return

        expenses = session.query(Expense).filter(
            Expense.user_id == callback.from_user.id,
            Expense.created_at >= month_start,
            Expense.created_at <= month_end
        ).order_by(Expense.created_at.desc()).all()

        if not expenses:
            await callback.message.answer(t(get_user_language(user, detect_language(callback.from_user.language_code)), "export.no_month"))
            await callback.answer()
            return

        csv_bytes = build_csv_bytes(expenses)
        bio = BytesIO(csv_bytes)
        bio.seek(0)
        filename = f"expenses_{now.strftime('%Y_%m')}_{callback.from_user.id}.csv"
        file = BufferedInputFile(bio.read(), filename=filename)
        await callback.message.answer_document(file)

    await callback.answer(t(get_user_language(user, detect_language(callback.from_user.language_code)), "export.ready"))


