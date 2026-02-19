from aiogram import Router, html
from aiogram.types import Message

from databases import get_session, Expense, User
from utils.currency import CURRENCY_SYMBOLS

router = Router()

@router.message()
async def add_expenses(message: Message):
    """Parse an incoming message and save a new expense for the user.

    Args:
        message: The incoming Telegram message in the format 'amount category [description]'.
    """
    text = message.text
    parts = text.split()

    if len(parts) < 2:
        await message.answer("You must provide at least an amount and a category")
        return

    try:
        amount = float(parts[0].replace(",", "."))
        category = parts[1].lower().strip()
        description = " ".join(parts[2:]) if len(parts) > 2 else None
    except ValueError:
        await message.answer(f"'{parts[0]}' is not a number!")
        return

    if amount <= 0:
        await message.answer("❌ Amount must be positive!")
        return

    if amount > 1_000_000:
        await message.answer("⚠️ Are you sure? That's over 1,000,000!")
        return

    with get_session() as session:
        new_expense = Expense(user_id=message.from_user.id,
                            amount=amount,
                            category=category,
                            description=description)
        session.add(new_expense)
        session.commit()

        user = session.query(User).filter(User.id == message.from_user.id).first()
        currency_symbol = CURRENCY_SYMBOLS.get(user.currency, "€") if user else "€"
        desc_text = f" ({description.capitalize()})" if description else ""
        await message.answer(html.bold(f"✅ Saved: {amount:.2f}{currency_symbol} — {category}{desc_text}"))