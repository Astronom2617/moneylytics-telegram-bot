"""Moneylytics — Telegram Mini App backend. Shares the bot's sync SQLAlchemy layer."""

import os
import csv
import io
import hmac
import hashlib
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from urllib.parse import parse_qsl

import jwt
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from sqlalchemy.exc import IntegrityError

load_dotenv()

from databases.db import get_session, init_db
from databases.models import User, Expense


BOT_TOKEN  = os.environ["BOT_TOKEN"]
JWT_SECRET = os.environ.get("JWT_SECRET", BOT_TOKEN + "_webapp")

# Fernet key used to encrypt Monobank personal tokens at rest. MUST be set in
# Heroku config vars (and any deploy env) — without it the Mono endpoints
# return 500. Generate one with:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
MONO_ENCRYPTION_KEY = os.environ.get("MONO_ENCRYPTION_KEY")

MONO_API = "https://api.monobank.ua"
MONO_WEBHOOK_URL = "https://moneylytics-bot-9bebd4a93154.herokuapp.com/api/mono/webhook"

MONO_CURRENCY = {980: "UAH", 978: "EUR", 840: "USD", 826: "GBP"}

# Monobank MCC (merchant category code) → our canonical lowercase category.
_MONO_MCC_GROUPS = {
    "food":          [5411, 5412, 5441, 5451, 5462, 5499, 5812, 5813, 5814],
    "transport":     [4111, 4121, 4131, 4784, 7511, 7512, 7513, 7519],
    "shopping":      [5300, 5310, 5311, 5331, 5399, 5600, 5621, 5631, 5641,
                      5651, 5661, 5691, 5699, 5732, 5734, 5999],
    "health":        [5047, 5122, 5912, 8011, 8021, 8031, 8049, 8062, 8099],
    "entertainment": [7832, 7922, 7929, 7941, 7991, 7993, 7994, 7995, 7999],
    "beauty":        [7230, 7231, 7297],
    "travel":        [3000, 4411, 4511, 4722, 7011, 7012],
    "education":     [8211, 8220, 8241, 8244, 8249, 8299],
    "housing":       [1520, 1711, 1731, 1740, 1750, 1761, 5200, 5211, 5251],
}
MONO_MCC_CATEGORY = {mcc: cat for cat, mccs in _MONO_MCC_GROUPS.items() for mcc in mccs}

# account id → user id, so the webhook avoids a Monobank API call per delivery.
# Monobank rate-limits client-info to once per 60s per token, so this matters.
_mono_account_cache: dict[str, int] = {}

# user id → (set of own IBANs, fetched-at unix ts). Lets the webhook recognise
# the user's own card-to-card / jar transfers and skip them. Refreshed lazily
# once older than an hour to respect Monobank's client-info rate limit.
_mono_iban_cache: dict[int, tuple[set[str], float]] = {}
_MONO_IBAN_TTL = 3600  # seconds


def _get_fernet() -> Fernet:
    if not MONO_ENCRYPTION_KEY:
        raise HTTPException(status_code=500, detail="MONO_ENCRYPTION_KEY not configured")
    return Fernet(MONO_ENCRYPTION_KEY.encode())


def encrypt_token(token: str) -> str:
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()


