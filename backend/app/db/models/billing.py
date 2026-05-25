from datetime import datetime, timezone, date
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Date,
    ForeignKey, Text, BigInteger, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    plan = Column(String(20), nullable=False, default="free")  # free | pro | team
    status = Column(String(30), nullable=False, default="active")  # active | past_due | canceled | trialing
    stripe_customer_id = Column(String(100), nullable=True, unique=True, index=True)
    stripe_subscription_id = Column(String(100), nullable=True, unique=True, index=True)
    stripe_price_id = Column(String(100), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="subscription", uselist=False)
    credit_ledger = relationship("CreditLedger", back_populates="subscription", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_subscriptions_user_plan", "user_id", "plan"),
    )


class CreditLedger(Base):
    __tablename__ = "credit_ledger"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=True)
    ledger_date = Column(Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    daily_used = Column(Integer, default=0, nullable=False)
    monthly_used = Column(Integer, default=0, nullable=False)
    daily_limit = Column(Integer, nullable=False, default=25)
    monthly_limit = Column(Integer, nullable=False, default=500)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="credit_ledger")
    subscription = relationship("Subscription", back_populates="credit_ledger")
    usage_events = relationship("CreditUsageEvent", back_populates="ledger", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "ledger_date", name="uq_credit_ledger_user_date"),
        Index("ix_credit_ledger_user_date", "user_id", "ledger_date"),
    )


class CreditUsageEvent(Base):
    __tablename__ = "credit_usage_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ledger_id = Column(Integer, ForeignKey("credit_ledger.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    feature = Column(String(60), nullable=False)  # upload|github_sync|agents|debug|tasks|predict|analysis|roadmap
    credits_used = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="usage_events")
    ledger = relationship("CreditLedger", back_populates="usage_events")

    __table_args__ = (
        Index("ix_usage_events_user_feature", "user_id", "feature"),
    )


class BillingEvent(Base):
    __tablename__ = "billing_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    stripe_event_id = Column(String(100), nullable=False, unique=True, index=True)
    event_type = Column(String(100), nullable=False)
    processed = Column(Boolean, default=False, nullable=False)
    event_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
