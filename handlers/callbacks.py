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
    now = datetime.now()
    today_start = datetime.combine(now, time.min)
    today_end = datetime.combine(now, time.max)
    week_start = today_start - timedelta(days=now.weekday())
    week_end = today_end
    return today_start, today_end, week_start, week_end


# Callback for choosing setting
@router.callback_query(F.data.startswith("set:"))
async def process_settings_selection(callback: CallbackQuery):
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


@router.callback_query(F.data.startswith("currency_"))
async def process_currency_selection(callback: CallbackQuery):
    currency = callback.data.split("_")[1]
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user is None:
            await callback.message.answer(t(detect_language(callback.from_user.language_code), "common.profile_missing"))
            await callback.answer()
            return

        user.currency = currency
        session.commit()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))

        await callback.message.answer(
            t(lang, "currency.updated", currency=CURRENCY_SYMBOLS.get(currency, currency)),
            reply_markup=get_main_menu(lang)
        )

    await callback.answer()


# Setting Budget
async def set_budget(message: Message, state: FSMContext, field: str, label: str):
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
            Expense.currency == currency,
            Expense.created_at >= today_start,
            Expense.created_at <= today_end
        ).scalar() or 0.0

        weekly_total = session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
            Expense.user_id == callback.from_user.id,
            Expense.currency == currency,
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
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
    await clear_budget(callback, "daily_budget", t(lang, "budget.daily"))

@router.callback_query(F.data == "budget_reset_weekly")
async def process_budget_reset_weekly(callback: CallbackQuery):
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
    await clear_budget(callback, "weekly_budget", t(lang, "budget.weekly"))

@router.callback_query(F.data.startswith("budget_daily"))
async def process_budget_daily(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BudgetStates.waiting_for_daily_budget)
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
    await callback.message.answer(t(lang, "budget.enter_daily"))
    await callback.answer()

@router.message(BudgetStates.waiting_for_daily_budget)
async def process_daily_budget(message: Message, state: FSMContext):
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))
    await set_budget(message, state, "daily_budget", t(lang, "budget.daily"))

@router.callback_query(F.data.startswith("budget_weekly"))
async def process_budget_weekly(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BudgetStates.waiting_for_weekly_budget)
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
    await callback.message.answer(t(lang, "budget.enter_weekly"))
    await callback.answer()

@router.message(BudgetStates.waiting_for_weekly_budget)
async def process_weekly_budget(message: Message, state: FSMContext):
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))
    await set_budget(message, state, "weekly_budget", t(lang, "budget.weekly"))


@router.callback_query(F.data.in_(["lang_en", "lang_ru", "lang_uk"]))
async def process_language_selection(callback: CallbackQuery):
    new_lang = callback.data.split("_")[1]

    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user is None:
            await callback.message.answer(t(detect_language(callback.from_user.language_code), "common.profile_missing"))
            await callback.answer()
            return

        user.language = new_lang
        session.commit()

    await callback.message.edit_text(t(new_lang, "language.updated"))
    await callback.message.answer(
        t(new_lang, "settings.choose"),
        reply_markup=get_main_menu(new_lang)
    )
    await callback.answer()


# Expense Management Callbacks

@router.callback_query(F.data == "expense_cancel")
async def cancel_expense_flow(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        lang = get_user_language(user, detect_language(callback.from_user.language_code))
    await callback.message.edit_text(t(lang, "expense.cancelled"))
    await callback.answer()

@router.callback_query(F.data == "expense_back")
async def back_to_expense_list(callback: CallbackQuery):
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
            await callback.message.edit_text(details, reply_markup=get_expense_details_keyboard(expense_id, lang))
    await callback.answer()

@router.callback_query(F.data.startswith("expense_edit_description:"))
async def edit_description_start(callback: CallbackQuery, state: FSMContext):
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

        await state.clear()

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
    data = await state.get_data()
    expense_id = data.get("expense_id")

    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))

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
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'amount', 'category', 'description', 'created_at', 'currency'])
    for e in expenses:
        desc = e.description.strip().replace('\n', ' ') if e.description else ''
        row_currency = e.currency if e.currency else 'EUR'
        writer.writerow([e.id, f"{e.amount:.2f}", e.category, desc, e.created_at.strftime('%Y-%m-%d %H:%M:%S'), row_currency])
    return output.getvalue().encode('utf-8-sig')


@router.callback_query(F.data == 'export_all')
async def export_all(callback: CallbackQuery):
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user is None:
            await callback.message.answer(t(detect_language(callback.from_user.language_code), "common.profile_missing"))
            await callback.answer()
            return

        lang = get_user_language(user, detect_language(callback.from_user.language_code))
        expenses = session.query(Expense).filter(Expense.user_id == callback.from_user.id).order_by(Expense.created_at.desc()).all()

        if not expenses:
            await callback.message.answer(t(lang, "export.no_all"))
            await callback.answer()
            return

        csv_bytes = build_csv_bytes(expenses)
        bio = BytesIO(csv_bytes)
        bio.seek(0)
        filename = f"expenses_all_{callback.from_user.id}.csv"
        file = BufferedInputFile(bio.read(), filename=filename)
        await callback.message.answer_document(file)
    await callback.answer(t(lang, "export.ready"))


@router.callback_query(F.data == 'export_current_month')
async def export_current_month(callback: CallbackQuery):
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_end = now

    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user is None:
            await callback.message.answer(t(detect_language(callback.from_user.language_code), "common.profile_missing"))
            await callback.answer()
            return

        lang = get_user_language(user, detect_language(callback.from_user.language_code))
        expenses = session.query(Expense).filter(
            Expense.user_id == callback.from_user.id,
            Expense.created_at >= month_start,
            Expense.created_at <= month_end
        ).order_by(Expense.created_at.desc()).all()

        if not expenses:
            await callback.message.answer(t(lang, "export.no_month"))
            await callback.answer()
            return

        csv_bytes = build_csv_bytes(expenses)
        bio = BytesIO(csv_bytes)
        bio.seek(0)
        filename = f"expenses_{now.strftime('%Y_%m')}_{callback.from_user.id}.csv"
        file = BufferedInputFile(bio.read(), filename=filename)
        await callback.message.answer_document(file)

    await callback.answer(t(lang, "export.ready"))