def _mono_request(path: str, token: str, payload: dict | None = None) -> dict:
    """Call the Monobank personal API. Raises urllib errors on failure.
    The raw token travels only in the X-Token header — never logged."""
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{MONO_API}{path}",
        data=data,
        method="POST" if data is not None else "GET",
        headers={"X-Token": token, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode()
    return json.loads(raw) if raw else {}


def _resolve_mono_user(db: Session, account_id: str):
    """Map a Monobank account id to the owning User. Checks the in-memory
    cache first; on a miss, walks users with a stored token and asks Monobank
    for their accounts, caching every account it sees along the way."""
    cached = _mono_account_cache.get(account_id)
    if cached is not None:
        user = db.query(User).filter(User.id == cached).first()
        if user and user.mono_token:
            return user
        _mono_account_cache.pop(account_id, None)

    users = db.query(User).filter(User.mono_token.isnot(None)).all()
    for user in users:
        try:
            token = decrypt_token(user.mono_token)
            info = _mono_request("/personal/client-info", token)
        except (InvalidToken, urllib.error.URLError, ValueError, OSError):
            continue
        for acc in info.get("accounts", []):
            acc_id = acc.get("id")
            if acc_id:
                _mono_account_cache[acc_id] = user.id
        if _mono_account_cache.get(account_id) == user.id:
            return user
    return None


def _user_own_ibans(user) -> set[str]:
    """The user's own account IBANs, so the webhook can skip self-transfers.
    Cached per user for an hour; on a fetch error we fall back to any stale
    cached set (better than dropping a legit expense)."""
    now = time.time()
    cached = _mono_iban_cache.get(user.id)
    if cached is not None and now - cached[1] < _MONO_IBAN_TTL:
        return cached[0]
    try:
        token = decrypt_token(user.mono_token)
        info = _mono_request("/personal/client-info", token)
    except (InvalidToken, urllib.error.URLError, ValueError, OSError):
        return cached[0] if cached else set()
    ibans = {acc.get("iban") for acc in info.get("accounts", []) if acc.get("iban")}
    _mono_iban_cache[user.id] = (ibans, now)
    return ibans


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
    if body.get("expense_date"):
        try:
            d = datetime.strptime(body["expense_date"], "%Y-%m-%d")
            expense.created_at = d.replace(hour=0, minute=0, second=0, microsecond=0)
            expense.date_edited = True
        except (TypeError, ValueError):
            pass
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
def get_stats(period: str = "week", currency: str | None = None, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
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

    # Distinct currencies in the period — drives the Analytics currency switcher.
    # Computed before the currency filter so the full set stays visible.
    cur_rows = db.query(Expense.currency).filter(
        and_(Expense.user_id == user_id, Expense.created_at >= since)
    ).distinct().all()
    currencies = sorted({row[0] or "EUR" for row in cur_rows})

    cat_q = db.query(
        Expense.category, func.sum(Expense.amount).label("total")
    ).filter(and_(Expense.user_id == user_id, Expense.created_at >= since))
    if currency:
        cat_q = cat_q.filter(Expense.currency == currency)
    by_category = cat_q.group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).all()

    # Last-7-day window. `daily` keeps the legacy single-series shape (honors
    # the `currency` filter) for Analytics; `daily_by_currency` is the per
    # currency breakdown the Dashboard sparkline needs and is intentionally
    # NOT filtered, so its currency switcher always sees every currency.
    week_days = [
        (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        for i in range(6, -1, -1)
    ]
    seven_start = week_days[0]
    seven_end = week_days[-1] + timedelta(days=1)

    daily = []
    for day_start in week_days:
        day_end = day_start + timedelta(days=1)
        day_q = db.query(func.sum(Expense.amount)).filter(
            and_(Expense.user_id == user_id, Expense.created_at >= day_start, Expense.created_at < day_end)
        )
        if currency:
            day_q = day_q.filter(Expense.currency == currency)
        r = day_q.scalar()
        daily.append({"date": day_start.strftime("%Y-%m-%d"), "total": round(r or 0.0, 2)})

    by_cur_rows = db.query(
        func.date(Expense.created_at), Expense.currency, func.sum(Expense.amount)
    ).filter(
        and_(Expense.user_id == user_id,
             Expense.created_at >= seven_start, Expense.created_at < seven_end)
    ).group_by(func.date(Expense.created_at), Expense.currency).all()

    sums = {}
    for day_val, cur, total in by_cur_rows:
        key = day_val if isinstance(day_val, str) else day_val.strftime("%Y-%m-%d")
        sums[(key, cur or "EUR")] = round(float(total or 0.0), 2)
    day_labels = [d.strftime("%Y-%m-%d") for d in week_days]
    daily_by_currency = {
        c: [{"date": d, "total": sums.get((d, c), 0.0)} for d in day_labels]
        for c in {cur for (_, cur) in sums}
    }

    return {
        "today": totals_by_currency_since(today_start),
        "week":  totals_by_currency_since(week_start),
        "month": totals_by_currency_since(month_start),
        "count_today": count_since(today_start),
        "count_week":  count_since(week_start),
        "count_month": count_since(month_start),
        "currencies":  currencies,
        "by_category":  [{"category": row.category, "total": round(row.total, 2)} for row in by_category],
        "daily_last_7": daily,
        "daily_by_currency": daily_by_currency,
    }


@app.get("/api/stats/alltime")
def get_alltime_stats(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    total_count = db.query(func.count(Expense.id)).filter(Expense.user_id == user_id).scalar() or 0
    rows = db.query(Expense.currency, func.sum(Expense.amount)).filter(
        Expense.user_id == user_id
    ).group_by(Expense.currency).all()
    total_by_currency = {(cur or "EUR"): round(float(total or 0.0), 2) for cur, total in rows}
    return {
        "total_count": int(total_count),
        "total_by_currency": total_by_currency,
        "member_since": user.created_at.isoformat() if user.created_at else None,
    }


@app.get("/api/expenses/export")
def export_expenses_csv(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    expenses = db.query(Expense).filter(Expense.user_id == user_id).order_by(Expense.created_at.desc()).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "time", "amount", "currency", "category", "description"])
    for e in expenses:
        writer.writerow([
            e.created_at.strftime("%Y-%m-%d") if e.created_at else "",
            e.created_at.strftime("%H:%M") if e.created_at else "",
            f"{e.amount:.2f}",
            e.currency or "",
            e.category or "",
            e.description or "",
        ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="moneylytics_export.csv"'},
    )


@app.get("/api/user")
def get_user(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    return _user_dict(user)


_KNOWN_CURRENCIES = ("EUR", "USD", "UAH", "GBP")


def _clean_budgets(raw) -> dict:
    """Validate the incoming per-currency budget map. Drops unknown
    currencies, non-positive/invalid limits, and empty currency entries
    so the stored shape stays {cur: {daily?: float, weekly?: float}}."""
    if not isinstance(raw, dict):
        return {}
    clean = {}
    for cur, limits in raw.items():
        if cur not in _KNOWN_CURRENCIES or not isinstance(limits, dict):
            continue
        entry = {}
        for period in ("daily", "weekly"):
            value = limits.get(period)
            if value in (None, ""):
                continue
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue
            if value > 0:
                entry[period] = round(value, 2)
        if entry:
            clean[cur] = entry
    return clean


@app.put("/api/user")
def update_user(body: dict, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    if body.get("currency"):
        user.currency = body["currency"]
    if body.get("language"):
        user.language = body["language"]
    if "budgets" in body:
        user.budgets = _clean_budgets(body["budgets"])
    db.commit()
    return _user_dict(user)


def _user_dict(u):
    return {"id": u.id, "first_name": u.first_name, "username": u.username,
            "currency": u.currency, "language": u.language,
            "budgets": u.budgets or {},
            "created_at": u.created_at.isoformat() if u.created_at else None}

def _expense_dict(e):
    # Mono expenses store a naive UTC timestamp (Monobank's unix `time`), so we
    # tag them with a 'Z' suffix and the frontend's new Date(...) converts them
    # to the viewer's local time. Manually-added expenses already hold the
    # client's local wall-clock, so they stay suffix-free.
    created_at = e.created_at.isoformat()
    if e.mono_tx_id:
        created_at += "Z"
    return {"id": e.id, "amount": e.amount, "category": e.category, "currency": e.currency,
            "description": e.description, "created_at": created_at,
            "date_edited": bool(e.date_edited), "mono_tx_id": e.mono_tx_id,
            "mono_counter_name": e.mono_counter_name}


@app.post("/api/mono/setup")
def mono_setup(body: dict, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    raw_token = (body.get("token") or "").strip()
    if not raw_token:
        raise HTTPException(status_code=400, detail="token required")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)

    # Register the webhook with Monobank using the raw token. Errors here must
    # not leak the token — only a generic message is surfaced or logged.
    try:
        _mono_request("/personal/webhook", raw_token, {"webHookUrl": MONO_WEBHOOK_URL})
    except urllib.error.HTTPError:
        return {"ok": False, "error": "Monobank rejected the token"}
    except (urllib.error.URLError, OSError, ValueError):
        return {"ok": False, "error": "Could not reach Monobank"}

    user.mono_token = encrypt_token(raw_token)
    db.commit()
    return {"ok": True}


@app.delete("/api/mono/setup")
def mono_disconnect(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    user.mono_token = None
    db.commit()
    for acc_id, uid in list(_mono_account_cache.items()):
        if uid == user_id:
            _mono_account_cache.pop(acc_id, None)
    _mono_iban_cache.pop(user_id, None)
    return {"ok": True}


@app.get("/api/mono/status")
def mono_status(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    return {"connected": bool(user.mono_token)}


@app.post("/api/mono/webhook")
def mono_webhook(body: dict, db: Session = Depends(get_db)):
    # Always 200 — Monobank retries any non-200. Every skip/error path below
    # returns a plain dict so FastAPI replies 200.
    try:
        if body.get("type") != "StatementItem":
            return {"status": "ignored"}

        data = body.get("data") or {}
        item = data.get("statementItem") or {}
        amount = item.get("amount")
        tx_id = item.get("id")
        if amount is None or tx_id is None:
            return {"status": "ignored"}
        if amount >= 0:  # income / refund — we only track spending
            return {"status": "skipped"}

        if db.query(Expense.id).filter(Expense.mono_tx_id == str(tx_id)).first():
            return {"status": "duplicate"}

        account_id = data.get("account")
        user = _resolve_mono_user(db, account_id) if account_id else None
        if not user:
            return {"status": "no_user"}

        # Skip the user's own transfers between their accounts/jars — these
        # aren't spending, just money moving around.
        counter_iban = item.get("counterIban")
        if counter_iban and counter_iban in _user_own_ibans(user):
            return {"status": "own_transfer"}

        currency = MONO_CURRENCY.get(item.get("currencyCode"), "UAH")
        category = MONO_MCC_CATEGORY.get(item.get("mcc"), "other")
        # Monobank's `time` is a unix timestamp in UTC — keep it naive UTC.
        created_at = datetime.utcfromtimestamp(item.get("time")) if item.get("time") else datetime.utcnow()
        description = item.get("description") or item.get("comment") or ""
        counter_name = item.get("counterName")

        expense = Expense(
            user_id=user.id,
            amount=abs(amount) / 100,
            category=category,
            currency=currency,
            description=description,
            created_at=created_at,
            mono_tx_id=str(tx_id),
            mono_counter_name=counter_name,
        )
        db.add(expense)
        try:
            db.commit()
        except IntegrityError:
            # Concurrent delivery of the same tx won the unique-index race.
            db.rollback()
            return {"status": "duplicate"}
        return {"status": "ok"}
    except Exception:
        db.rollback()
        return {"status": "error"}


app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")