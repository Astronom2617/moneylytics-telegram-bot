from aiogram import Router, html, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from databases import get_session, User
from utils.keyboards import get_main_menu, get_settings_keyboard
from handlers.onboarding import start_onboarding
from utils.currency import CURRENCY_MAP
from utils.translations import detect_language, get_user_language, text_options, t

router = Router()


# Start
@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Handle the /start command, greeting returning users or starting onboarding.

    Args:
        message: The incoming Telegram message.
    """
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        if user:
            lang = get_user_language(user, detect_language(message.from_user.language_code))
            await message.answer(
                t(lang, "start.welcome_back", name=html.bold(message.from_user.full_name)),
                reply_markup=get_main_menu(lang)
            )
        else:
            await start_onboarding(message, detect_language(message.from_user.language_code))


# Set currency
@router.message(Command("setcurrency"))
async def command_set_currency_handler(message: Message):
    """Handle the /setcurrency command to update the user's preferred currency.

    Args:
        message: The incoming Telegram message containing the currency code.
    """
    parts = message.text.split()
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))

    if len(parts) < 2:
        await message.answer(t(lang, "currency.choose"))
        return

    user_input = parts[1].upper()

    user_currency = CURRENCY_MAP.get(user_input)

    if not user_currency:
        await message.answer(t(lang, "currency.unknown", supported="EUR, USD, UAH, GBP"))
        return

    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()

        if user:
            user.currency = user_currency
            session.commit()

            await message.answer(t(lang, "currency.updated", currency=user_currency))
        else:
            await message.answer(t(lang, "common.profile_missing"))


# Help
@router.message(Command("help"))
@router.message(F.text.in_(text_options("menu.help")))
async def command_help_handler(message: Message):
    """Handle the /help command or the Help button, displaying usage instructions.

    Args:
        message: The incoming Telegram message.
    """
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))

    text = t(lang, "help.text")
    await message.answer(text)


# Settings
@router.message(Command("settings"))
@router.message(F.text.in_(text_options("menu.settings")))
async def button_settings(message: Message):
    """Handle the /settings command or the Settings button, showing the settings menu.

    Args:
        message: The incoming Telegram message.
    """
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))

    await message.answer(t(lang, "settings.choose"), reply_markup=get_settings_keyboard(lang))
