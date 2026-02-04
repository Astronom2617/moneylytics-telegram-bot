from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from databases.models import Base

DATABASE_URL = 'sqlite:///./moneylytics_bot.db'
engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session() -> Session:
    return SessionLocal()
