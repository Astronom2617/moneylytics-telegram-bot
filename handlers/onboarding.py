from aiogram import Router
from aiogram.types import Message

from databases import get_session, User
from utils.keyboards import get_currency_keyboard
from utils.translations import detect_language, get_user_language, t

router = Router()

async def start_onboarding(message: Message, lang: str = "en"):
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        if user:
            lang = get_user_language(user, detect_language(message.from_user.language_code))

    await message.answer(
        t(lang, 'start.hello', name=message.from_user.first_name) + "\n\n" +
        t(lang, 'start.welcome') + "\n" +
        t(lang, 'start.setup')
    )

    await message.answer(
        t(lang, "currency.choose"),
        reply_markup=get_currency_keyboard()
    )