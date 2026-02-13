from aiogram import Router, html, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from utils.keyboards import get_budget_keyboard

from databases import get_session, User

router = Router()

class BudgetStates(StatesGroup):
    waiting_for_daily_budget = State()
    waiting_for_weekly_budget = State()

@router.message(F.text == "💰 Budget")
async def button_budget(message: Message):
    await message.answer("Choose your budget:",
                         reply_markup=get_budget_keyboard()
                         )
