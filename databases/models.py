from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Float, DateTime, Integer, ForeignKey, Date, JSON
from datetime import datetime, date

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    # Per-currency budgets: {"EUR": {"daily": 50.0, "weekly": 200.0}, "USD": {...}}.
    # A currency/period is absent when no limit is set — never stored as 0/null.
    budgets: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    currency: Mapped[str] = mapped_column(String(20), default="EUR", nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    daily_over_limit_count: Mapped[int] = mapped_column(Integer, default=0)
    weekly_over_limit_count: Mapped[int] = mapped_column(Integer, default=0)
    daily_over_limit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    weekly_over_limit_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    def budget_for(self, currency: str | None, period: str) -> float | None:
        """Limit for a currency/period ('daily'|'weekly'), or None if unset."""
        entry = (self.budgets or {}).get(currency or "EUR")
        if not isinstance(entry, dict):
            return None
        value = entry.get(period)
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None
        return value if value > 0 else None

    def set_budget_value(self, currency: str | None, period: str, value) -> None:
        """Set or clear a limit. Falsy/invalid value clears it. Empty
        currencies are pruned so the frontend never renders blank slots.
        Reassigns the dict so SQLAlchemy flags the JSON column dirty."""
        currency = currency or "EUR"
        data = {c: dict(v) for c, v in (self.budgets or {}).items()}
        entry = data.get(currency, {})
        try:
            num = float(value)
        except (TypeError, ValueError):
            num = 0.0
        if num > 0:
            entry[period] = num
        else:
            entry.pop(period, None)
        if entry:
            data[currency] = entry
        else:
            data.pop(currency, None)
        self.budgets = data

    # Backwards-compatible read accessors for the Telegram bot, which still
    # works in a single (the user's main) currency.
    @property
    def daily_budget(self) -> float | None:
        return self.budget_for(self.currency, "daily")

    @property
    def weekly_budget(self) -> float | None:
        return self.budget_for(self.currency, "weekly")

class Expense(Base):
    __tablename__ = 'expenses'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    amount: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(20), default="EUR", nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class FeedbackReport(Base):
    __tablename__ = 'feedback_reports'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    text: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_read: Mapped[bool] = mapped_column(default=False)