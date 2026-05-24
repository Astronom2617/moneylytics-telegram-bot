from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from os import getenv
from datetime import datetime, timedelta
from sqlalchemy import func

from databases import get_session, User, FeedbackReport
from databases.models import Expense
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
            text=t(lang, "admin.stats_btn"),
            callback_data="admin:stats"
        )],
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
            text=t(lang, "admin.stats_btn"),
            callback_data="admin:stats"
        )],
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


def _collect_stats():
    """Single DB pass for the admin pulse panel. Mirrors the Dataclip query
    so the in-Telegram view stays consistent with the dashboard one."""
    now = datetime.now()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    with get_session() as s:
        # "Reachable" base — excludes users who blocked the bot. Stats below
        # use this so activation/DAU percentages reflect the real audience.
        reachable = s.query(User).filter(User.is_blocked == False)  # noqa: E712
        total_users = reachable.with_entities(func.count(User.id)).scalar() or 0
        new_7d = reachable.with_entities(func.count(User.id)).filter(User.created_at > week_ago).scalar() or 0
        new_24h = reachable.with_entities(func.count(User.id)).filter(User.created_at > day_ago).scalar() or 0
        with_mono = reachable.with_entities(func.count(User.id)).filter(User.mono_token.isnot(None)).scalar() or 0
        blocked = s.query(func.count(User.id)).filter(User.is_blocked == True).scalar() or 0  # noqa: E712
        total_expenses = s.query(func.count(Expense.id)).scalar() or 0
        dau = s.query(func.count(func.distinct(Expense.user_id))).filter(
            Expense.created_at >= today_start
        ).scalar() or 0
        wau = s.query(func.count(func.distinct(Expense.user_id))).filter(
            Expense.created_at >= week_start
        ).scalar() or 0

        # Language breakdown — drives the broadcast audience selector and
        # tells us where engagement actually lives. Reachable only.
        lang_rows = (
            s.query(User.language, func.count(User.id))
            .filter(User.is_blocked == False)  # noqa: E712
            .group_by(User.language)
            .all()
        )
        by_lang = {(row[0] or "en"): int(row[1]) for row in lang_rows}

        # Top spenders by expense count — these are the people whose churn
        # would hurt the most.
        top_rows = (
            s.query(User, func.count(Expense.id).label("cnt"))
            .outerjoin(Expense, Expense.user_id == User.id)
            .group_by(User.id)
            .order_by(func.count(Expense.id).desc())
            .limit(5)
            .all()
        )
        top = []
        for u, cnt in top_rows:
            if not cnt:
                continue
            name = f"@{u.username}" if u.username else (u.first_name or str(u.id))
            top.append((name, int(cnt), bool(u.mono_token)))

        # Activation funnel: of all users, how many made at least one expense.
        active_users = s.query(func.count(func.distinct(Expense.user_id))).scalar() or 0

    return {
        "total_users": total_users,
        "new_7d": new_7d,
        "new_24h": new_24h,
        "with_mono": with_mono,
        "total_expenses": total_expenses,
        "dau": dau,
        "wau": wau,
        "by_lang": by_lang,
        "top": top,
        "active_users": active_users,
        "blocked": blocked,
    }


def _format_stats(s: dict) -> str:
    """Compact monospace-friendly stats card. Activation% surfaced explicitly
    because that's the metric most likely to move with onboarding tweaks."""
    activation = (s["active_users"] / s["total_users"] * 100) if s["total_users"] else 0
    mono_pct = (s["with_mono"] / s["total_users"] * 100) if s["total_users"] else 0
    lines = [
        "📊 <b>Статистика</b>",
        "",
        f"👥 Достижимых юзеров: <b>{s['total_users']}</b>",
        f"   ├ за 24ч: <b>+{s['new_24h']}</b>",
        f"   ├ за 7д:  <b>+{s['new_7d']}</b>",
        f"   └ 🚫 заблокировали: <b>{s['blocked']}</b>",
        "",
        f"🟢 Активны сегодня: <b>{s['dau']}</b>",
        f"🟡 Активны за неделю: <b>{s['wau']}</b>",
        f"💸 Всего расходов: <b>{s['total_expenses']}</b>",
        "",
        f"📈 Активация: <b>{activation:.0f}%</b> ({s['active_users']}/{s['total_users']})",
        f"🏦 С Monobank: <b>{s['with_mono']}</b> ({mono_pct:.0f}%)",
        "",
        "🌐 <b>По языкам:</b> " + " · ".join(
            f"{flag}{n}" for flag, n in zip(
                ["🇷🇺", "🇺🇦", "🇬🇧"],
                [s["by_lang"].get("ru", 0), s["by_lang"].get("uk", 0), s["by_lang"].get("en", 0)],
            )
        ),
    ]
    if s["top"]:
        lines.append("")
        lines.append("🏆 <b>Топ-юзеры:</b>")
        for i, (name, cnt, has_mono) in enumerate(s["top"], 1):
            mono_mark = " 🏦" if has_mono else ""
            lines.append(f"   {i}. {name}{mono_mark} — {cnt}")
    return "\n".join(lines)


