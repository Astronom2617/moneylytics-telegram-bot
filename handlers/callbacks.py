from aiogram import Router, html, F
from aiogram.types import CallbackQuery, Message
from datetime import datetime, time, timedelta
from sqlalchemy import func

from databases import get_session, User, Expense
from utils.keyboards import (get_main_menu, get_currency_keyboard, get_expenses_list_keyboard,
                              get_expense_details_keyboard, get_edit_field_keyboard,
                              get_category_keyboard, get_delete_confirmation_keyboard,
                              get_description_edit_keyboard,
                              EXPENSE_CATEGORIES)
from utils.currency import CURRENCY_SYMBOLS
from aiogram.fsm.context import FSMContext
from handlers.budget import BudgetStates
from handlers.expenses import ExpenseEditStates

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

# Expense Management Callbacks

@router.callback_query(F.data == "expense_cancel")
async def cancel_expense_flow(callback: CallbackQuery, state: FSMContext):
    """Cancel any ongoing expense edit flow."""
    await state.clear()
    await callback.message.edit_text("❌ Cancelled.")
    await callback.answer()

@router.callback_query(F.data == "expense_back")
async def back_to_expense_list(callback: CallbackQuery):
    """Go back to expense list."""
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user is None:
            await callback.message.edit_text("User not found!")
            await callback.answer()
            return
        
        expenses = session.query(Expense).filter(
            Expense.user_id == callback.from_user.id
        ).order_by(Expense.created_at.desc()).limit(10).all()
        
        if not expenses:
            await callback.message.edit_text("You don't have any expenses yet.")
            await callback.answer()
            return
        
        currency_symbol = CURRENCY_SYMBOLS.get(user.currency, "€") if user.currency else "€"
        
        text = f"{html.bold('📝 Your Recent Expenses:')}\n\n"
        for i, exp in enumerate(expenses, 1):
            if exp.description:
                norm_desc = exp.description.strip().replace("\n", " ")
                desc_text = f" - {html.quote(norm_desc)}"
            else:
                desc_text = ""
            text += f"{i}. {exp.amount:.2f}{currency_symbol} {exp.category.capitalize()}{desc_text}\n"
        
        text += f"\n{html.italic('Select an expense to edit or delete:')}"
        
        await callback.message.edit_text(text, reply_markup=get_expenses_list_keyboard(expenses))
    await callback.answer()

@router.callback_query(F.data.startswith("expense_select:"))
async def select_expense(callback: CallbackQuery):
    """Show details of selected expense with edit/delete options."""
    expense_id = int(callback.data.split(":")[1])
    
    with get_session() as session:
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text("❌ Expense not found or you don't have permission to view it.")
            await callback.answer()
            return
        
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        currency_symbol = CURRENCY_SYMBOLS.get(user.currency, "€") if user and user.currency else "€"
        
        if expense.description:
            norm_desc = expense.description.strip().replace("\n", " ")
            desc_text = f"\n📝 Description: {html.quote(norm_desc)}"
        else:
            desc_text = ""
        
        text = (
            f"{html.bold('💰 Expense Details')}\n\n"
            f"Amount: {expense.amount:.2f} {currency_symbol}\n"
            f"Category: {expense.category.capitalize()}{desc_text}\n"
            f"Date: {expense.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        
        await callback.message.edit_text(text, reply_markup=get_expense_details_keyboard(expense_id))
    await callback.answer()

@router.callback_query(F.data.startswith("expense_edit:"))
async def edit_expense(callback: CallbackQuery):
    """Show menu to choose which field to edit."""
    expense_id = int(callback.data.split(":")[1])
    
    with get_session() as session:
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text("❌ Expense not found or you don't have permission to edit it.")
            await callback.answer()
            return
        
        text = f"{html.bold('✏️ Choose what to edit:')}"
        await callback.message.edit_text(text, reply_markup=get_edit_field_keyboard(expense_id))
    await callback.answer()

@router.callback_query(F.data.startswith("expense_edit_amount:"))
async def edit_amount_start(callback: CallbackQuery, state: FSMContext):
    """Start editing amount - prompt user to enter new value."""
    expense_id = int(callback.data.split(":")[1])
    
    with get_session() as session:
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text("❌ Expense not found.")
            await callback.answer()
            return
        
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        currency_symbol = CURRENCY_SYMBOLS.get(user.currency, "€") if user and user.currency else "€"
        
        text = f"Current amount: {expense.amount:.2f} {currency_symbol}\n\nEnter new amount:"
        await callback.message.edit_text(text)
        await state.set_state(ExpenseEditStates.edit_amount)
        await state.update_data(expense_id=expense_id)
    await callback.answer()

@router.message(ExpenseEditStates.edit_amount)
async def process_edit_amount(message: Message, state: FSMContext):
    """Receive and save the new amount."""
    data = await state.get_data()
    expense_id = data.get("expense_id")
    
    raw_text = message.text or ""
    try:
        new_amount = float(raw_text.replace(",", "."))
    except ValueError:
        await message.answer(f"❌ '{html.quote(raw_text)}' is not a valid number!")
        return
    
    if new_amount <= 0:
        await message.answer("❌ Amount must be positive!")
        return
    
    if new_amount > 1_000_000:
        await message.answer("⚠️ Amount is over 1,000,000!")
        return
    
    with get_session() as session:
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == message.from_user.id
        ).first()
        
        if expense is None:
            await message.answer("❌ Expense not found.")
            await state.clear()
            return
        
        expense.amount = new_amount
        session.commit()
        
        user = session.query(User).filter(User.id == message.from_user.id).first()
        currency_symbol = CURRENCY_SYMBOLS.get(user.currency, "€") if user and user.currency else "€"
    
    await state.clear()
    # Confirm and show updated expense details
    await message.answer(f"✅ Amount updated to {new_amount:.2f} {currency_symbol}")
    with get_session() as session:
        updated = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == message.from_user.id
        ).first()
        if updated:
            if updated.description:
                norm_desc = updated.description.strip().replace("\n", " ")
                desc_text = f"\n📝 Description: {html.quote(norm_desc)}"
            else:
                desc_text = ""
            user = session.query(User).filter(User.id == message.from_user.id).first()
            currency_symbol = CURRENCY_SYMBOLS.get(user.currency, "€") if user and user.currency else "€"
            details = (
                f"{html.bold('💰 Expense Details')}\n\n"
                f"Amount: {updated.amount:.2f} {currency_symbol}\n"
                f"Category: {updated.category.capitalize()}{desc_text}\n"
                f"Date: {updated.created_at.strftime('%d.%m.%Y %H:%M')}"
            )
            await message.answer(details, reply_markup=get_expense_details_keyboard(expense_id))

