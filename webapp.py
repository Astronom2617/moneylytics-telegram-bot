"""Moneylytics — Telegram Mini App backend. Shares the bot's sync SQLAlchemy layer."""

import os
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from urllib.parse import parse_qsl

import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

load_dotenv()

from databases.db import get_session, init_db
from databases.models import User, Expense


BOT_TOKEN  = os.environ["BOT_TOKEN"]
JWT_SECRET = os.environ.get("JWT_SECRET", BOT_TOKEN + "_webapp")


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


security = HTTPBearer()

def get_current_user_id(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
        return int(payload["user_id"])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


app = FastAPI(title="Moneylytics API", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()


def _validate_init_data(init_data: str) -> dict:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing hash")
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected   = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise HTTPException(status_code=401, detail="Invalid signature")
    return json.loads(parsed.get("user", "{}"))


@app.post("/api/auth")
def auth_endpoint(body: dict, db: Session = Depends(get_db)):
    init_data = body.get("initData", "")
    if not init_data:
        raise HTTPException(status_code=400, detail="initData required")
    tg_user = _validate_init_data(init_data)
    user_id = tg_user.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="No user in initData")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(
            id=user_id,
            username=tg_user.get("username"),
            first_name=tg_user.get("first_name", "User"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    token = jwt.encode({"user_id": user_id}, JWT_SECRET, algorithm="HS256")
    return {"token": token, "user": _user_dict(user)}


def _period_start(period: str):
    now = datetime.now()
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        return (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return None


@app.get("/api/expenses")
def list_expenses(period: str = "week", user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    q = db.query(Expense).filter(Expense.user_id == user_id)
    since = _period_start(period)
    if since:
        q = q.filter(Expense.created_at >= since)
    return [_expense_dict(e) for e in q.order_by(Expense.created_at.desc()).all()]


@app.post("/api/expenses", status_code=201)
def create_expense(body: dict, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    amount = body.get("amount")
    if not amount or float(amount) <= 0:
        raise HTTPException(status_code=400, detail="amount must be positive")
    user = db.query(User).filter(User.id == user_id).first()
    currency = body.get("currency") or (user.currency if user else "EUR")

    # Store the client's local wall-clock time. Prefer the ready-made local
    # ISO string; otherwise shift utcnow() by timezone_offset, which uses JS
    # getTimezoneOffset() sign convention (UTC+1 is -60).
    created_at = datetime.utcnow()
    client_now = body.get("client_now")
    if client_now:
        try:
            created_at = datetime.fromisoformat(client_now)
        except (TypeError, ValueError):
            client_now = None
    if not client_now:
        tz_offset = body.get("timezone_offset")
        if tz_offset is not None:
            try:
                created_at = created_at - timedelta(minutes=int(tz_offset))
            except (TypeError, ValueError):
                pass

    expense = Expense(
        user_id=user_id,
        amount=float(amount),
        category=body.get("category", "other").lower(),
        currency=currency,
        description=body.get("description"),
        created_at=created_at,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return _expense_dict(expense)


@app.put("/api/expenses/{expense_id}")
def update_expense(
    expense_id: int,
    body: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    expense = db.query(Expense).filter(and_(Expense.id == expense_id, Expense.user_id == user_id)).first()
    if not expense:
        raise HTTPException(status_code=404)
    if "amount" in body:
        amt = float(body["amount"])
        if amt <= 0:
            raise HTTPException(status_code=400, detail="amount must be positive")
        expense.amount = amt
    if "category" in body and body["category"]:
        expense.category = str(body["category"]).lower()
    if "description" in body:
        expense.description = body["description"] or None
    db.commit()
    db.refresh(expense)
    return _expense_dict(expense)


@app.delete("/api/expenses/{expense_id}")
def delete_expense(expense_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(and_(Expense.id == expense_id, Expense.user_id == user_id)).first()
    if not expense:
        raise HTTPException(status_code=404)
    db.delete(expense)
    db.commit()
    return {"ok": True}


@app.get("/api/stats")
def get_stats(period: str = "week", user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start  = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def totals_by_currency_since(dt):
        rows = db.query(Expense.currency, func.sum(Expense.amount)).filter(
            and_(Expense.user_id == user_id, Expense.created_at >= dt)
        ).group_by(Expense.currency).all()
        return {row[0] or "EUR": round(float(row[1] or 0.0), 2) for row in rows}

    def count_since(dt):
        return db.query(func.count(Expense.id)).filter(
            and_(Expense.user_id == user_id, Expense.created_at >= dt)
        ).scalar() or 0

    since = _period_start(period) or month_start
    by_category = db.query(
        Expense.category, func.sum(Expense.amount).label("total")
    ).filter(and_(Expense.user_id == user_id, Expense.created_at >= since)
    ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).all()

    daily = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end   = day_start + timedelta(days=1)
        r = db.query(func.sum(Expense.amount)).filter(
            and_(Expense.user_id == user_id, Expense.created_at >= day_start, Expense.created_at < day_end)
        ).scalar()
        daily.append({"date": day_start.strftime("%Y-%m-%d"), "total": round(r or 0.0, 2)})

    return {
        "today": totals_by_currency_since(today_start),
        "week":  totals_by_currency_since(week_start),
        "month": totals_by_currency_since(month_start),
        "count_today": count_since(today_start),
        "count_week":  count_since(week_start),
        "count_month": count_since(month_start),
        "by_category":  [{"category": row.category, "total": round(row.total, 2)} for row in by_category],
        "daily_last_7": daily,
    }


@app.get("/api/user")
def get_user(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    return _user_dict(user)


@app.put("/api/user")
def update_user(body: dict, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    for field in ("daily_budget", "weekly_budget", "currency", "language"):
        if field in body:
            setattr(user, field, body[field] if body[field] != "" else None)
    db.commit()
    return _user_dict(user)


def _user_dict(u):
    return {"id": u.id, "first_name": u.first_name, "currency": u.currency,
            "language": u.language, "daily_budget": u.daily_budget, "weekly_budget": u.weekly_budget}

def _expense_dict(e):
    return {"id": e.id, "amount": e.amount, "category": e.category, "currency": e.currency,
            "description": e.description, "created_at": e.created_at.isoformat()}


app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")