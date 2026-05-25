"""
Credit service — tracks daily/monthly AI credit consumption per user.

Credit costs per feature:
  upload      : 10
  github_sync : 5
  agents      : 8
  debug       : 5
  tasks       : 5
  predict     : 5
  analysis    : 5
  roadmap     : 5

Plan daily/monthly limits:
  free : 25 / 500
  pro  : 500 / 15_000
  team : 3_000 / 100_000
"""
from datetime import datetime, timezone, date as date_type
from typing import Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.models.billing import Subscription, CreditLedger, CreditUsageEvent

FEATURE_COSTS: dict[str, int] = {
    "upload": 10,
    "github_sync": 5,
    "agents": 8,
    "debug": 5,
    "tasks": 5,
    "predict": 5,
    "analysis": 5,
    "roadmap": 5,
}

PLAN_LIMITS: dict[str, dict] = {
    "free":  {"daily": 25,    "monthly": 500},
    "pro":   {"daily": 500,   "monthly": 15_000},
    "team":  {"daily": 3_000, "monthly": 100_000},
}


def _get_or_create_subscription(db: Session, user_id: int) -> Subscription:
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if not sub:
        sub = Subscription(user_id=user_id, plan="free", status="active")
        db.add(sub)
        db.flush()
    return sub


def _get_or_create_ledger(db: Session, user_id: int, sub: Subscription) -> CreditLedger:
    today = datetime.now(timezone.utc).date()
    ledger = (
        db.query(CreditLedger)
        .filter(CreditLedger.user_id == user_id, CreditLedger.ledger_date == today)
        .first()
    )
    if not ledger:
        limits = PLAN_LIMITS.get(sub.plan, PLAN_LIMITS["free"])
        # Calculate current month usage for monthly_used carry-over
        current_month_used = _get_monthly_used(db, user_id, today)
        ledger = CreditLedger(
            user_id=user_id,
            subscription_id=sub.id,
            ledger_date=today,
            daily_used=0,
            monthly_used=current_month_used,
            daily_limit=limits["daily"],
            monthly_limit=limits["monthly"],
        )
        db.add(ledger)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            ledger = (
                db.query(CreditLedger)
                .filter(CreditLedger.user_id == user_id, CreditLedger.ledger_date == today)
                .first()
            )
    return ledger


def _get_monthly_used(db: Session, user_id: int, today: date_type) -> int:
    from sqlalchemy import func, extract
    result = (
        db.query(func.sum(CreditLedger.daily_used))
        .filter(
            CreditLedger.user_id == user_id,
            extract("year", CreditLedger.ledger_date) == today.year,
            extract("month", CreditLedger.ledger_date) == today.month,
        )
        .scalar()
    )
    return result or 0


def check_credits(db: Session, user_id: int, feature: str) -> Tuple[bool, str, int]:
    """
    Returns (allowed, reason, credits_needed).
    Does NOT deduct credits.
    """
    cost = FEATURE_COSTS.get(feature, 5)
    sub = _get_or_create_subscription(db, user_id)

    if sub.status not in ("active", "trialing"):
        return False, f"Subscription inactive: {sub.status}", cost

    ledger = _get_or_create_ledger(db, user_id, sub)

    if ledger.daily_used + cost > ledger.daily_limit:
        return False, f"Daily credit limit reached ({ledger.daily_used}/{ledger.daily_limit}). Upgrade to continue.", cost

    if ledger.monthly_used + cost > ledger.monthly_limit:
        return False, f"Monthly credit limit reached ({ledger.monthly_used}/{ledger.monthly_limit}). Upgrade to continue.", cost

    return True, "ok", cost


def deduct_credits(db: Session, user_id: int, feature: str, project_id: int | None = None) -> bool:
    """Deduct credits atomically. Returns True on success."""
    cost = FEATURE_COSTS.get(feature, 5)
    sub = _get_or_create_subscription(db, user_id)
    ledger = _get_or_create_ledger(db, user_id, sub)

    ledger.daily_used += cost
    ledger.monthly_used += cost

    event = CreditUsageEvent(
        user_id=user_id,
        ledger_id=ledger.id,
        project_id=project_id,
        feature=feature,
        credits_used=cost,
    )
    db.add(event)
    db.commit()
    return True


def get_credit_status(db: Session, user_id: int) -> dict:
    """Return current credit status for a user."""
    sub = _get_or_create_subscription(db, user_id)
    db.commit()

    today = datetime.now(timezone.utc).date()
    ledger = _get_or_create_ledger(db, user_id, sub)
    db.commit()

    limits = PLAN_LIMITS.get(sub.plan, PLAN_LIMITS["free"])

    return {
        "plan": sub.plan,
        "subscription_status": sub.status,
        "daily_used": ledger.daily_used,
        "daily_limit": limits["daily"],
        "daily_remaining": max(0, limits["daily"] - ledger.daily_used),
        "monthly_used": ledger.monthly_used,
        "monthly_limit": limits["monthly"],
        "monthly_remaining": max(0, limits["monthly"] - ledger.monthly_used),
        "stripe_customer_id": sub.stripe_customer_id,
        "stripe_subscription_id": sub.stripe_subscription_id,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "cancel_at_period_end": sub.cancel_at_period_end,
        "feature_costs": FEATURE_COSTS,
    }


def get_plan(db: Session, user_id: int) -> str:
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if not sub:
        return "free"
    if sub.status not in ("active", "trialing"):
        return "free"
    return sub.plan


def is_plan_or_higher(db: Session, user_id: int, required_plan: str) -> bool:
    plan_order = {"free": 0, "pro": 1, "team": 2}
    current = get_plan(db, user_id)
    return plan_order.get(current, 0) >= plan_order.get(required_plan, 0)
