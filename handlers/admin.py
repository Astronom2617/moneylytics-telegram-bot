from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from os import getenv

from databases import get_session, User, FeedbackReport
from utils.translations import t, get_user_language

router = Router()
ADMIN_ID = int(getenv("ADMIN_ID", "0"))
PAGE_SIZE = 5


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def get_admin_lang() -> str:
    with get_session() as session:
        admin = session.query(User).filter(User.id == ADMIN_ID).first()
        return get_user_language(admin, "en")


class BroadcastStates(StatesGroup):
    waiting_for_text = State()


@router.message(Command("admin"))
async def admin_menu(message: Message):
    if not is_admin(message.from_user.id):
        return

    lang = get_admin_lang()

    with get_session() as session:
        unread = session.query(FeedbackReport).filter(FeedbackReport.is_read == False).count()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t(lang, "admin.feedbacks_btn", count=unread),
            callback_data="admin:feedbacks:0"
        )],
        [InlineKeyboardButton(
            text=t(lang, "admin.broadcast_btn"),
            callback_data="admin:broadcast"
        )],
    ])
    await message.answer(t(lang, "admin.menu_title"), reply_markup=keyboard)


async def render_admin_menu(callback: CallbackQuery, lang: str):
    with get_session() as session:
        unread = session.query(FeedbackReport).filter(FeedbackReport.is_read == False).count()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t(lang, "admin.feedbacks_btn", count=unread),
            callback_data="admin:feedbacks:0"
        )],
        [InlineKeyboardButton(
            text=t(lang, "admin.broadcast_btn"),
            callback_data="admin:broadcast"
        )],
    ])
    await callback.message.edit_text(t(lang, "admin.menu_title"), reply_markup=keyboard)


@router.callback_query(F.data.startswith("admin:feedbacks:"))
async def show_feedbacks(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    lang = get_admin_lang()
    page = int(callback.data.split(":")[2])
    offset = page * PAGE_SIZE

    with get_session() as session:
        total = session.query(FeedbackReport).count()
        reports = (
            session.query(FeedbackReport)
            .order_by(FeedbackReport.created_at.desc())
            .offset(offset)
            .limit(PAGE_SIZE)
            .all()
        )
        user_ids = [r.user_id for r in reports]
        users = {u.id: u for u in session.query(User).filter(User.id.in_(user_ids)).all()}

    if not reports:
        await callback.answer(t(lang, "admin.no_reports"))
        return

    lines = [t(lang, "admin.feedbacks_title", page=page + 1)]
    for r in reports:
        user = users.get(r.user_id)
        name = f"@{user.username}" if user and user.username else (user.first_name if user else str(r.user_id))
        status = "🔵" if not r.is_read else "⚪️"
        date = r.created_at.strftime("%d.%m %H:%M")
        lines.append(f"{status} <b>{name}</b> · {date}\n<i>{r.text[:80]}{'...' if len(r.text) > 80 else ''}</i>")
        lines.append(f"  └ /fb_{r.id}\n")

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text=t(lang, "admin.prev"), callback_data=f"admin:feedbacks:{page-1}"))
    if offset + PAGE_SIZE < total:
        nav_buttons.append(InlineKeyboardButton(text=t(lang, "admin.next"), callback_data=f"admin:feedbacks:{page+1}"))

    rows = []
    if nav_buttons:
        rows.append(nav_buttons)
    rows.append([InlineKeyboardButton(text=t(lang, "admin.mark_all_read"), callback_data="admin:read_all")])
    rows.append([InlineKeyboardButton(text=t(lang, "admin.back"), callback_data="admin:menu")])

    await callback.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await callback.answer()


@router.message(F.text.regexp(r"^/fb_\d+$"))
async def show_single_feedback(message: Message):
    if not is_admin(message.from_user.id):
        return

    lang = get_admin_lang()
    report_id = int(message.text.split("_")[1])

    with get_session() as session:
        report = session.query(FeedbackReport).filter(FeedbackReport.id == report_id).first()
        if not report:
            await message.answer(t(lang, "admin.report_not_found"))
            return

        user = session.query(User).filter(User.id == report.user_id).first()
        name = f"@{user.username}" if user and user.username else (user.first_name if user else str(report.user_id))
        report.is_read = True
        session.commit()

    date = report.created_at.strftime("%d.%m.%Y %H:%M")
    await message.answer(t(lang, "admin.report_title", id=report.id, name=name, date=date, text=report.text))


@router.callback_query(F.data == "admin:read_all")
async def mark_all_read(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    lang = get_admin_lang()

    with get_session() as session:
        session.query(FeedbackReport).filter(FeedbackReport.is_read == False).update({"is_read": True})
        session.commit()

    await callback.answer(t(lang, "admin.read_all_done"))
    await render_admin_menu(callback, lang)


@router.callback_query(F.data == "admin:menu")
async def back_to_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    lang = get_admin_lang()
    await render_admin_menu(callback, lang)


@router.callback_query(F.data == "admin:broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    lang = get_admin_lang()
    await state.set_state(BroadcastStates.waiting_for_text)
    await callback.message.answer(t(lang, "admin.broadcast_prompt"))
    await callback.answer()


@router.message(BroadcastStates.waiting_for_text, F.text == "/cancel")
async def broadcast_force_cancel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    lang = get_admin_lang()
    await state.clear()
    await message.answer(t(lang, "admin.broadcast_cancelled"))


@router.message(BroadcastStates.waiting_for_text)
async def broadcast_preview(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    lang = get_admin_lang()
    await state.update_data(broadcast_text=message.text)

    with get_session() as session:
        user_count = session.query(User).count()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t(lang, "admin.broadcast_send"), callback_data="admin:broadcast_confirm"),
        InlineKeyboardButton(text=t(lang, "admin.broadcast_cancel_btn"), callback_data="admin:broadcast_cancel"),
    ]])

    await message.answer(
        t(lang, "admin.broadcast_preview", text=message.text, count=user_count),
        reply_markup=keyboard
    )


@router.callback_query(F.data == "admin:broadcast_confirm")
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    lang = get_admin_lang()
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    await state.clear()

    with get_session() as session:
        user_ids = [u.id for u in session.query(User).all()]

    sent, failed = 0, 0
    for user_id in user_ids:
        try:
            await callback.bot.send_message(user_id, text)
            sent += 1
        except Exception:
            failed += 1

    await callback.message.answer(t(lang, "admin.broadcast_done", sent=sent, failed=failed))
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    lang = get_admin_lang()
    await state.clear()
    await callback.message.answer(t(lang, "admin.broadcast_cancelled"))
    await callback.answer()