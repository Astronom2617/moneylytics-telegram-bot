from aiogram import Router, html, F
from aiogram.enums import Currency
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from databases import get_session, User
from utils.keyboards import get_main_menu

# CURRENCY DICT
CURRENCY_MAP = {
    "EUR": "EUR",
    "EURO": "EUR",
    "€": "EUR",

    "USD": "USD",
    "DOLLAR": "USD",
    "AMERICAN DOLLAR": "USD",
    "$": "USD",

    "UAH": "UAH",
    "HRYVNIA": "UAH",
    "UKRAINIAN HRYVNIA": "UAH",
    "₴": "UAH",

    "GBP": "GBP",
    "BRITISH POUND": "GBP",
    "POUND": "GBP",
    "£": "GBP",
}

CURRENCY_SYMBOLS = {
    "EUR": "€",
    "USD": "$",
    "UAH": "₴",
    "GBP": "£",
}

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
    await message.answer(
        f"Hello, {html.bold(message.from_user.full_name)}!",
        reply_markup=get_main_menu()
    )

# Set currency
@router.message(Command("setcurrency"))
async def command_set_currency_handler(message: Message):
    parts = message.text.split()

    if len(parts) < 2:
        await message.answer("Usage: /setcurrency EUR")
        return

    user_input = parts[1].upper()

    user_currency = CURRENCY_MAP.get(user_input)

    if not user_currency:
        await message.answer("Unknown currency! Supported: EUR, USD, UAH, GBP")
        return

    with get_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()

        if user:
            user.currency = user_currency
            session.commit()

            await message.answer(f"Successfully set {user_currency} currency!")
        else:
            await message.answer(f"User not found! Use /start first!")

# Help
@router.message(Command("help"))
@router.message(F.text == "ℹ️ Help")
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

# Settings
@router.message(F.text == "⚙️ Settings")
async def button_settings(message: Message):
    await message.answer("⚙️ Settings menu is under development 🚧")

