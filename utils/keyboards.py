from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.translations import CANONICAL_CATEGORIES, LANGUAGE_NAMES, t, t_category


# Main Menu
def get_main_menu(lang: str = "en") -> ReplyKeyboardMarkup:
    main_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, 'menu.today')), KeyboardButton(text=t(lang, 'menu.week'))],
            [KeyboardButton(text=t(lang, 'menu.categories')), KeyboardButton(text=t(lang, 'menu.budget'))],
            [KeyboardButton(text=t(lang, 'menu.settings')), KeyboardButton(text=t(lang, 'menu.help'))],
            [KeyboardButton(text=t(lang, 'menu.my_expenses')), KeyboardButton(text=t(lang, 'menu.export'))],
        ],
        resize_keyboard=True,
        input_field_placeholder=t(lang, 'menu.placeholder')
    )
    return main_menu


# Settings Buttons
def get_settings_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    settings_menu = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, 'settings.currency'), callback_data='set:cur'),
                InlineKeyboardButton(text=t(lang, 'settings.language'), callback_data='set:lang')
            ]
        ]
    )
    return settings_menu


def get_language_keyboard(current_lang: str | None = None) -> InlineKeyboardMarkup:
    """Inline keyboard for selecting a preferred language.
    current_lang=None means onboarding — no checkmarks shown.
    Buttons show: "English 🇺🇸", "Русский 🇷🇺", "Українська 🇺🇦"
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"{'✅ ' if current_lang == 'en' else ''}English 🇺🇸",
                callback_data='lang_en',
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅ ' if current_lang == 'ru' else ''}Русский 🇷🇺",
                callback_data='lang_ru',
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅ ' if current_lang == 'uk' else ''}Українська 🇺🇦",
                callback_data='lang_uk',
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Budget Buttons
def get_budget_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    budget_menu = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, 'budget.daily_button'), callback_data='budget_daily'),
                InlineKeyboardButton(text=t(lang, 'budget.weekly_button'), callback_data='budget_weekly')
            ],
            [
                InlineKeyboardButton(text=t(lang, 'budget.view_button'), callback_data='budget_view')
            ],
            [
                InlineKeyboardButton(text=t(lang, 'budget.reset_daily_button'), callback_data='budget_reset_daily'),
                InlineKeyboardButton(text=t(lang, 'budget.reset_weekly_button'), callback_data='budget_reset_weekly')
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


EXPENSE_CATEGORIES = list(CANONICAL_CATEGORIES)


# Expense Management Keyboards
def get_expenses_list_keyboard(expenses: list, lang: str = "en") -> InlineKeyboardMarkup:
    keyboard = []
    for expense in expenses:
        amount = f"{expense.amount:.2f}"
        category = t_category(lang, expense.category)
        if expense.description:
            desc_clean = expense.description.strip().replace("\n", " ")
            desc_text = f" - {desc_clean[:15]}..." if len(desc_clean) > 15 else f" - {desc_clean}"
        else:
            desc_text = ""
        button_text = f"💰 {amount} {category}{desc_text}"
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"expense_select:{expense.id}"
            )
        ])

    keyboard.append([InlineKeyboardButton(text=t(lang, 'common.cancel'), callback_data="expense_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_expense_details_keyboard(expense_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text=t(lang, "keyboard.edit"), callback_data=f"expense_edit:{expense_id}"),
            InlineKeyboardButton(text=t(lang, "keyboard.delete"), callback_data=f"expense_delete:{expense_id}")
        ],
        [InlineKeyboardButton(text=t(lang, "keyboard.back"), callback_data="expense_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_edit_field_keyboard(expense_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=t(lang, "keyboard.edit_amount"), callback_data=f"expense_edit_amount:{expense_id}")],
        [InlineKeyboardButton(text=t(lang, "keyboard.edit_category"),
                              callback_data=f"expense_edit_category:{expense_id}")],
        [InlineKeyboardButton(text=t(lang, "keyboard.edit_description"),
                              callback_data=f"expense_edit_description:{expense_id}")],
        [InlineKeyboardButton(text=t(lang, "keyboard.back"), callback_data=f"expense_select:{expense_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_category_keyboard(expense_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    keyboard = []
    for i, category in enumerate(EXPENSE_CATEGORIES):
        if i % 2 == 0:
            row = [InlineKeyboardButton(text=t_category(lang, category),
                                        callback_data=f"expense_category_select:{category}")]
            if i + 1 < len(EXPENSE_CATEGORIES):
                row.append(InlineKeyboardButton(text=t_category(lang, EXPENSE_CATEGORIES[i + 1]),
                                                callback_data=f"expense_category_select:{EXPENSE_CATEGORIES[i + 1]}"))
            keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton(text=t(lang, "keyboard.back"), callback_data=f"expense_edit:{expense_id}"),
        InlineKeyboardButton(text=t(lang, "common.cancel"), callback_data="expense_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_pending_expense_category_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    keyboard = []
    for i, category in enumerate(EXPENSE_CATEGORIES):
        if i % 2 == 0:
            row = [InlineKeyboardButton(text=t_category(lang, category),
                                        callback_data=f"pending_expense_category:{category}")]
            if i + 1 < len(EXPENSE_CATEGORIES):
                next_category = EXPENSE_CATEGORIES[i + 1]
                row.append(InlineKeyboardButton(text=t_category(lang, next_category),
                                                callback_data=f"pending_expense_category:{next_category}"))
            keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text=t(lang, "common.cancel"), callback_data="pending_expense_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_pending_expense_currency_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='€ EUR', callback_data='pending_expense_currency:EUR')
    builder.button(text='₴ UAH', callback_data='pending_expense_currency:UAH')
    builder.button(text='$ USD', callback_data='pending_expense_currency:USD')
    builder.button(text='£ GBP', callback_data='pending_expense_currency:GBP')
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text=t(lang, "common.cancel"), callback_data="pending_expense_cancel"))
    return builder.as_markup()


def get_delete_confirmation_keyboard(expense_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text=t(lang, "keyboard.confirm_delete"),
                                 callback_data=f"expense_confirm_delete:{expense_id}"),
            InlineKeyboardButton(text=t(lang, "common.cancel"), callback_data=f"expense_select:{expense_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_description_edit_keyboard(expense_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text=t(lang, "keyboard.clear_description"),
                                 callback_data=f"expense_clear_description:{expense_id}"),
            InlineKeyboardButton(text=t(lang, "common.cancel"), callback_data=f"expense_select:{expense_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_export_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=t(lang, 'export.current_month'), callback_data='export_current_month')],
        [InlineKeyboardButton(text=t(lang, 'export.all'), callback_data='export_all')],
        [InlineKeyboardButton(text=t(lang, 'common.cancel'), callback_data='export_cancel')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)