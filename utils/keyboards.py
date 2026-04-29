from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Main Menu
def get_main_menu() -> ReplyKeyboardMarkup:
    main_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📊 Today'), KeyboardButton(text='📅 Week')],
            [KeyboardButton(text='📈 Categories'), KeyboardButton(text='💰 Budget')],
            [KeyboardButton(text='⚙️ Settings'), KeyboardButton(text='ℹ️ Help')],
        ],
        resize_keyboard=True,
        input_field_placeholder='Choose an action'
    )
    return main_menu

# Settings Buttons
def get_settings_keyboard() -> InlineKeyboardMarkup:
    settings_menu = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text = 'Choose your currency 💲', callback_data='set:cur'),
                InlineKeyboardButton(text = 'Choose your language 🌐', callback_data='set:lang')
            ]
        ]
    )
    return settings_menu

# Budget Buttons
def get_budget_keyboard() -> InlineKeyboardMarkup:
    budget_menu = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='📅 Daily budget', callback_data='budget_daily'),
                InlineKeyboardButton(text='📆 Weekly budget', callback_data='budget_weekly')
            ],
            [
                InlineKeyboardButton(text='👀 View budgets', callback_data='budget_view')
            ],
            [
                InlineKeyboardButton(text='♻️ Reset daily', callback_data='budget_reset_daily'),
                InlineKeyboardButton(text='♻️ Reset weekly', callback_data='budget_reset_weekly')
            ],
        ]
    )
    return budget_menu

# Currency Buttons
def get_currency_keyboard() -> InlineKeyboardMarkup:
    currency_menu = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='EUR €', callback_data='currency_EUR'),
                InlineKeyboardButton(text='USD $', callback_data='currency_USD'),
            ],
            [
                InlineKeyboardButton(text='UAH ₴', callback_data='currency_UAH'),
                InlineKeyboardButton(text='GBP £', callback_data='currency_GBP'),
            ]
        ]
    )
    return currency_menu
