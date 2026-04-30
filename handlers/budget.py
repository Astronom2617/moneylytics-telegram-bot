from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from databases import get_session, User
from utils.keyboards import get_budget_keyboard
from utils.translations import detect_language, get_user_language, text_options, t

router = Router()

class BudgetStates(StatesGroup):
    waiting_for_daily_budget = State()
    waiting_for_weekly_budget = State()

@router.message(Command("budget"))
@router.message(Command("setbudget"))
@router.message(F.text.in_(text_options("menu.budget")))
async def button_budget(message: Message):
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))

    await message.answer(t(lang, "budget.choose_option"), reply_markup=get_budget_keyboard(lang))

