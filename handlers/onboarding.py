import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction

from databases import get_session, User
from utils.keyboards import get_currency_keyboard, get_language_keyboard, get_main_menu
from utils.translations import t
from utils.currency import CURRENCY_SYMBOLS

router = Router()


# FSM States for onboarding flow
class OnboardingStates(StatesGroup):
    """
    State 1: choosing_language - User selects their preferred language
    State 2: showing_greeting - Bot sends greeting messages with delays
    State 3: choosing_currency - User selects their currency
    """
    choosing_language = State()
    showing_greeting = State()
    choosing_currency = State()


async def start_onboarding(message: Message, state: FSMContext):
    """
    Entry point for onboarding. Shows ONLY language selection.
    No language detection or fallback - user must choose explicitly.
    """
    await state.set_state(OnboardingStates.choosing_language)

    # Send multilingual prompt (no language preference yet)
    await message.answer(
        "🌐 Choose your language 🇺🇸 / Выберите язык 🇷🇺 / Оберіть мову 🇺🇦",
        reply_markup=get_language_keyboard(current_lang=None)
    )


@router.callback_query(OnboardingStates.choosing_language, F.data.in_(["lang_en", "lang_ru", "lang_uk"]))
async def onboarding_language_selected(callback: CallbackQuery, state: FSMContext):
    """
    State 1 → State 2: User selected language
    - Save language to FSM context AND database immediately
    - Move to greeting state
    - ALL subsequent messages use ONLY this selected language
    """
    selected_lang = callback.data.split("_")[1]  # Extract "en", "ru", or "uk"

    # Save language to FSM context for immediate use
    await state.update_data(language=selected_lang)

    # Create or update user in database with selected language
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user is None:
            user = User(
                id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                language=selected_lang,
                currency=None
            )
            session.add(user)
        else:
            user.language = selected_lang
        session.commit()

    # Acknowledge selection and move to greeting
    await callback.answer()
    await callback.message.delete()

    # Move to greeting state
    await state.set_state(OnboardingStates.showing_greeting)
    await send_greeting_messages(callback.message, selected_lang, callback.from_user.first_name, state)


async def send_greeting_messages(message: Message, lang: str, user_name: str, state: FSMContext):
    """
    State 2: Show greeting messages with typing action and delays
    - All messages use the selected language (passed explicitly)
    - Typing action before each message
    - Small delays between messages for better UX
    """
    # Send "typing..." action
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    await asyncio.sleep(0.5)

    # Message 1: Hello
    await message.answer(
        t(lang, 'start.hello', name=user_name)
    )

    await asyncio.sleep(0.7)
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    await asyncio.sleep(0.5)

    # Message 2: Welcome
    await message.answer(
        t(lang, 'start.welcome')
    )

    await asyncio.sleep(0.7)
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    await asyncio.sleep(0.5)

    # Message 3: Setup
    await message.answer(
        t(lang, 'start.setup')
    )

    await asyncio.sleep(0.8)

    # Move to currency selection
    await state.set_state(OnboardingStates.choosing_currency)
    await message.answer(
        t(lang, "currency.choose"),
        reply_markup=get_currency_keyboard()
    )


@router.callback_query(OnboardingStates.choosing_currency, F.data.startswith("currency_"))
async def onboarding_currency_selected(callback: CallbackQuery, state: FSMContext):
    """
    State 3 → Complete: User selected currency
    - Retrieve language from FSM context (NOT from detect_language)
    - Save currency to database
    - Complete onboarding
    - Show main menu in selected language
    """
    currency = callback.data.split("_")[1]

    # Get selected language from FSM context (guaranteed to exist)
    data = await state.get_data()
    lang = data.get("language", "en")  # Fallback to "en" if somehow missing

    # Update user with currency
    with get_session() as session:
        user = session.query(User).filter(User.id == callback.from_user.id).first()
        if user:
            user.currency = currency
            session.commit()

    # Complete onboarding
    await state.clear()

    # Show confirmation message in selected language
    await callback.message.answer(
        t(lang, "currency.updated", currency=CURRENCY_SYMBOLS.get(currency, currency)),
        reply_markup=get_main_menu(lang)
    )

    # Show how to add expenses hint in selected language
    await callback.message.answer(t(lang, "start.add_expenses_hint"))

    await callback.answer()