import os
import json
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from databases.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./moneylytics_bot.db")

# Heroku hands out postgres:// URLs but SQLAlchemy needs the postgresql:// scheme
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def _normalize_legacy_categories(conn):
    # Collapses old free-form/localized categories into the five canonical ones.
    # Idempotent — safe to run on every startup.
    legacy_mappings = {
        'еда': 'food',
        'пища': 'food',
        'пицца': 'food',
        'pizza': 'food',
        
        'транспорт': 'transport',
        'uber': 'transport',
        'bolt': 'transport',
        'taxi': 'transport',
        'bus': 'transport',
        'metro': 'transport',
        'train': 'transport',
        
        'жилье': 'housing',
        'жильё': 'housing',
        'rent': 'housing',
        'water': 'housing',
        'electricity': 'housing',
        'internet': 'housing',
        'ikea': 'housing',
        
        'развлечения': 'entertainment',
        'netflix': 'entertainment',
        'spotify': 'entertainment',
        'cinema': 'entertainment',
        'steam': 'entertainment',
        'bowling': 'entertainment',
        
        'другое': 'other',
    }

    case_conditions = []
    for legacy, canonical in legacy_mappings.items():
        case_conditions.append(f"WHEN LOWER(category) = '{legacy.lower()}' THEN '{canonical}'")
    
    case_statement = '\n    '.join(case_conditions)

    normalize_query = f"""
    UPDATE expenses
    SET category = CASE
        {case_statement}
        WHEN LOWER(category) IN ('food', 'transport', 'housing', 'entertainment', 'other')
            THEN LOWER(category)
        ELSE 'other'
    END
    WHERE category IS NOT NULL
    """
    
    conn.execute(text(normalize_query))

def _migrate_budgets_to_json(conn, columns):
    """Adds the `budgets` JSON column and folds the legacy single-currency
    daily_budget/weekly_budget into it under the user's main currency.
    Idempotent: only seeds rows whose budgets are still empty."""
    is_postgres = engine.dialect.name == "postgresql"
    # The Postgres `json` type has no equality operator, so compare on ::text.
    empty_pred = (
        "budgets IS NULL OR budgets::text = '{}'"
        if is_postgres else
        "budgets IS NULL OR budgets = '' OR budgets = '{}'"
    )

    if "budgets" not in columns:
        conn.execute(text("ALTER TABLE users ADD COLUMN budgets JSON"))

    conn.execute(text(f"UPDATE users SET budgets = '{{}}' WHERE budgets IS NULL"))

    has_legacy = "daily_budget" in columns or "weekly_budget" in columns
    if not has_legacy:
        return

    daily_col = "daily_budget" if "daily_budget" in columns else "NULL AS daily_budget"
    weekly_col = "weekly_budget" if "weekly_budget" in columns else "NULL AS weekly_budget"
    rows = conn.execute(text(
        f"SELECT id, currency, {daily_col}, {weekly_col} FROM users "
        f"WHERE {empty_pred}"
    )).fetchall()

    update_sql = (
        "UPDATE users SET budgets = CAST(:b AS JSON) WHERE id = :id"
        if is_postgres else
        "UPDATE users SET budgets = :b WHERE id = :id"
    )

    for row in rows:
        daily = float(row[2]) if row[2] else None
        weekly = float(row[3]) if row[3] else None
        if not daily and not weekly:
            continue
        entry = {}
        if daily:
            entry["daily"] = daily
        if weekly:
            entry["weekly"] = weekly
        payload = {(row[1] or "EUR"): entry}
        conn.execute(text(update_sql), {"b": json.dumps(payload), "id": row[0]})


def init_db():
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("users")}
        with engine.begin() as conn:
            if "language" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN language VARCHAR(10) DEFAULT 'en'"))
            if "daily_over_limit_date" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN daily_over_limit_date DATE"))
            if "weekly_over_limit_date" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN weekly_over_limit_date DATE"))
            conn.execute(text("UPDATE users SET language = 'en' WHERE language IS NULL OR language = ''"))
            _migrate_budgets_to_json(conn, columns)

    if "expenses" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("expenses")}
        with engine.begin() as conn:
            if "currency" not in columns:
                conn.execute(text("ALTER TABLE expenses ADD COLUMN currency VARCHAR(20) DEFAULT 'EUR'"))
            conn.execute(text(
                """
                UPDATE expenses
                SET currency = COALESCE(
                    (SELECT users.currency FROM users WHERE users.id = expenses.user_id),
                    'EUR'
                )
                WHERE currency IS NULL OR currency = ''
                """
            ))
            _normalize_legacy_categories(conn)

    if "feedback_reports" not in inspector.get_table_names():
        Base.metadata.tables['feedback_reports'].create(bind=engine)

def get_session() -> Session:
    return SessionLocal()
