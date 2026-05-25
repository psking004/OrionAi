"""
Billing routes — Stripe subscriptions, credits, webhooks.

POST /billing/checkout          Create Stripe Checkout session
POST /billing/portal            Create billing portal session
GET  /billing/status            Current plan + credit status
GET  /billing/plans             Available plans
GET  /billing/usage             Usage history
POST /billing/cancel            Cancel subscription at period end
POST /billing/webhook           Stripe webhook (raw body, signature validated)
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.db.models.billing import Subscription, CreditLedger, CreditUsageEvent
from app.db.schemas.billing import (
    CheckoutSessionRequest, CheckoutSessionResponse,
    BillingPortalRequest, BillingPortalResponse,
    CreditStatusResponse, SubscriptionResponse,
    UsageHistoryResponse, UsageEvent, PlanInfo,
)
from app.services import credit_service, stripe_service
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])


PLANS = [
    PlanInfo(
        id="free",
        name="Free",
        price_inr=0,
        daily_credits=25,
        monthly_credits=500,
        features=[
            "25 credits/day",
            "500 credits/month",
            "Basic AI analysis",
            "ZIP upload (1 per day)",
            "Standard processing",
        ],
    ),
    PlanInfo(
        id="pro",
        name="Pro",
        price_inr=499,
        daily_credits=500,
        monthly_credits=15_000,
        features=[
            "500 credits/day",
            "15,000 credits/month",
            "AI CTO mode",
            "Advanced architecture intelligence",
            "Continuous GitHub sync",
            "Advanced debugging",
            "Roadmap intelligence",
            "Memory system",
            "Faster processing",
        ],
        stripe_price_id=settings.STRIPE_PRO_PRICE_ID,
    ),
    PlanInfo(
        id="team",
        name="Team",
        price_inr=1_999,
        daily_credits=3_000,
        monthly_credits=100_000,
        features=[
            "3,000 credits/day",
            "100,000 credits/month",
            "Multi-user workspaces",
            "Organization analytics",
            "Shared AI memory",
            "Team dashboards",
            "Engineering velocity tracking",
            "Collaborative AI agents",
            "Centralized intelligence",
        ],
        stripe_price_id=settings.STRIPE_TEAM_PRICE_ID,
    ),
]


@router.get("/plans", response_model=list[PlanInfo])
def get_plans():
    """Return available subscription plans."""
    return PLANS


@router.get("/status", response_model=CreditStatusResponse)
def get_billing_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return current plan, credit usage, and subscription details."""
    return credit_service.get_credit_status(db, current_user.id)


@router.get("/usage", response_model=UsageHistoryResponse)
def get_usage_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return recent AI feature usage events."""
    events = (
        db.query(CreditUsageEvent)
        .filter(CreditUsageEvent.user_id == current_user.id)
        .order_by(CreditUsageEvent.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )
    return UsageHistoryResponse(
        events=[UsageEvent.model_validate(e) for e in events],
        total_events=len(events),
    )


@router.post("/checkout", response_model=CheckoutSessionResponse)
def create_checkout_session(
    payload: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe Checkout session to upgrade plan."""
    if payload.plan not in ("pro", "team"):
        raise HTTPException(status_code=400, detail="Invalid plan. Choose 'pro' or 'team'.")

    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Stripe not configured. Set STRIPE_SECRET_KEY in environment.",
        )

    try:
        customer_id = stripe_service.get_or_create_customer(db, current_user.id, current_user.email)
        result = stripe_service.create_checkout_session(
            customer_id=customer_id,
            plan=payload.plan,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
            user_id=current_user.id,
        )
        return CheckoutSessionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Stripe checkout error for user {current_user.id}: {e}")
        raise HTTPException(status_code=502, detail="Stripe service error. Try again later.")


@router.post("/portal", response_model=BillingPortalResponse)
def create_billing_portal(
    payload: BillingPortalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create Stripe Customer Portal session to manage subscription."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured.")

    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No Stripe customer found. Subscribe first.")

    try:
        portal_url = stripe_service.create_billing_portal(sub.stripe_customer_id, payload.return_url)
        return BillingPortalResponse(portal_url=portal_url)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Stripe portal error for user {current_user.id}: {e}")
        raise HTTPException(status_code=502, detail="Stripe service error.")


@router.post("/cancel")
def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel subscription at end of billing period."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured.")

    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if not sub or not sub.stripe_subscription_id:
        raise HTTPException(status_code=404, detail="No active subscription found.")

    try:
        import stripe as stripe_lib
        stripe_lib.api_key = settings.STRIPE_SECRET_KEY
        stripe_lib.Subscription.modify(
            sub.stripe_subscription_id,
            cancel_at_period_end=True,
        )
        sub.cancel_at_period_end = True
        db.commit()
        return {"message": "Subscription will cancel at period end.", "cancel_at_period_end": True}
    except Exception as e:
        logger.error(f"Stripe cancel error for user {current_user.id}: {e}")
        raise HTTPException(status_code=502, detail="Stripe service error.")


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Stripe webhook handler.
    Validates signature to prevent replay attacks.
    Uses raw body for signature verification.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.warning("Stripe webhook received but STRIPE_WEBHOOK_SECRET not set — ignoring.")
        return JSONResponse(status_code=200, content={"status": "no_secret"})

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe_service.construct_webhook_event(payload, sig_header)
    except ValueError as e:
        logger.warning(f"Stripe webhook signature validation failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_type = event["type"]
    logger.info(f"Stripe webhook received: {event_type} ({event['id']})")

    handled_events = {
        "checkout.session.completed",
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "invoice.payment_failed",
        "invoice.payment_succeeded",
    }

    if event_type in handled_events:
        try:
            stripe_service.handle_subscription_event(db, event)
        except Exception as e:
            logger.error(f"Webhook processing error: {e}", exc_info=True)
            # Return 200 to prevent Stripe retries for non-retriable errors
            return JSONResponse(status_code=200, content={"status": "processing_error"})

    return JSONResponse(status_code=200, content={"status": "ok"})
