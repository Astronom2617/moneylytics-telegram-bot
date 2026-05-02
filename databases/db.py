from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from databases.models import Base

DATABASE_URL = 'sqlite:///./moneylytics_bot.db'
engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def _normalize_legacy_categories(conn):
    """
    Normalize legacy non-canonical category values in existing Expense records
    to canonical values: food, transport, housing, entertainment, other.
    Mapping is idempotent and can be run safely multiple times.
    """
    # Legacy -> Canonical category mappings
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

def get_session() -> Session:
    return SessionLocal()
