from aiogram import Router, html
from aiogram.filters import CommandStart
from aiogram.types import Message
from databases import get_session, User

router = Router()

# Start
@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        if user is None:
            new_user = User(id=message.from_user.id,
                            username=message.from_user.username,
                            first_name=message.from_user.first_name
                            )
            session.add(new_user)
            session.commit()
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")

