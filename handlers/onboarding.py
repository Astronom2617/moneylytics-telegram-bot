from aiogram import Router
from aiogram.types import Message

from utils.keyboards import get_currency_keyboard

router = Router()

async def start_onboarding(message: Message):
    await message.answer(
        f"Hello, {message.from_user.first_name}! 👋\n\n"
        "Welcome to MoneyLyticsBot!\n"
        "Let's set up your account."
    )

    await message.answer(
        "Please choose your currency.",
        reply_markup=get_currency_keyboard()
    )