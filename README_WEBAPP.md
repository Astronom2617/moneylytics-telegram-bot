# Moneylytics — Telegram Mini App

## Архитектура

```
Telegram (фронтенд TMA)
        ↓ HTTPS
FastAPI (webapp.py)   ←→  Postgres (та же БД что у бота)
        ↓
React build (frontend/dist)
```

Aiogram бот живёт отдельно как Heroku worker. Оба процесса используют одну БД.

---

## Локальный запуск

### 1. Backend

```bash
# Из корня репо
pip install -r requirements_webapp.txt

export BOT_TOKEN=<твой токен>
export DATABASE_URL=postgresql+asyncpg://...  # или postgres://... — скрипт сам заменит

uvicorn webapp:app --reload --port 8000
```

API будет доступен на http://localhost:8000/api/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Фронт запустится на http://localhost:5173 и проксирует /api на :8000.

> В dev-режиме авторизация пропускается — показывается mock-пользователь "Dev".
> Это только для localhost, на продакшне проверяется настоящий Telegram initData.

---

## Деплой на Heroku

### Вариант A — два отдельных приложения (рекомендуется)

1. Собери фронтенд:
   ```bash
   cd frontend && npm install && npm run build
   ```
   Папка `frontend/dist` появится в корне репо.

2. Создай новое Heroku приложение:
   ```bash
   heroku create moneylytics-webapp
   ```

3. Задай переменные окружения:
   ```bash
   heroku config:set BOT_TOKEN=<токен>             --app moneylytics-webapp
   heroku config:set DATABASE_URL=<та же БД>       --app moneylytics-webapp
   heroku config:set JWT_SECRET=<любая длинная строка> --app moneylytics-webapp
   ```

4. Добавь buildpack для Python:
   ```bash
   heroku buildpacks:set heroku/python --app moneylytics-webapp
   ```

5. Создай `Procfile` для webapp (или отдельный профиль):
   ```
   web: uvicorn webapp:app --host 0.0.0.0 --port $PORT
   ```

6. Задеплой:
   ```bash
   git push heroku main
   ```

### Вариант B — один dyno, два процесса

Если хочешь запускать бота и webapp на одном dyno, используй `Procfile`:
```
web: uvicorn webapp:app --host 0.0.0.0 --port $PORT
worker: python bot.py
```
> Требует Heroku Eco dyno ($5/мес) чтобы оба процесса работали одновременно.

---

## Настройка Telegram Mini App

1. Зайди в @BotFather → твой бот → **Bot Settings** → **Menu Button**
2. Выбери **Configure menu button**
3. Укажи URL твоего Heroku webapp: `https://moneylytics-webapp.herokuapp.com`
4. Или создай отдельный `/webapp` хендлер в боте с inline кнопкой:

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

@router.message(Command("app"))
async def open_webapp(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="Open Moneylytics",
            web_app=WebAppInfo(url="https://moneylytics-webapp.herokuapp.com")
        )
    ]])
    await message.answer("Tap to open the app:", reply_markup=kb)
```

---

## Переменные окружения

| Переменная    | Обязательная | Описание |
|--------------|------|---------|
| `BOT_TOKEN`  | ✅   | Токен бота из @BotFather |
| `DATABASE_URL` | ✅ | Postgres URL (Heroku даёт автоматически) |
| `JWT_SECRET` | ❌   | Секрет для JWT (дефолт: BOT_TOKEN + "_webapp") |

---

## Структура файлов

```
webapp.py                  ← FastAPI бэкенд
requirements_webapp.txt    ← зависимости для webapp
models.py                  ← твои существующие SQLAlchemy модели (не трогаем)
frontend/
  package.json
  vite.config.js
  index.html
  src/
    App.jsx                ← рутовый компонент, auth, routing
    App.css                ← глобальные стили + Telegram theme vars
    api.js                 ← все HTTP запросы к бэкенду
    hooks/useTelegram.js   ← хук для Telegram WebApp SDK
    pages/
      Dashboard.jsx        ← главный экран: бюджеты + топ категорий
      History.jsx          ← список расходов с фильтрами + удаление
      Analytics.jsx        ← pie chart + bar chart
      Settings.jsx         ← бюджеты, валюта, язык
    components/
      BottomNav.jsx        ← нижняя навигация (4 таба)
      AddExpenseModal.jsx  ← bottom sheet для добавления расхода
```