@router.callback_query(F.data == "admin:stats")
async def show_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    lang = get_admin_lang()
    stats = _collect_stats()
    text = _format_stats(stats)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 " + t(lang, "admin.refresh"), callback_data="admin:stats")],
        [InlineKeyboardButton(text=t(lang, "admin.back"), callback_data="admin:menu")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        # Telegram errors when edit_text would produce identical content;
        # we still want the user to see they tapped Refresh.
        pass
    await callback.answer()


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


# Audience presets for broadcast. Order matters — drives the button row layout.
# 'self' is a tiny dry-run that targets just the admin so they can sanity-check
# rendering (HTML tags, line breaks, emojis) before blasting everyone.
_BROADCAST_AUDIENCES = {
    "all":  {"label": "📢 Всем",      "filter": None},
    "ru":   {"label": "🇷🇺 RU",      "filter": "ru"},
    "uk":   {"label": "🇺🇦 UK",      "filter": "uk"},
    "en":   {"label": "🇬🇧 EN",      "filter": "en"},
    "self": {"label": "🧪 Себе",     "filter": "_self"},
}


def _audience_user_ids(audience: str) -> list[int]:
    if audience == "self":
        return [ADMIN_ID]
    with get_session() as s:
        # Skip users who blocked the bot — they raised TelegramForbiddenError
        # on a previous send. Saves time and keeps the failed count honest.
        q = s.query(User.id).filter(User.is_blocked == False)  # noqa: E712
        target_lang = _BROADCAST_AUDIENCES.get(audience, {}).get("filter")
        if target_lang and target_lang != "_self":
            q = q.filter(User.language == target_lang)
        return [row[0] for row in q.all()]


def _mark_user_blocked(user_id: int) -> None:
    """Flip the is_blocked flag for a user. Tolerant of missing rows so a
    transient race (user deleted while we're sending) doesn't crash the
    whole broadcast."""
    try:
        with get_session() as s:
            user = s.query(User).filter(User.id == user_id).first()
            if user and not user.is_blocked:
                user.is_blocked = True
                s.commit()
    except Exception:
        pass


@router.message(BroadcastStates.waiting_for_text)
async def broadcast_preview(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    lang = get_admin_lang()
    await state.update_data(broadcast_text=message.text)

    # Show per-audience counts up-front so the admin can compare segment
    # sizes before picking a target. "Себе" always shows 1.
    counts = {key: len(_audience_user_ids(key)) for key in _BROADCAST_AUDIENCES}

    # First row: bulk audiences. Second row: per-language. Third row: test+cancel.
    rows = [
        [InlineKeyboardButton(
            text=f"{_BROADCAST_AUDIENCES['all']['label']} ({counts['all']})",
            callback_data="admin:broadcast_send:all",
        )],
        [
            InlineKeyboardButton(
                text=f"{_BROADCAST_AUDIENCES['ru']['label']} ({counts['ru']})",
                callback_data="admin:broadcast_send:ru",
            ),
            InlineKeyboardButton(
                text=f"{_BROADCAST_AUDIENCES['uk']['label']} ({counts['uk']})",
                callback_data="admin:broadcast_send:uk",
            ),
            InlineKeyboardButton(
                text=f"{_BROADCAST_AUDIENCES['en']['label']} ({counts['en']})",
                callback_data="admin:broadcast_send:en",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_BROADCAST_AUDIENCES['self']['label'],
                callback_data="admin:broadcast_send:self",
            ),
            InlineKeyboardButton(
                text=t(lang, "admin.broadcast_cancel_btn"),
                callback_data="admin:broadcast_cancel",
            ),
        ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    await message.answer(
        t(lang, "admin.broadcast_preview", text=message.text, count=counts["all"]),
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin:broadcast_send:"))
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    lang = get_admin_lang()
    audience = callback.data.split(":")[2]
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    if not text:
        await callback.answer("No text in state", show_alert=True)
        return

    # Self-test keeps the FSM so the admin can iterate; everything else clears.
    if audience != "self":
        await state.clear()

    user_ids = _audience_user_ids(audience)
    sent, failed, blocked = 0, 0, 0
    for user_id in user_ids:
        try:
            await callback.bot.send_message(user_id, text, parse_mode="HTML")
            sent += 1
        except TelegramForbiddenError:
            # User blocked the bot or deleted their account — flag them so
            # we don't keep wasting time on them in future broadcasts.
            _mark_user_blocked(user_id)
            failed += 1
            blocked += 1
        except TelegramBadRequest as e:
            # "chat not found" / "user is deactivated" — also a permanent
            # delivery failure; treat the same as a hard block.
            msg = str(e).lower()
            if any(k in msg for k in ("chat not found", "deactivated", "user is blocked")):
                _mark_user_blocked(user_id)
                blocked += 1
            failed += 1
        except Exception:
            failed += 1

    audience_label = _BROADCAST_AUDIENCES.get(audience, {}).get("label", audience)
    if audience == "self":
        await callback.message.answer(
            f"🧪 Тестовая отправка ({audience_label})\nОтправлено: <b>{sent}</b>",
            parse_mode="HTML",
        )
    else:
        extra = f"\nАудитория: {audience_label}"
        if blocked:
            extra += f"\n🚫 Заблокировали бота: <b>{blocked}</b> (помечены)"
        await callback.message.answer(
            t(lang, "admin.broadcast_done", sent=sent, failed=failed) + extra,
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    lang = get_admin_lang()
    await state.clear()
    await callback.message.answer(t(lang, "admin.broadcast_cancelled"))
    await callback.answer()