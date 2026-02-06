from aiogram import Router, html, F
from aiogram.types import Message

from databases import get_session, Expense

router = Router()

@router.message(F.text == "💰 Budget")
async def button_budget(message: Message):
    await message.answer("💰 Budget management is under development 🚧")
