"""
Stripe integration service.

Uses stripe Python SDK with STRIPE_SECRET_KEY from environment.
Webhook signature validation prevents replay attacks.
"""
import json
import stripe
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.models.billing import Subscription, BillingEvent
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Lazily initialize stripe — only fails at call time if key missing
def _stripe():
    if not settings.STRIPE_SECRET_KEY:
        raise RuntimeError("STRIPE_SECRET_KEY not configured. Set it in environment variables.")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


PLAN_PRICE_IDS: dict[str, Optional[str]] = {
    "pro":  settings.STRIPE_PRO_PRICE_ID  if hasattr(settings, "STRIPE_PRO_PRICE_ID")  else None,
    "team": settings.STRIPE_TEAM_PRICE_ID if hasattr(settings, "STRIPE_TEAM_PRICE_ID") else None,
}

PRICE_TO_PLAN: dict[str, str] = {}

def _build_price_map():
    global PRICE_TO_PLAN
    for plan, price_id in PLAN_PRICE_IDS.items():
        if price_id:
            PRICE_TO_PLAN[price_id] = plan

_build_price_map()


def get_or_create_customer(db: Session, user_id: int, email: str) -> str:
    """Get existing Stripe customer or create new one."""
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if sub and sub.stripe_customer_id:
        return sub.stripe_customer_id

    s = _stripe()
    customer = s.Customer.create(
        email=email,
        metadata={"user_id": str(user_id)},
    )
    if sub:
        sub.stripe_customer_id = customer.id
    else:
        sub = Subscription(
            user_id=user_id,
            plan="free",
            status="active",
            stripe_customer_id=customer.id,
        )
        db.add(sub)
    db.commit()
    logger.info(f"Stripe customer created: {customer.id} for user {user_id}")
    return customer.id


def create_checkout_session(
    customer_id: str,
    plan: str,
    success_url: str,
    cancel_url: str,
    user_id: int,
) -> dict:
    """Create a Stripe Checkout session for a subscription."""
    price_id = PLAN_PRICE_IDS.get(plan)
    if not price_id:
        raise ValueError(f"No Stripe price ID configured for plan '{plan}'. Set STRIPE_PRO_PRICE_ID / STRIPE_TEAM_PRICE_ID.")

    s = _stripe()
    session = s.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": str(user_id), "plan": plan},
        subscription_data={
            "metadata": {"user_id": str(user_id), "plan": plan}
        },
        allow_promotion_codes=True,
    )
    return {"checkout_url": session.url, "session_id": session.id}


def create_billing_portal(customer_id: str, return_url: str) -> str:
    """Create a Stripe Customer Portal session."""
    s = _stripe()
    session = s.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return session.url


def construct_webhook_event(payload: bytes, sig_header: str):
    """Validate Stripe webhook signature and parse event."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET not configured.")
    s = _stripe()
    try:
        event = s.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except stripe.error.SignatureVerificationError as e:
        raise ValueError(f"Invalid Stripe webhook signature: {e}")


def handle_subscription_event(db: Session, event) -> bool:
    """
    Process Stripe subscription lifecycle events.
    Returns True if event was processed, False if duplicate.
    """
    event_id = event["id"]
    event_type = event["type"]

    # Idempotency check — skip already-processed events
    existing = db.query(BillingEvent).filter(BillingEvent.stripe_event_id == event_id).first()
    if existing and existing.processed:
        logger.info(f"Skipping already-processed event: {event_id}")
        return False

    # Record the event
    billing_event = BillingEvent(
        stripe_event_id=event_id,
        event_type=event_type,
        event_data=json.dumps(event["data"]["object"]),
    )

    try:
        obj = event["data"]["object"]
        customer_id = obj.get("customer")

        sub_record = db.query(Subscription).filter(
            Subscription.stripe_customer_id == customer_id
        ).first() if customer_id else None

        if sub_record:
            billing_event.user_id = sub_record.user_id

        if event_type == "checkout.session.completed":
            _handle_checkout_completed(db, obj, sub_record)

        elif event_type in ("customer.subscription.updated", "customer.subscription.created"):
            _handle_subscription_updated(db, obj, sub_record)

        elif event_type == "customer.subscription.deleted":
            _handle_subscription_deleted(db, obj, sub_record)

        elif event_type == "invoice.payment_failed":
            if sub_record:
                sub_record.status = "past_due"
                db.flush()

        billing_event.processed = True
        db.add(billing_event)
        db.commit()
        logger.info(f"Processed Stripe event: {event_type} ({event_id})")
        return True

    except Exception as exc:
        logger.error(f"Failed processing Stripe event {event_id}: {exc}", exc_info=True)
        billing_event.processed = False
        db.add(billing_event)
        db.commit()
        raise


def _handle_checkout_completed(db: Session, obj: dict, sub_record):
    """Handle checkout.session.completed — subscription is now active."""
    if obj.get("mode") != "subscription":
        return
    stripe_sub_id = obj.get("subscription")
    user_id_meta = obj.get("metadata", {}).get("user_id")
    plan = obj.get("metadata", {}).get("plan", "pro")

    if not stripe_sub_id or not user_id_meta:
        return

    if not sub_record:
        customer_id = obj.get("customer")
        sub_record = db.query(Subscription).filter(
            Subscription.user_id == int(user_id_meta)
        ).first()
        if sub_record:
            sub_record.stripe_customer_id = customer_id

    if sub_record:
        sub_record.stripe_subscription_id = stripe_sub_id
        sub_record.plan = plan
        sub_record.status = "active"
        db.flush()
        _sync_credit_limits(db, sub_record.user_id, plan)


def _handle_subscription_updated(db: Session, obj: dict, sub_record):
    """Sync subscription state from Stripe."""
    if not sub_record:
        return

    status = obj.get("status", "active")
    plan_price_id = None
    items = obj.get("items", {}).get("data", [])
    if items:
        plan_price_id = items[0].get("price", {}).get("id")

    new_plan = PRICE_TO_PLAN.get(plan_price_id, sub_record.plan) if plan_price_id else sub_record.plan

    from datetime import datetime, timezone
    sub_record.status = status
    sub_record.plan = new_plan
    sub_record.stripe_subscription_id = obj.get("id", sub_record.stripe_subscription_id)
    sub_record.stripe_price_id = plan_price_id
    sub_record.cancel_at_period_end = obj.get("cancel_at_period_end", False)

    period_start = obj.get("current_period_start")
    period_end = obj.get("current_period_end")
    if period_start:
        sub_record.current_period_start = datetime.fromtimestamp(period_start, tz=timezone.utc)
    if period_end:
        sub_record.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)

    db.flush()
    _sync_credit_limits(db, sub_record.user_id, new_plan)


def _handle_subscription_deleted(db: Session, obj: dict, sub_record):
    """Downgrade to free on subscription cancellation."""
    if not sub_record:
        return
    sub_record.plan = "free"
    sub_record.status = "canceled"
    sub_record.stripe_subscription_id = None
    sub_record.cancel_at_period_end = False
    db.flush()
    _sync_credit_limits(db, sub_record.user_id, "free")


def _sync_credit_limits(db: Session, user_id: int, plan: str):
    """Update today's credit ledger limits to match the new plan."""
    from app.services.credit_service import PLAN_LIMITS, _get_or_create_subscription, _get_or_create_ledger
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    sub = _get_or_create_subscription(db, user_id)
    ledger = _get_or_create_ledger(db, user_id, sub)
    ledger.daily_limit = limits["daily"]
    ledger.monthly_limit = limits["monthly"]
    db.flush()
