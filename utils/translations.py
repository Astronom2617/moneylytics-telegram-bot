from __future__ import annotations

SUPPORTED_LANGUAGES = ("en", "ru", "uk")
DEFAULT_LANGUAGE = "en"
CANONICAL_CATEGORIES = ("food", "transport", "housing", "entertainment", "other")

LANGUAGE_NAMES = {
    "en": "English",
    "ru": "Русский",
    "uk": "Українська",
}

TRANSLATIONS = {
    "en": {
        "menu.today": "📊 Today",
        "menu.week": "📅 Week",
        "menu.categories": "📈 Categories",
        "menu.budget": "💰 Budget",
        "menu.settings": "⚙️ Settings",
        "menu.help": "ℹ️ Help",
        "menu.my_expenses": "📝 My Expenses",
        "menu.export": "📤 Export",
        "menu.placeholder": "Choose an action",
        "category.food": "Food",
        "category.transport": "Transport",
        "category.housing": "Housing",
        "category.entertainment": "Entertainment",
        "category.other": "Other",
        "settings.choose": "Choose your settings:",
        "settings.currency": "Choose your currency 💲",
        "settings.language": "Choose your language 🌐",
        "currency.choose": "Please choose your currency.",
        "currency.updated": "✅ Great! Your currency is set to {currency}.",
        "currency.unknown": "Unknown currency! Supported: {supported}",
        "language.choose": "Choose your language.",
        "language.updated": "✅ Language updated.",
        "start.welcome_back": "Welcome back, {name}!",
        "start.hello": "Hello, {name}! 👋",
        "start.welcome": "Welcome to MoneyLyticsBot!",
        "start.setup": "Let's set up your account.",
        "start.add_expenses_hint": (
            "📖 How to add expenses:\n"
            "Send a message in format:\n"
            "amount category description\n"
            "Example: 500 food pizza"
        ),
        "help.text": (
            "📖 How to use Moneylytics Bot\n\n"
            "Adding expenses:\n"
            "Send a message in format: amount category description\n\n"
            "Examples:\n"
            "- 25 food pizza\n"
            "- 90 housing rent\n"
            "- 5 transport (description is optional)\n\n"
            "Available commands:\n"
            "- /start - Register in the bot\n"
            "- /today - Daily expense report\n"
            "- /week - Weekly expense report\n"
            "- /categories - Expense breakdown with chart\n"
            "- /budget - Manage budget limits\n"
            "- /settings - Account settings\n"
            "- /setcurrency - Set preferred currency\n"
            "- /help - Show this message\n\n"
            "Tips:\n"
            "- Amount must be a number\n"
            "- Category is required (e.g., food, transport, entertainment)\n"
            "- Description is optional but recommended\n\n"
            "Categories examples:\n"
            "food, transport, housing, entertainment, other"
        ),
        "expenses.empty": (
            "You don't have any expenses yet. Start adding expenses with: amount category description"
        ),
        "expenses.title": "📝 Your Recent Expenses:",
        "expenses.select_prompt": "Select an expense to edit or delete:",
        "common.profile_missing": (
            "I couldn't find your profile — please send /start to register."
        ),
        "expense.saved": "✅ Saved: {amount}{currency} — {category}{description}",
        "expenses.choose_currency": "Choose a currency for this expense:",
        "expenses.missing_fields": "You must provide at least an amount and a category",
        "expenses.choose_category_to_save": "Choose a category to save this expense:",
        "expenses.invalid_or_missing_category": "Category is missing or invalid. Please choose one:",
        "expenses.add_cancelled": "Expense was not saved.",
        "expenses.choose_currency_to_save": "Choose a currency for this expense:",
        "expenses.invalid_or_missing_currency": "You have multiple currencies in your history. Which one?:",
        "expenses.invalid_number": "'{value}' is not a number!",
        "expenses.amount_positive": "❌ Amount must be positive!",
        "expenses.amount_too_large": "⚠️ Are you sure? That's over 1,000,000!",
        "budget.choose_option": "Choose your budget option:",
        "budget.daily_button": "📅 Daily budget",
        "budget.weekly_button": "📆 Weekly budget",
        "budget.view_button": "👀 View budgets",
        "budget.reset_daily_button": "♻️ Reset daily",
        "budget.reset_weekly_button": "♻️ Reset weekly",
        "budget.enter_daily": "Enter your daily budget amount:",
        "budget.enter_weekly": "Enter your weekly budget amount:",
        "budget.daily": "Daily budget",
        "budget.weekly": "Weekly budget",
        "budget.set": "{label} set to {amount} {currency} ✅",
        "budget.invalid_number": "'{value}' is not a number!",
        "budget.amount_positive": "❌ Budget must be positive!",
        "budget.cleared": "{label} cleared ✅",
        "budget.not_set": "Not set",
        "budget.overview_title": "💰 Budget overview",
        "budget.daily_limit_label": "📅 Daily limit",
        "budget.spent_today_label": "Spent today",
        "budget.weekly_limit_label": "📆 Weekly limit",
        "budget.spent_week_label": "Spent this week",
        "budget.daily_exceeded": "⚠️ Daily budget exceeded: {total} {currency} / {limit} {currency}",
        "budget.weekly_exceeded": "⚠️ Weekly budget exceeded: {total} {currency} / {limit} {currency}",
        "export.menu_title": "Choose export option:",
        "export.current_month": "Export current month",
        "export.all": "Export all expenses",
        "export.cancelled": "❌ Export cancelled",
        "export.ready": "Export ready ✅",
        "export.no_all": "You don't have any expenses to export.",
        "export.no_month": "You don't have any expenses this month to export.",
        "common.cancel": "❌ Cancel",
        "common.unknown_setting": "Unknown setting",
        "expense.cancelled": "❌ Cancelled.",
        "expense.not_found": "❌ Expense not found.",
        "expense.not_found_permission": "❌ Expense not found or you don't have permission to access it.",
        "expense.details_title": "💰 Expense Details",
        "expense.amount_label": "Amount",
        "expense.category_label": "Category",
        "expense.date_label": "Date",
        "expense.description_label": "📝 Description",
        "expense.choose_edit_field": "✏️ Choose what to edit:",
        "expense.current_amount_prompt": "Current amount: {amount} {currency}\n\nEnter new amount:",
        "expense.invalid_number": "❌ '{value}' is not a valid number!",
        "expense.amount_positive": "❌ Amount must be positive!",
        "expense.amount_too_large": "⚠️ Amount is over 1,000,000!",
        "expense.amount_updated": "✅ Amount updated to {amount} {currency}",
        "expense.current_category_prompt": "Current category: {category}\n\nSelect new category:",
        "expense.invalid_category": "❌ Invalid category selected.",
        "expense.category_updated": "✅ Category updated to {category}",
        "expense.current_description_prompt": "Current description: {description}\n\nEnter new description:",
        "expense.none_label": "(none)",
        "expense.description_updated": "✅ Description updated to: {description}",
        "expense.description_cleared": "✅ Description cleared",
        "expense.delete_title": "⚠️ Delete this expense?",
        "expense.delete_warning": "This action cannot be undone.",
        "expense.deleted": "✅ Deleted: {amount} {category}",
        "keyboard.edit": "✏️ Edit",
        "keyboard.delete": "🗑️ Delete",
        "keyboard.back": "⬅️ Back",
        "keyboard.edit_amount": "💰 Edit Amount",
        "keyboard.edit_category": "🏷️ Edit Category",
        "keyboard.edit_description": "📝 Edit Description",
        "keyboard.confirm_delete": "✅ Yes, delete",
        "keyboard.clear_description": "🗑️ Clear description",
        "reports.no_today": "You don't have any expenses today.",
        "reports.no_week": "You don't have any expenses this week.",
        "reports.no_month": "You don't have any expenses this month.",
        "reports.title_today": "📊 Today's report ({date})",
        "reports.title_week": "📊 Weekly report ({start} - {end})",
        "reports.largest_today": "Largest expense today",
        "reports.largest_week": "Largest expense this week",
        "reports.total_label": "💰 Total: {total} {currency}",
        "reports.totals_by_currency": "💰 Totals by currency:",
        "reports.total_currency_line": "- {total} {currency}",
        "reports.currency_section": "Currency: {currency}",
        "reports.chart_title": "Expenses by Category ({start} - {end})",
        "reports.chart_title_currency": "Expenses by Category ({start} - {end}) - {currency}",
        "reports.chart_caption": "Here is your pie chart by categories for this month ({start} - {end}).",
    },
    "ru": {
        "menu.today": "📊 Сегодня",
        "menu.week": "📅 Неделя",
        "menu.categories": "📈 Категории",
        "menu.budget": "💰 Бюджет",
        "menu.settings": "⚙️ Настройки",
        "menu.help": "ℹ️ Помощь",
        "menu.my_expenses": "📝 Мои расходы",
        "menu.export": "📤 Экспорт",
        "menu.placeholder": "Выберите действие",
        "category.food": "Еда",
        "category.transport": "Транспорт",
        "category.housing": "Жильё",
        "category.entertainment": "Развлечения",
        "category.other": "Другое",
        "settings.choose": "Выберите настройки:",
        "settings.currency": "Выберите валюту 💲",
        "settings.language": "Выберите язык 🌐",
        "currency.choose": "Пожалуйста, выберите валюту.",
        "currency.updated": "✅ Отлично! Ваша валюта установлена: {currency}.",
        "currency.unknown": "Неизвестная валюта! Поддерживаются: {supported}",
        "language.choose": "Выберите язык.",
        "language.updated": "✅ Язык обновлён.",
        "start.welcome_back": "С возвращением, {name}!",
        "start.hello": "Привет, {name}! 👋",
        "start.welcome": "Добро пожаловать в MoneyLyticsBot!",
        "start.setup": "Давайте настроим ваш аккаунт.",
        "start.add_expenses_hint": (
            "📖 Как добавлять расходы:\n"
            "Отправьте сообщение в формате:\n"
            "amount category description\n"
            "Пример: 500 food pizza"
        ),
        "help.text": (
            "📖 Как пользоваться Moneylytics Bot\n\n"
            "Добавление расходов:\n"
            "Отправьте сообщение в формате: amount category description\n\n"
            "Примеры:\n"
            "- 25 food pizza\n"
            "- 90 housing rent\n"
            "- 5 transport (описание необязательно)\n\n"
            "Доступные команды:\n"
            "- /start - Регистрация в боте\n"
            "- /today - Отчёт за день\n"
            "- /week - Отчёт за неделю\n"
            "- /categories - Расходы по категориям с графиком\n"
            "- /budget - Управление лимитами бюджета\n"
            "- /settings - Настройки аккаунта\n"
            "- /setcurrency - Установить валюту\n"
            "- /help - Показать это сообщение\n\n"
            "Советы:\n"
            "- Сумма должна быть числом\n"
            "- Категория обязательна (например: food, transport, entertainment)\n"
            "- Описание необязательно, но рекомендуется\n\n"
            "Примеры категорий:\n"
            "food, transport, housing, entertainment, other"
        ),
        "expenses.empty": (
            "У вас ещё нет расходов. Начните добавлять расходы в формате: amount category description"
        ),
        "expenses.title": "📝 Ваши последние расходы:",
        "expenses.select_prompt": "Выберите расход для редактирования или удаления:",
        "common.profile_missing": (
            "Не удалось найти ваш профиль — отправьте /start, чтобы зарегистрироваться."
        ),
        "expense.saved": "✅ Сохранено: {amount}{currency} — {category}{description}",
        "expenses.choose_currency": "Выберите валюту для этого расхода:",
         "expenses.missing_fields": "Нужно указать как минимум сумму и категорию",
         "expenses.choose_category_to_save": "Выберите категорию, чтобы сохранить этот расход:",
         "expenses.invalid_or_missing_category": "Категория отсутствует или некорректна. Пожалуйста, выберите:",
         "expenses.add_cancelled": "Расход не был сохранён.",
         "expenses.choose_currency_to_save": "Выберите валюту для этого расхода:",
         "expenses.invalid_or_missing_currency": "У вас несколько валют в истории. Какую выбрать?:",
        "expenses.invalid_number": "'{value}' не является числом!",
        "expenses.amount_positive": "❌ Сумма должна быть положительной!",
        "expenses.amount_too_large": "⚠️ Вы уверены? Это больше 1 000 000!",
        "budget.choose_option": "Выберите вариант бюджета:",
        "budget.daily_button": "📅 Дневной бюджет",
        "budget.weekly_button": "📆 Недельный бюджет",
        "budget.view_button": "👀 Просмотр бюджетов",
        "budget.reset_daily_button": "♻️ Сбросить дневной",
        "budget.reset_weekly_button": "♻️ Сбросить недельный",
        "budget.enter_daily": "Введите сумму дневного бюджета:",
        "budget.enter_weekly": "Введите сумму недельного бюджета:",
        "budget.daily": "Дневной бюджет",
        "budget.weekly": "Недельный бюджет",
        "budget.set": "{label} установлен в {amount} {currency} ✅",
        "budget.invalid_number": "'{value}' не является числом!",
        "budget.amount_positive": "❌ Бюджет должен быть положительным!",
        "budget.cleared": "{label} очищен ✅",
        "budget.not_set": "Не задан",
        "budget.overview_title": "💰 Обзор бюджета",
        "budget.daily_limit_label": "📅 Дневной лимит",
        "budget.spent_today_label": "Потрачено сегодня",
        "budget.weekly_limit_label": "📆 Недельный лимит",
        "budget.spent_week_label": "Потрачено за неделю",
        "budget.daily_exceeded": "⚠️ Превышен дневной бюджет: {total} {currency} / {limit} {currency}",
        "budget.weekly_exceeded": "⚠️ Превышен недельный бюджет: {total} {currency} / {limit} {currency}",
        "export.menu_title": "Выберите вариант экспорта:",
        "export.current_month": "Экспорт за текущий месяц",
        "export.all": "Экспорт всех расходов",
        "export.cancelled": "❌ Экспорт отменён",
        "export.ready": "Экспорт готов ✅",
        "export.no_all": "У вас нет расходов для экспорта.",
        "export.no_month": "У вас нет расходов за этот месяц для экспорта.",
        "common.cancel": "❌ Отмена",
        "common.unknown_setting": "Неизвестная настройка",
        "expense.cancelled": "❌ Отменено.",
        "expense.not_found": "❌ Расход не найден.",
        "expense.not_found_permission": "❌ Расход не найден или у вас нет доступа.",
        "expense.details_title": "💰 Детали расхода",
        "expense.amount_label": "Сумма",
        "expense.category_label": "Категория",
        "expense.date_label": "Дата",
        "expense.description_label": "📝 Описание",
        "expense.choose_edit_field": "✏️ Что редактировать?",
        "expense.current_amount_prompt": "Текущая сумма: {amount} {currency}\n\nВведите новую сумму:",
        "expense.invalid_number": "❌ '{value}' не является допустимым числом!",
        "expense.amount_positive": "❌ Сумма должна быть положительной!",
        "expense.amount_too_large": "⚠️ Сумма больше 1 000 000!",
        "expense.amount_updated": "✅ Сумма обновлена до {amount} {currency}",
        "expense.current_category_prompt": "Текущая категория: {category}\n\nВыберите новую категорию:",
        "expense.invalid_category": "❌ Выбрана неверная категория.",
        "expense.category_updated": "✅ Категория обновлена: {category}",
        "expense.current_description_prompt": "Текущее описание: {description}\n\nВведите новое описание:",
        "expense.none_label": "(нет)",
        "expense.description_updated": "✅ Описание обновлено: {description}",
        "expense.description_cleared": "✅ Описание очищено",
        "expense.delete_title": "⚠️ Удалить этот расход?",
        "expense.delete_warning": "Это действие нельзя отменить.",
        "expense.deleted": "✅ Удалено: {amount} {category}",
        "keyboard.edit": "✏️ Редактировать",
        "keyboard.delete": "🗑️ Удалить",
        "keyboard.back": "⬅️ Назад",
        "keyboard.edit_amount": "💰 Изменить сумму",
        "keyboard.edit_category": "🏷️ Изменить категорию",
        "keyboard.edit_description": "📝 Изменить описание",
        "keyboard.confirm_delete": "✅ Да, удалить",
        "keyboard.clear_description": "🗑️ Очистить описание",
        "reports.no_today": "У вас нет расходов за сегодня.",
        "reports.no_week": "У вас нет расходов за эту неделю.",
        "reports.no_month": "У вас нет расходов за этот месяц.",
        "reports.title_today": "📊 Отчёт за сегодня ({date})",
        "reports.title_week": "📊 Отчёт за неделю ({start} - {end})",
        "reports.largest_today": "Самый большой расход сегодня",
        "reports.largest_week": "Самый большой расход на этой неделе",
        "reports.total_label": "💰 Всего: {total} {currency}",
        "reports.totals_by_currency": "💰 Итого по валютам:",
        "reports.total_currency_line": "- {total} {currency}",
        "reports.currency_section": "Валюта: {currency}",
        "reports.chart_title": "Расходы по категориям ({start} - {end})",
        "reports.chart_title_currency": "Расходы по категориям ({start} - {end}) - {currency}",
        "reports.chart_caption": "Вот ваш круговой график по категориям за этот месяц ({start} - {end}).",
    },
    "uk": {
        "menu.today": "📊 Сьогодні",
        "menu.week": "📅 Тиждень",
        "menu.categories": "📈 Категорії",
        "menu.budget": "💰 Бюджет",
        "menu.settings": "⚙️ Налаштування",
        "menu.help": "ℹ️ Довідка",
        "menu.my_expenses": "📝 Мої витрати",
        "menu.export": "📤 Експорт",
        "menu.placeholder": "Оберіть дію",
        "category.food": "Їжа",
        "category.transport": "Транспорт",
        "category.housing": "Житло",
        "category.entertainment": "Розваги",
        "category.other": "Інше",
        "settings.choose": "Оберіть налаштування:",
        "settings.currency": "Оберіть валюту 💲",
        "settings.language": "Оберіть мову 🌐",
        "currency.choose": "Будь ласка, оберіть валюту.",
        "currency.updated": "✅ Чудово! Вашу валюту встановлено: {currency}.",
        "currency.unknown": "Невідома валюта! Підтримуються: {supported}",
        "language.choose": "Оберіть мову.",
        "language.updated": "✅ Мову оновлено.",
        "start.welcome_back": "Ласкаво знову, {name}!",
        "start.hello": "Привіт, {name}! 👋",
        "start.welcome": "Ласкаво просимо до MoneyLyticsBot!",
        "start.setup": "Давайте налаштуємо ваш акаунт.",
        "start.add_expenses_hint": (
            "📖 Як додавати витрати:\n"
            "Надішліть повідомлення у форматі:\n"
            "amount category description\n"
            "Приклад: 500 food pizza"
        ),
        "help.text": (
            "📖 Як користуватися Moneylytics Bot\n\n"
            "Додавання витрат:\n"
            "Надішліть повідомлення у форматі: amount category description\n\n"
            "Приклади:\n"
            "- 25 food pizza\n"
            "- 90 housing rent\n"
            "- 5 transport (опис необов'язковий)\n\n"
            "Доступні команди:\n"
            "- /start - Реєстрація в боті\n"
            "- /today - Звіт за день\n"
            "- /week - Звіт за тиждень\n"
            "- /categories - Розподіл витрат з графіком\n"
            "- /budget - Керування лімітами бюджету\n"
            "- /settings - Налаштування акаунта\n"
            "- /setcurrency - Встановити валюту\n"
            "- /help - Показати це повідомлення\n\n"
            "Поради:\n"
            "- Сума має бути числом\n"
            "- Категорія обов'язкова (наприклад: food, transport, entertainment)\n"
            "- Опис необов'язковий, але бажаний\n\n"
            "Приклади категорій:\n"
            "food, transport, housing, entertainment, other"
        ),
        "expenses.empty": (
            "У вас ще немає витрат. Почніть додавати витрати у форматі: amount category description"
        ),
        "expenses.title": "📝 Ваші останні витрати:",
        "expenses.select_prompt": "Оберіть витрату для редагування або видалення:",
        "common.profile_missing": (
            "Не вдалося знайти ваш профіль — надішліть /start, щоб зареєструватися."
        ),
        "expense.saved": "✅ Збережено: {amount}{currency} — {category}{description}",
        "expenses.choose_currency": "Оберіть валюту для цієї витрати:",
         "expenses.missing_fields": "Потрібно вказати щонайменше суму та категорію",
         "expenses.choose_category_to_save": "Оберіть категорію, щоб зберегти цю витрату:",
         "expenses.invalid_or_missing_category": "Категорія відсутня або некоректна. Будь ласка, оберіть:",
         "expenses.add_cancelled": "Витрату не було збережено.",
         "expenses.choose_currency_to_save": "Оберіть валюту для цієї витрати:",
         "expenses.invalid_or_missing_currency": "У вас кілька валют в історії. Яку обрати?:",
        "expenses.invalid_number": "'{value}' не є числом!",
        "expenses.amount_positive": "❌ Сума має бути додатною!",
        "expenses.amount_too_large": "⚠️ Ви впевнені? Це більше 1 000 000!",
        "budget.choose_option": "Оберіть варіант бюджету:",
        "budget.daily_button": "📅 Денний бюджет",
        "budget.weekly_button": "📆 Тижневий бюджет",
        "budget.view_button": "👀 Перегляд бюджетів",
        "budget.reset_daily_button": "♻️ Скинути денний",
        "budget.reset_weekly_button": "♻️ Скинути тижневий",
        "budget.enter_daily": "Введіть суму денного бюджету:",
        "budget.enter_weekly": "Введіть суму тижневого бюджету:",
        "budget.daily": "Денний бюджет",
        "budget.weekly": "Тижневий бюджет",
        "budget.set": "{label} встановлено в {amount} {currency} ✅",
        "budget.invalid_number": "'{value}' не є числом!",
        "budget.amount_positive": "❌ Бюджет має бути додатним!",
        "budget.cleared": "{label} очищено ✅",
        "budget.not_set": "Не встановлено",
        "budget.overview_title": "💰 Огляд бюджету",
        "budget.daily_limit_label": "📅 Денний ліміт",
        "budget.spent_today_label": "Витрачено сьогодні",
        "budget.weekly_limit_label": "📆 Тижневий ліміт",
        "budget.spent_week_label": "Витрачено за тиждень",
        "budget.daily_exceeded": "⚠️ Перевищено денний бюджет: {total} {currency} / {limit} {currency}",
        "budget.weekly_exceeded": "⚠️ Перевищено тижневий бюджет: {total} {currency} / {limit} {currency}",
        "export.menu_title": "Оберіть варіант експорту:",
        "export.current_month": "Експорт за поточний місяць",
        "export.all": "Експорт усіх витрат",
        "export.cancelled": "❌ Експорт скасовано",
        "export.ready": "Експорт готовий ✅",
        "export.no_all": "У вас немає витрат для експорту.",
        "export.no_month": "У вас немає витрат за цей місяць для експорту.",
        "common.cancel": "❌ Скасувати",
        "common.unknown_setting": "Невідома опція",
        "expense.cancelled": "❌ Скасовано.",
        "expense.not_found": "❌ Витрату не знайдено.",
        "expense.not_found_permission": "❌ Витрату не знайдено або немає доступу.",
        "expense.details_title": "💰 Деталі витрати",
        "expense.amount_label": "Сума",
        "expense.category_label": "Категорія",
        "expense.date_label": "Дата",
        "expense.description_label": "📝 Опис",
        "expense.choose_edit_field": "✏️ Що редагувати?",
        "expense.current_amount_prompt": "Поточна сума: {amount} {currency}\n\nВведіть нову суму:",
        "expense.invalid_number": "❌ '{value}' не є коректним числом!",
        "expense.amount_positive": "❌ Сума має бути додатною!",
        "expense.amount_too_large": "⚠️ Сума більша за 1 000 000!",
        "expense.amount_updated": "✅ Суму оновлено до {amount} {currency}",
        "expense.current_category_prompt": "Поточна категорія: {category}\n\nОберіть нову категорію:",
        "expense.invalid_category": "❌ Обрано неправильну категорію.",
        "expense.category_updated": "✅ Категорію оновлено: {category}",
        "expense.current_description_prompt": "Поточний опис: {description}\n\nВведіть новий опис:",
        "expense.none_label": "(немає)",
        "expense.description_updated": "✅ Опис оновлено: {description}",
        "expense.description_cleared": "✅ Опис очищено",
        "expense.delete_title": "⚠️ Видалити цю витрату?",
        "expense.delete_warning": "Цю дію не можна скасувати.",
        "expense.deleted": "✅ Видалено: {amount} {category}",
        "keyboard.edit": "✏️ Редагувати",
        "keyboard.delete": "🗑️ Видалити",
        "keyboard.back": "⬅️ Назад",
        "keyboard.edit_amount": "💰 Змінити суму",
        "keyboard.edit_category": "🏷️ Змінити категорію",
        "keyboard.edit_description": "📝 Змінити опис",
        "keyboard.confirm_delete": "✅ Так, видалити",
        "keyboard.clear_description": "🗑️ Очистити опис",
        "reports.no_today": "У вас немає витрат за сьогодні.",
        "reports.no_week": "У вас немає витрат за цей тиждень.",
        "reports.no_month": "У вас немає витрат за цей місяць.",
        "reports.title_today": "📊 Звіт за сьогодні ({date})",
        "reports.title_week": "📊 Звіт за тиждень ({start} - {end})",
        "reports.largest_today": "Найбільша витрата сьогодні",
        "reports.largest_week": "Найбільша витрата цього тижня",
        "reports.total_label": "💰 Разом: {total} {currency}",
        "reports.totals_by_currency": "💰 Підсумки за валютами:",
        "reports.total_currency_line": "- {total} {currency}",
        "reports.currency_section": "Валюта: {currency}",
        "reports.chart_title": "Витрати за категоріями ({start} - {end})",
        "reports.chart_title_currency": "Витрати за категоріями ({start} - {end}) - {currency}",
        "reports.chart_caption": "Ось ваша кругова діаграма за категоріями за цей місяць ({start} - {end}).",
    },
}