@router.callback_query(F.data.startswith("expense_edit_category:"))
async def edit_category_start(callback: CallbackQuery, state: FSMContext):
    """Start editing category - show category selection buttons."""
    expense_id = int(callback.data.split(":")[1])
    
    with get_session() as session:
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text("❌ Expense not found.")
            await callback.answer()
            return
        
        text = f"Current category: {expense.category.capitalize()}\n\n{html.bold('Select new category:')}"
        await callback.message.edit_text(text, reply_markup=get_category_keyboard(expense_id))
        await state.set_state(ExpenseEditStates.edit_category)
        await state.update_data(expense_id=expense_id)
    await callback.answer()

@router.callback_query(F.data.startswith("expense_category_select:"))
async def process_category_select(callback: CallbackQuery, state: FSMContext):
    """Receive and save the new category."""
    new_category = callback.data.split(":")[1]
    data = await state.get_data()
    expense_id = data.get("expense_id")
    
    if new_category not in EXPENSE_CATEGORIES:
        await callback.message.edit_text("❌ Invalid category selected.")
        await callback.answer()
        return
    
    with get_session() as session:
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text("❌ Expense not found.")
            await callback.answer()
            await state.clear()
            return
        
        expense.category = new_category
        session.commit()
    
    await state.clear()
    # Confirmation and show updated details
    await callback.message.answer(f"✅ Category updated to {new_category.capitalize()}")
    with get_session() as session:
        updated = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        if updated:
            if updated.description:
                norm_desc = updated.description.strip().replace("\n", " ")
                desc_text = f"\n📝 Description: {html.quote(norm_desc)}"
            else:
                desc_text = ""
            user = session.query(User).filter(User.id == callback.from_user.id).first()
            currency_symbol = CURRENCY_SYMBOLS.get(user.currency, "€") if user and user.currency else "€"
            details = (
                f"{html.bold('💰 Expense Details')}\n\n"
                f"Amount: {updated.amount:.2f} {currency_symbol}\n"
                f"Category: {updated.category.capitalize()}{desc_text}\n"
                f"Date: {updated.created_at.strftime('%d.%m.%Y %H:%M')}"
            )
            # Edit the original message to show details with inline keyboard
            await callback.message.edit_text(details, reply_markup=get_expense_details_keyboard(expense_id))
    await callback.answer()

