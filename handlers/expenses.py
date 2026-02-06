from aiogram import Router, html
from aiogram.types import Message

from databases import get_session, Expense

router = Router()

@router.message()
async def add_expenses(message: Message):
    text = message.text
    parts = text.split()

    if len(parts) < 2:
        await message.answer("You must provide at least an amount and a category")
        return

    try:
        amount = float(parts[0])
        category = parts[1]
        description = " ".join(parts[2:]) if len(parts) > 2 else None
    except ValueError:
        await message.answer(f"'{parts[0]}' is not a number!")
        return

    with get_session() as session:
        new_expense = Expense(user_id=message.from_user.id,
                            amount=amount,
                            category=category,
                            description=description)
        session.add(new_expense)
        session.commit()
        await message.answer(f"{html.bold(message.from_user.full_name)}, your expense has been saved!")