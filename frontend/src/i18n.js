const dict = {
  en: {
    // Pages
    'page.dashboard':  'Dashboard',
    'page.history':    'History',
    'page.analytics':  'Analytics',
    'page.settings':   'Settings',

    // Nav
    'nav.home':        'Home',
    'nav.history':     'History',
    'nav.analytics':   'Analytics',
    'nav.settings':    'Settings',

    // Greetings
    'greeting.morning':   'Good morning',
    'greeting.afternoon': 'Good afternoon',
    'greeting.evening':   'Good evening',

    // Periods
    'period.today': 'Today',
    'period.week':  'Week',
    'period.month': 'Month',
    'period.all':   'All',

    // Dashboard
    'dashboard.today':            'TODAY',
    'dashboard.thisWeek':         'THIS WEEK',
    'dashboard.thisMonth':        'THIS MONTH',
    'dashboard.of':               'of',
    'dashboard.left':             'left',
    'dashboard.overBudgetBy':     'Over budget by',
    'dashboard.topCategories':    'Top categories this week',
    'dashboard.transactions':     'transactions',
    'dashboard.transaction':      'transaction',
    'dashboard.thisWeekLower':    'this week',
    'dashboard.motivateNoToday':  "Nothing spent today — great start! 🌱",
    'dashboard.spent':            'Spent',
    'dashboard.lastTx':           'Last transaction',
    'dashboard.add':              'Add',
    'dashboard.noTx':             'No transactions yet',
    'dashboard.streak':           'day streak',
    'dashboard.streakNone':       'Start your streak',

    // History
    'history.transactions':       'transactions',
    'history.noExpenses':         'No expenses',
    'history.yet':                'yet',
    'history.this':               'this',
    'history.today':              'Today',
    'history.yesterday':          'Yesterday',
    'history.details':            'Expense details',
    'history.edit':               'Edit expense',
    'history.dateTime':           'Date & time',
    'history.note':               'Note',
    'history.delete':             'Delete expense',
    'history.deleting':           'Deleting…',
    'history.confirmDelete':      'Delete this expense?',
    'history.save':               'Save changes',
    'history.saving':             'Saving…',
    'history.currencyLocked':     'Currency is locked',

    // Analytics
    'analytics.noData':           'No data for this period',
    'analytics.byCategory':       'By category',
    'analytics.last7Days':        'Last 7 days',
    'analytics.totalsNote':       'Totals shown in your current currency (no conversion)',
    'analytics.currencyNote':     'Independent analytics per currency',

    // Common
    'common.addExpense':          'Add expense',
    'common.newExpense':          'New expense',
    'common.amount':              'Amount',
    'common.category':            'Category',
    'common.noteOptional':        'Note (optional)',
    'common.notePlaceholder':     'e.g. lunch with friends',
    'common.cancel':              'Cancel',
    'common.save':                'Save',

    // Settings
    'settings.budgets':           'Budgets',
    'settings.dailyLimit':        'Daily limit',
    'settings.weeklyLimit':       'Weekly limit',
    'settings.noLimit':           'No limit',
    'settings.currency':          'Currency',
    'settings.language':          'Language',
    'settings.saveChanges':       'Save changes',
    'settings.saving':            'Saving…',
    'settings.saved':             'Saved!',
    'settings.loggedInAs':        'Logged in as',
    'settings.id':                'ID',

    // Profile
    'profile.title':       'Profile',
    'profile.memberSince': 'Member since',
    'profile.transactions':'transactions',
    'profile.totalSpent':  'Total spent',
    'profile.export':      'Export CSV',

    // Categories
    'cat.Food':          'Food',
    'cat.Transport':     'Transport',
    'cat.Shopping':      'Shopping',
    'cat.Entertainment': 'Entertainment',
    'cat.Health':        'Health',
    'cat.Housing':       'Housing',
    'cat.Utilities':     'Utilities',
    'cat.Education':     'Education',
    'cat.Travel':        'Travel',
    'cat.Gifts':         'Gifts',
    'cat.Other':         'Other',
  },

  ru: {
    'page.dashboard':  'Главная',
    'page.history':    'История',
    'page.analytics':  'Аналитика',
    'page.settings':   'Настройки',

    'nav.home':        'Главная',
    'nav.history':     'История',
    'nav.analytics':   'Аналитика',
    'nav.settings':    'Настройки',

    'greeting.morning':   'Доброе утро',
    'greeting.afternoon': 'Добрый день',
    'greeting.evening':   'Добрый вечер',

    'period.today': 'Сегодня',
    'period.week':  'Неделя',
    'period.month': 'Месяц',
    'period.all':   'Всё',

    'dashboard.today':            'СЕГОДНЯ',
    'dashboard.thisWeek':         'ЭТА НЕДЕЛЯ',
    'dashboard.thisMonth':        'ЭТОТ МЕСЯЦ',
    'dashboard.of':               'из',
    'dashboard.left':             'осталось',
    'dashboard.overBudgetBy':     'Превышение на',
    'dashboard.topCategories':    'Топ категорий за неделю',
    'dashboard.transactions':     'операций',
    'dashboard.transaction':      'операция',
    'dashboard.thisWeekLower':    'за неделю',
    'dashboard.motivateNoToday':  'Сегодня ноль трат — отличное начало! 🌱',
    'dashboard.spent':            'Потрачено',
    'dashboard.lastTx':           'Последняя операция',
    'dashboard.add':              'Добавить',
    'dashboard.noTx':             'Операций пока нет',
    'dashboard.streak':           'дней подряд',
    'dashboard.streakNone':       'Начни серию',

    'history.transactions':       'операций',
    'history.noExpenses':         'Нет расходов',
    'history.yet':                'пока',
    'history.this':               'за',
    'history.today':              'Сегодня',
    'history.yesterday':          'Вчера',
    'history.details':            'Детали расхода',
    'history.edit':               'Редактировать',
    'history.dateTime':           'Дата и время',
    'history.note':               'Заметка',
    'history.delete':             'Удалить расход',
    'history.deleting':           'Удаление…',
    'history.confirmDelete':      'Удалить этот расход?',
    'history.save':               'Сохранить',
    'history.saving':             'Сохранение…',
    'history.currencyLocked':     'Валюта зафиксирована',

    'analytics.noData':           'Нет данных за этот период',
    'analytics.byCategory':       'По категориям',
    'analytics.last7Days':        'Последние 7 дней',
    'analytics.totalsNote':       'Суммы показаны в вашей текущей валюте (без конвертации)',
    'analytics.currencyNote':     'Отдельная аналитика по каждой валюте',

    'common.addExpense':          'Добавить расход',
    'common.newExpense':          'Новый расход',
    'common.amount':              'Сумма',
    'common.category':            'Категория',
    'common.noteOptional':        'Заметка (необязательно)',
    'common.notePlaceholder':     'напр. обед с друзьями',
    'common.cancel':              'Отмена',
    'common.save':                'Сохранить',

    'settings.budgets':           'Бюджеты',
    'settings.dailyLimit':        'Дневной лимит',
    'settings.weeklyLimit':       'Недельный лимит',
    'settings.noLimit':           'Без лимита',
    'settings.currency':          'Валюта',
    'settings.language':          'Язык',
    'settings.saveChanges':       'Сохранить',
    'settings.saving':            'Сохранение…',
    'settings.saved':             'Сохранено!',
    'settings.loggedInAs':        'Вы вошли как',
    'settings.id':                'ID',

    'profile.title':       'Профиль',
    'profile.memberSince': 'С нами с',
    'profile.transactions':'операций',
    'profile.totalSpent':  'Всего потрачено',
    'profile.export':      'Экспорт в CSV',

    'cat.Food':          'Еда',
    'cat.Transport':     'Транспорт',
    'cat.Shopping':      'Покупки',
    'cat.Entertainment': 'Развлечения',
    'cat.Health':        'Здоровье',
    'cat.Housing':       'Жильё',
    'cat.Utilities':     'Услуги',
    'cat.Education':     'Образование',
    'cat.Travel':        'Путешествия',
    'cat.Gifts':         'Подарки',
    'cat.Other':         'Прочее',
  },

  uk: {
    'page.dashboard':  'Головна',
    'page.history':    'Історія',
    'page.analytics':  'Аналітика',
    'page.settings':   'Налаштування',

    'nav.home':        'Головна',
    'nav.history':     'Історія',
    'nav.analytics':   'Аналітика',
    'nav.settings':    'Налаштування',

    'greeting.morning':   'Доброго ранку',
    'greeting.afternoon': 'Доброго дня',
    'greeting.evening':   'Доброго вечора',

    'period.today': 'Сьогодні',
    'period.week':  'Тиждень',
    'period.month': 'Місяць',
    'period.all':   'Усі',

    'dashboard.today':            'СЬОГОДНІ',
    'dashboard.thisWeek':         'ЦЕЙ ТИЖДЕНЬ',
    'dashboard.thisMonth':        'ЦЕЙ МІСЯЦЬ',
    'dashboard.of':               'з',
    'dashboard.left':             'залишилось',
    'dashboard.overBudgetBy':     'Перевищення на',
    'dashboard.topCategories':    'Топ категорій за тиждень',
    'dashboard.transactions':     'операцій',
    'dashboard.transaction':      'операція',
    'dashboard.thisWeekLower':    'за тиждень',
    'dashboard.motivateNoToday':  'Сьогодні нуль витрат — чудовий початок! 🌱',
    'dashboard.spent':            'Витрачено',
    'dashboard.lastTx':           'Остання операція',
    'dashboard.add':              'Додати',
    'dashboard.noTx':             'Операцій поки немає',
    'dashboard.streak':           'днів поспіль',
    'dashboard.streakNone':       'Почни серію',

    'history.transactions':       'операцій',
    'history.noExpenses':         'Немає витрат',
    'history.yet':                'поки що',
    'history.this':               'за',
    'history.today':              'Сьогодні',
    'history.yesterday':          'Вчора',
    'history.details':            'Деталі витрати',
    'history.edit':               'Редагувати',
    'history.dateTime':           'Дата і час',
    'history.note':               'Нотатка',
    'history.delete':             'Видалити витрату',
    'history.deleting':           'Видалення…',
    'history.confirmDelete':      'Видалити цю витрату?',
    'history.save':               'Зберегти',
    'history.saving':             'Збереження…',
    'history.currencyLocked':     'Валюта зафіксована',

    'analytics.noData':           'Немає даних за цей період',
    'analytics.byCategory':       'За категоріями',
    'analytics.last7Days':        'Останні 7 днів',
    'analytics.totalsNote':       'Суми показані у вашій поточній валюті (без конвертації)',
    'analytics.currencyNote':     'Окрема аналітика для кожної валюти',

    'common.addExpense':          'Додати витрату',
    'common.newExpense':          'Нова витрата',
    'common.amount':              'Сума',
    'common.category':            'Категорія',
    'common.noteOptional':        'Нотатка (необов’язково)',
    'common.notePlaceholder':     'напр. обід з друзями',
    'common.cancel':              'Скасувати',
    'common.save':                'Зберегти',

    'settings.budgets':           'Бюджети',
    'settings.dailyLimit':        'Денний ліміт',
    'settings.weeklyLimit':       'Тижневий ліміт',
    'settings.noLimit':           'Без ліміту',
    'settings.currency':          'Валюта',
    'settings.language':          'Мова',
    'settings.saveChanges':       'Зберегти',
    'settings.saving':            'Збереження…',
    'settings.saved':             'Збережено!',
    'settings.loggedInAs':        'Ви увійшли як',
    'settings.id':                'ID',

    'profile.title':       'Профіль',
    'profile.memberSince': 'З нами з',
    'profile.transactions':'операцій',
    'profile.totalSpent':  'Усього витрачено',
    'profile.export':      'Експорт у CSV',

    'cat.Food':          'Їжа',
    'cat.Transport':     'Транспорт',
    'cat.Shopping':      'Покупки',
    'cat.Entertainment': 'Розваги',
    'cat.Health':        'Здоров’я',
    'cat.Housing':       'Житло',
    'cat.Utilities':     'Послуги',
    'cat.Education':     'Освіта',
    'cat.Travel':        'Подорожі',
    'cat.Gifts':         'Подарунки',
    'cat.Other':         'Інше',
  },
}

export function useTranslation(language) {
  const lang = dict[language] ? language : 'en'
  return (key) => dict[lang][key] ?? dict.en[key] ?? key
}

export function localeFor(language) {
  switch (language) {
    case 'ru': return 'ru-RU'
    case 'uk': return 'uk-UA'
    default:   return 'en-GB'
  }
}

export function translateCategory(category, language) {
  const lang = dict[language] ? language : 'en'
  const cap = category.charAt(0).toUpperCase() + category.slice(1).toLowerCase()
  return dict[lang][`cat.${cap}`] ?? dict.en[`cat.${cap}`] ?? cap
}
