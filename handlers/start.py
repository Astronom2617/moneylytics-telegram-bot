from aiogram import Router, html, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext

from databases import get_session, User
from utils.keyboards import get_main_menu, get_settings_keyboard, get_currency_keyboard
from handlers.onboarding import start_onboarding
from utils.currency import CURRENCY_MAP
from utils.translations import detect_language, get_user_language, text_options, t

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        if user:
            # Receiving any message means Telegram delivered ours — so if we
            # previously marked them blocked, that flag is stale. Clear it.
            if user.is_blocked:
                user.is_blocked = False
                session.commit()
            lang = get_user_language(user, detect_language(message.from_user.language_code))
            await message.answer(
                t(lang, "start.welcome_back", name=html.bold(message.from_user.full_name)),
                reply_markup=get_main_menu(lang)
            )
        else:
            await start_onboarding(message, state)


@router.message(Command("setcurrency"))
async def command_set_currency_handler(message: Message):
    parts = message.text.split()
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))

    if len(parts) < 2:
        await message.answer(
            t(lang, "currency.choose"),
            reply_markup=get_currency_keyboard()
        )
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


@router.message(Command("help"))
@router.message(F.text.in_(text_options("menu.help")))
async def command_help_handler(message: Message):
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))

    await message.answer(t(lang, "help.text"))


@router.message(Command("app"))
async def command_app_handler(message: Message):
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📊 Open Moneylytics",
            web_app=WebAppInfo(url="https://moneylytics-bot-9bebd4a93154.herokuapp.com")
        )
    ]])
    await message.answer(t(lang, "app.open"), reply_markup=kb)


@router.message(Command("settings"))
@router.message(F.text.in_(text_options("menu.settings")))
async def button_settings(message: Message):
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))

    await message.answer(t(lang, "settings.choose"), reply_markup=get_settings_keyboard(lang))