def normalize_language(language: str | None) -> str:
    if not language:
        return DEFAULT_LANGUAGE

    normalized = language.lower().replace("_", "-").split("-")[0]
    return normalized if normalized in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def detect_language(telegram_language_code: str | None) -> str:
    return normalize_language(telegram_language_code)


def get_user_language(user, fallback: str = DEFAULT_LANGUAGE) -> str:
    user_lang = getattr(user, "language", None)
    return normalize_language(user_lang or fallback)


def t(language: str | None, key: str, **kwargs) -> str:
    lang = normalize_language(language)
    template = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANGUAGE]).get(
        key,
        TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key),
    )
    return template.format(**kwargs)


def text_options(key: str) -> tuple[str, ...]:
    return tuple(TRANSLATIONS[lang][key] for lang in SUPPORTED_LANGUAGES)


def t_category(language: str | None, category: str) -> str:
    safe_category = (category or "").strip().lower()
    if not safe_category:
        return t(language, "category.other")
    key = f"category.{safe_category}"
    translated = t(language, key)
    return translated if translated != key else safe_category.capitalize()


def normalize_category(category: str | None) -> str | None:
    if not category:
        return None
    normalized = category.strip().lower()
    return normalized if normalized else None


def is_canonical_category(category: str | None) -> bool:
    normalized = normalize_category(category)
    return normalized in CANONICAL_CATEGORIES
