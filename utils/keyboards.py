from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Main Menu
def get_main_menu() -> ReplyKeyboardMarkup:
    main_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📊 Today'), KeyboardButton(text='📅 Week')],
            [KeyboardButton(text='📈 Categories'), KeyboardButton(text='💰 Budget')],
            [KeyboardButton(text='⚙️ Settings'), KeyboardButton(text='ℹ️ Help')],
            [KeyboardButton(text='📝 My Expenses')],
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

# Expense Categories (fixed list for editing)
EXPENSE_CATEGORIES = ["food", "transport", "housing", "entertainment", "other"]

# Expense Management Keyboards
def get_expenses_list_keyboard(expenses: list) -> InlineKeyboardMarkup:
    """Build keyboard with recent expenses as inline buttons for selection.
    
    Args:
        expenses: List of Expense objects to display.
    
    Returns:
        InlineKeyboardMarkup with expense buttons.
    """
    keyboard = []
    for expense in expenses:
        amount = f"{expense.amount:.2f}"
        category = expense.category.capitalize()
        if expense.description:
            # Strip whitespace and replace line breaks
            desc_clean = expense.description.strip().replace("\n", " ")
            # Truncate and add ... if needed
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
    
    keyboard.append([InlineKeyboardButton(text="❌ Cancel", callback_data="expense_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_expense_details_keyboard(expense_id: int) -> InlineKeyboardMarkup:
    """Build keyboard for expense detail view with edit/delete options.
    
    Args:
        expense_id: ID of the expense.
    
    Returns:
        InlineKeyboardMarkup with edit and delete buttons.
    """
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ Edit", callback_data=f"expense_edit:{expense_id}"),
            InlineKeyboardButton(text="🗑️ Delete", callback_data=f"expense_delete:{expense_id}")
        ],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="expense_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_edit_field_keyboard(expense_id: int) -> InlineKeyboardMarkup:
    """Build keyboard to choose which field to edit.
    
    Args:
        expense_id: ID of the expense.
    
    Returns:
        InlineKeyboardMarkup with field selection buttons.
    """
    keyboard = [
        [InlineKeyboardButton(text="💰 Edit Amount", callback_data=f"expense_edit_amount:{expense_id}")],
        [InlineKeyboardButton(text="🏷️ Edit Category", callback_data=f"expense_edit_category:{expense_id}")],
        [InlineKeyboardButton(text="📝 Edit Description", callback_data=f"expense_edit_description:{expense_id}")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data=f"expense_select:{expense_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_category_keyboard(expense_id: int) -> InlineKeyboardMarkup:
    """Build keyboard with fixed category options for editing.
    
    Args:
        expense_id: ID of the expense being edited.
    
    Returns:
        InlineKeyboardMarkup with category buttons.
    """
    keyboard = []
    for i, category in enumerate(EXPENSE_CATEGORIES):
        if i % 2 == 0:
            row = [InlineKeyboardButton(text=category.capitalize(), callback_data=f"expense_category_select:{category}")]
            if i + 1 < len(EXPENSE_CATEGORIES):
                row.append(InlineKeyboardButton(text=EXPENSE_CATEGORIES[i + 1].capitalize(), callback_data=f"expense_category_select:{EXPENSE_CATEGORIES[i + 1]}"))
            keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Back", callback_data=f"expense_edit:{expense_id}"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="expense_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_delete_confirmation_keyboard(expense_id: int) -> InlineKeyboardMarkup:
    """Build keyboard for delete confirmation.
    
    Args:
        expense_id: ID of the expense to delete.
    
    Returns:
        InlineKeyboardMarkup with confirmation buttons.
    """
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Yes, delete", callback_data=f"expense_confirm_delete:{expense_id}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data=f"expense_select:{expense_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_description_edit_keyboard(expense_id: int) -> InlineKeyboardMarkup:
    """Keyboard for description edit step: clear or cancel (back to details).

    Args:
        expense_id: ID of the expense being edited.

    Returns:
        InlineKeyboardMarkup with Clear and Cancel buttons.
    """
    keyboard = [
        [
            InlineKeyboardButton(text="🗑️ Clear description", callback_data=f"expense_clear_description:{expense_id}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data=f"expense_select:{expense_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

