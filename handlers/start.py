from aiogram import Router, html
from aiogram.filters import CommandStart, Command
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

# Help
@router.message(Command("help"))
async def command_help_handler(message: Message):
    text = f"""
    {html.bold('📖 How to use Moneylytics Bot')}

    {html.bold('Adding expenses:')}
    Send a message in format: {html.bold('amount category description')}
    
    {html.bold('Examples:')}
    - 25 food pizza
    - 90 healthcare dental cleaning
    - 5 coffee (description is optional)

    {html.bold('Available commands:')}
    - /start - Register in the bot
    - /today - Get today's expense report
    - /week - Get weekly expense report
    - /help - Show this instruction

    {html.bold('Tips:')}
    - Amount must be a number
    - Category is required (e.g., food, transport, entertainment)
    - Description is optional but recommended
    
    {html.bold('Categories examples:')}
    food, transport, healthcare, entertainment, shopping, bills, coffee, education, gym, other"""
    await message.answer(text)

