from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class CreditStatusResponse(BaseModel):
    plan: str
    subscription_status: str
    daily_used: int
    daily_limit: int
    daily_remaining: int
    monthly_used: int
    monthly_limit: int
    monthly_remaining: int
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    feature_costs: dict

    model_config = {"from_attributes": True}


class CheckoutSessionRequest(BaseModel):
    plan: str  # pro | team
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str


class BillingPortalRequest(BaseModel):
    return_url: str


class BillingPortalResponse(BaseModel):
    portal_url: str


class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    stripe_subscription_id: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False

    model_config = {"from_attributes": True}


class UsageEvent(BaseModel):
    feature: str
    credits_used: int
    project_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UsageHistoryResponse(BaseModel):
    events: list[UsageEvent]
    total_events: int


class PlanInfo(BaseModel):
    id: str
    name: str
    price_inr: int
    daily_credits: int
    monthly_credits: int
    features: list[str]
    stripe_price_id: Optional[str] = None
