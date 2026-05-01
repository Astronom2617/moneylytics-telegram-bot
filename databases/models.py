from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Float, DateTime, Integer, ForeignKey, Date
from datetime import datetime, date

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    daily_budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    weekly_budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(20), default="EUR", nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    daily_over_limit_count: Mapped[int] = mapped_column(Integer, default=0)
    weekly_over_limit_count: Mapped[int] = mapped_column(Integer, default=0)
    daily_over_limit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    weekly_over_limit_date: Mapped[date | None] = mapped_column(Date, nullable=True)

class Expense(Base):
    __tablename__ = 'expenses'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    amount: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(20), default="EUR", nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)