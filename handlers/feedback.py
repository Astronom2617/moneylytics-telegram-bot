from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from os import getenv

from databases import get_session, User, FeedbackReport
from utils.translations import t, get_user_language, detect_language

router = Router()
ADMIN_ID = int(getenv("ADMIN_ID", "0"))


class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()


@router.message(F.text.in_({"🐛 Feedback", "🐛 Обратная связь", "🐛 Зворотній зв'язок"}))
async def feedback_start(message: Message, state: FSMContext):
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))

    await state.set_state(FeedbackStates.waiting_for_feedback)
    await message.answer(t(lang, "feedback.prompt"))


@router.message(FeedbackStates.waiting_for_feedback)
async def feedback_received(message: Message, state: FSMContext):
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        lang = get_user_language(user, detect_language(message.from_user.language_code))

        report = FeedbackReport(user_id=message.from_user.id, text=message.text)
        session.add(report)
        session.commit()

        unread_count = session.query(FeedbackReport).filter(FeedbackReport.is_read == False).count()

        admin = session.query(User).filter(User.id == ADMIN_ID).first()
        admin_lang = get_user_language(admin, "en")

    await state.clear()
    await message.answer(t(lang, "feedback.thanks"))

    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    await message.bot.send_message(
        ADMIN_ID,
        t(admin_lang, "admin.new_feedback", name=username, text=message.text, count=unread_count)
    )