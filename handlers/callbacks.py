from aiogram import Router, html, F
from aiogram.types import CallbackQuery, Message

from databases import get_session, User
from utils.keyboards import get_main_menu, get_currency_keyboard
from utils.currency import CURRENCY_SYMBOLS
from aiogram.fsm.context import FSMContext
from handlers.budget import BudgetStates

router = Router()

# Callback for choosing setting
@router.callback_query(F.data.startswith("set:"))
async def process_settings_selection(callback: CallbackQuery):
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

# Setting daily budget
@router.callback_query(F.data.startswith("budget_daily"))
async def process_budget_daily(callback: CallbackQuery, state: F.State.callback_data):
    await state.set_state(BudgetStates.waiting_for_daily_budget)
    await callback.message.answer("Enter your daily budget amount:")
    await callback.answer()

@router.message(BudgetStates.waiting_for_daily_budget)
async def process_daily_budget(message: Message, state: FSMContext):
    text_d = message.text
    limit = 0.0
    try:
        limit = float(text_d.replace(",", "."))
    except ValueError:
        await message.answer(f"'{limit}' is not a number!")
        return

    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        user.daily_budget = limit
        session.commit()

    await state.clear()

    await message.answer(html.bold(f"Daily budget set to {limit} {CURRENCY_SYMBOLS.get(user.currency)} ✅"))

# Setting weekly budget
@router.callback_query(F.data.startswith("budget_weekly"))
async def process_budget_weekly(callback: CallbackQuery, state: F.State.callback_data):
    await state.set_state(BudgetStates.waiting_for_weekly_budget)
    await callback.message.answer("Enter your weekly budget amount:")
    await callback.answer()

@router.message(BudgetStates.waiting_for_weekly_budget)
async def process_weekly_budget(message: Message, state: FSMContext):
    text_w = message.text
    limit = 0.0
    try:
        limit = float(text_w.replace(",", "."))
    except ValueError:
        await message.answer(f"'{limit}' is not a number!")
        return

    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        user.weekly_budget = limit
        session.commit()

    await state.clear()

    await message.answer(html.bold(f"Weekly budget set to {limit} {CURRENCY_SYMBOLS.get(user.currency)} ✅"))