@router.callback_query(F.data.startswith("expense_edit_description:"))
async def edit_description_start(callback: CallbackQuery, state: FSMContext):
    """Start editing description - prompt user to enter new value."""
    expense_id = int(callback.data.split(":")[1])
    
    with get_session() as session:
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text("❌ Expense not found.")
            await callback.answer()
            return
        
        if expense.description:
            norm_desc = expense.description.strip().replace("\n", " ")
            current_desc = html.quote(norm_desc)
        else:
            current_desc = "(none)"
        text = f"Current description: {current_desc}\n\nEnter new description (or send a new message to replace):"
        await callback.message.edit_text(text, reply_markup=get_description_edit_keyboard(expense_id))
        await state.set_state(ExpenseEditStates.edit_description)
        await state.update_data(expense_id=expense_id)
    await callback.answer()


@router.callback_query(F.data.startswith("expense_clear_description:"))
async def clear_description_callback(callback: CallbackQuery, state: FSMContext):
    """Clear the description of the expense and show updated details."""
    expense_id = int(callback.data.split(":")[1])

    with get_session() as session:
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()

        if expense is None:
            await callback.message.edit_text("❌ Expense not found.")
            await callback.answer()
            return

        expense.description = None
        session.commit()

        # Clear any FSM state related to editing
        await state.clear()

        # Confirmation and show updated details
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        currency_symbol = CURRENCY_SYMBOLS.get(user.currency, "€") if user and user.currency else "€"
        details = (
            f"{html.bold('💰 Expense Details')}\n\n"
            f"Amount: {expense.amount:.2f} {currency_symbol}\n"
            f"Category: {expense.category.capitalize()}\n"
            f"Date: {expense.created_at.strftime('%d.%m.%Y %H:%M')}"
        )

        await callback.message.edit_text("✅ Description cleared")
        await callback.message.answer(details, reply_markup=get_expense_details_keyboard(expense_id))
    await callback.answer()

@router.message(ExpenseEditStates.edit_description)
async def process_edit_description(message: Message, state: FSMContext):
    """Receive and save the new description."""
    data = await state.get_data()
    expense_id = data.get("expense_id")
    
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
            await message.answer("❌ Expense not found.")
            await state.clear()
            return
        
        expense.description = new_description
        session.commit()
    
    await state.clear()
    # Confirmation and show updated details
    if new_description:
        await message.answer(f"✅ Description updated to: {html.quote(new_description)}")
    else:
        await message.answer("✅ Description cleared")

    with get_session() as session:
        updated = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == message.from_user.id
        ).first()
        if updated:
            if updated.description:
                norm_desc = updated.description.strip().replace("\n", " ")
                desc_text = f"\n📝 Description: {html.quote(norm_desc)}"
            else:
                desc_text = ""
            details = (
                f"{html.bold('💰 Expense Details')}\n\n"
                f"Amount: {updated.amount:.2f} {CURRENCY_SYMBOLS.get((session.query(User).filter(User.id == message.from_user.id).first() and session.query(User).filter(User.id == message.from_user.id).first().currency) or 'EUR', '€')}\n"
                f"Category: {updated.category.capitalize()}{desc_text}\n"
                f"Date: {updated.created_at.strftime('%d.%m.%Y %H:%M')}"
            )
            await message.answer(details, reply_markup=get_expense_details_keyboard(expense_id))

@router.callback_query(F.data.startswith("expense_delete:"))
async def delete_expense(callback: CallbackQuery):
    """Show delete confirmation dialog."""
    expense_id = int(callback.data.split(":")[1])
    
    with get_session() as session:
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text("❌ Expense not found or you don't have permission to delete it.")
            await callback.answer()
            return
        
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        currency_symbol = CURRENCY_SYMBOLS.get(user.currency, "€") if user and user.currency else "€"
        
        if expense.description:
            norm_desc = expense.description.strip().replace("\n", " ")
            desc_text = f" - {html.quote(norm_desc)}"
        else:
            desc_text = ""
        text = (
            f"{html.bold('⚠️ Delete this expense?')}\n\n"
            f"{expense.amount:.2f} {currency_symbol} {expense.category.capitalize()}{desc_text}\n\n"
            f"This action cannot be undone."
        )
        
        await callback.message.edit_text(text, reply_markup=get_delete_confirmation_keyboard(expense_id))
    await callback.answer()

@router.callback_query(F.data.startswith("expense_confirm_delete:"))
async def confirm_delete_expense(callback: CallbackQuery):
    """Delete the expense."""
    expense_id = int(callback.data.split(":")[1])
    
    with get_session() as session:
        expense = session.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == callback.from_user.id
        ).first()
        
        if expense is None:
            await callback.message.edit_text("❌ Expense not found.")
            await callback.answer()
            return
        
        amount = expense.amount
        category = expense.category
        
        session.delete(expense)
        session.commit()
    
    await callback.message.edit_text(f"✅ Deleted: {amount:.2f} {category.capitalize()}")
    await callback.answer()
