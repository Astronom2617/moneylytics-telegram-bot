from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from databases.models import Base

DATABASE_URL = 'sqlite:///./moneylytics_bot.db'
engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("users")}
        with engine.begin() as conn:
            if "language" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN language VARCHAR(10) DEFAULT 'en'"))
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

def get_session() -> Session:
    return SessionLocal()
