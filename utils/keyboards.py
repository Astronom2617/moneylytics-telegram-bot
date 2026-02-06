from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


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

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Меню настроек"""
    # твой код здесь
    pass

def get_currency_keyboard() -> InlineKeyboardMarkup:
    """Выбор валюты"""
    # твой код здесь
    pass