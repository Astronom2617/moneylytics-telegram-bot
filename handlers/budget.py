from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from utils.keyboards import get_budget_keyboard

router = Router()

class BudgetStates(StatesGroup):
    waiting_for_daily_budget = State()
    waiting_for_weekly_budget = State()

@router.message(Command("setbudget"))
@router.message(F.text == "💰 Budget")
async def button_budget(message: Message):
    await message.answer("Choose your budget:",
                         reply_markup=get_budget_keyboard()
                         )
