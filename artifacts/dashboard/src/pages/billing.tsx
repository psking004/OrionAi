import React, { useState } from "react";
import { useGetBillingStatus, useGetPlans, useGetUsageHistory, useCreateCheckoutSession, useCreateBillingPortal } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import {
  CreditCard, Zap, CheckCircle2, ArrowUpRight, Calendar,
  BarChart3, RefreshCw, Shield, Users, Cpu, Clock,
} from "lucide-react";

const PLAN_GRADIENTS: Record<string, string> = {
  free: "border-border/50 bg-card/30",
  pro:  "border-primary/40 bg-primary/5",
  team: "border-chart-2/40 bg-chart-2/5",
};
const PLAN_ACCENT: Record<string, string> = {
  free: "text-muted-foreground",
  pro:  "text-primary",
  team: "text-chart-2",
};
const PLAN_ICONS: Record<string, React.ReactNode> = {
  free: <Zap className="h-5 w-5" />,
  pro:  <Cpu className="h-5 w-5" />,
  team: <Users className="h-5 w-5" />,
};

export default function BillingPage() {
  const { toast } = useToast();
  const [upgrading, setUpgrading] = useState<string | null>(null);

  const { data: status, isLoading: statusLoading } = useGetBillingStatus();
  const { data: plans = [] } = useGetPlans();
  const { data: usage } = useGetUsageHistory();

  const checkoutMutation = useCreateCheckoutSession();
  const portalMutation = useCreateBillingPortal();

  const handleUpgrade = (planId: string) => {
    if (planId === "free") return;
    setUpgrading(planId);
    const baseUrl = window.location.origin + import.meta.env.BASE_URL.replace(/\/$/, "");
    checkoutMutation.mutate(
      {
        data: {
          plan: planId,
          success_url: `${baseUrl}/billing?success=1`,
          cancel_url: `${baseUrl}/billing?canceled=1`,
        },
      },
      {
        onSuccess: (data: any) => {
          window.location.href = data.checkout_url;
        },
        onError: (err: any) => {
          toast({
            title: "Stripe not configured",
            description: err?.response?.data?.detail || "Set STRIPE_SECRET_KEY to enable payments.",
            variant: "destructive",
          });
          setUpgrading(null);
        },
      }
    );
  };

  const handleManage = () => {
    const baseUrl = window.location.origin + import.meta.env.BASE_URL.replace(/\/$/, "");
    portalMutation.mutate(
      { data: { return_url: `${baseUrl}/billing` } },
      {
        onSuccess: (data: any) => {
          window.location.href = data.portal_url;
        },
        onError: () => {
          toast({ title: "Portal unavailable", description: "No active subscription found.", variant: "destructive" });
        },
      }
    );
  };

  if (statusLoading) {
    return (
      <div className="container max-w-screen-xl p-6 space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-64" />)}
        </div>
      </div>
    );
  }

  const currentPlan = status?.plan || "free";
  const dailyPct = status ? (status.daily_used / status.daily_limit) * 100 : 0;
  const monthlyPct = status ? (status.monthly_used / status.monthly_limit) * 100 : 0;

  return (
    <ScrollArea className="flex-1">
      <div className="container max-w-screen-xl p-4 md:p-6 space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight mb-1">Billing & Credits</h1>
          <p className="text-muted-foreground text-sm">Manage your subscription and monitor AI usage.</p>
        </div>

        {/* Credit Status Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-card/30 border-border/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-[10px] text-muted-foreground">CURRENT PLAN</span>
                <Badge variant="outline" className={`font-mono text-[10px] uppercase ${PLAN_ACCENT[currentPlan]}`}>
                  {currentPlan}
                </Badge>
              </div>
              <div className="text-2xl font-mono font-bold">{currentPlan.toUpperCase()}</div>
              {status?.current_period_end && (
                <div className="flex items-center gap-1 mt-2 text-[10px] font-mono text-muted-foreground">
                  <Calendar className="h-3 w-3" />
                  Renews {new Date(status.current_period_end).toLocaleDateString()}
                </div>
              )}
              {status?.cancel_at_period_end && (
                <div className="text-[10px] text-destructive font-mono mt-1">Cancels at period end</div>
              )}
            </CardContent>
          </Card>

          <Card className="bg-card/30 border-border/50">
            <CardContent className="p-4">
              <div className="font-mono text-[10px] text-muted-foreground mb-3">DAILY CREDITS</div>
              <div className="flex items-end justify-between mb-2">
                <span className="text-2xl font-mono font-bold">{status?.daily_remaining ?? 0}</span>
                <span className="text-xs font-mono text-muted-foreground">/ {status?.daily_limit ?? 25}</span>
              </div>
              <Progress value={Math.max(0, 100 - dailyPct)} className="h-1.5" />
              <div className="text-[10px] font-mono text-muted-foreground mt-1">{status?.daily_used ?? 0} used today</div>
            </CardContent>
          </Card>

          <Card className="bg-card/30 border-border/50">
            <CardContent className="p-4">
              <div className="font-mono text-[10px] text-muted-foreground mb-3">MONTHLY CREDITS</div>
              <div className="flex items-end justify-between mb-2">
                <span className="text-2xl font-mono font-bold">{status?.monthly_remaining ?? 0}</span>
                <span className="text-xs font-mono text-muted-foreground">/ {status?.monthly_limit ?? 500}</span>
              </div>
              <Progress value={Math.max(0, 100 - monthlyPct)} className="h-1.5" />
              <div className="text-[10px] font-mono text-muted-foreground mt-1">{status?.monthly_used ?? 0} used this month</div>
            </CardContent>
          </Card>

          <Card className="bg-card/30 border-border/50">
            <CardContent className="p-4">
              <div className="font-mono text-[10px] text-muted-foreground mb-3">CREDIT COSTS</div>
              <div className="space-y-1">
                {status?.feature_costs && Object.entries(status.feature_costs).map(([feature, cost]) => (
                  <div key={feature} className="flex justify-between text-[10px] font-mono">
                    <span className="text-muted-foreground">{feature}</span>
                    <span className="text-foreground">{String(cost)} cr</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Plans */}
        <div>
          <h2 className="text-lg font-bold mb-4 font-mono">SUBSCRIPTION PLANS</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {plans.map((plan: any) => {
              const isCurrent = plan.id === currentPlan;
              const isPopular = plan.id === "pro";
              return (
                <Card key={plan.id} className={`relative border ${PLAN_GRADIENTS[plan.id]} transition-all hover:shadow-lg`}>
                  {isPopular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <Badge className="bg-primary text-primary-foreground font-mono text-[10px] px-3">POPULAR</Badge>
                    </div>
                  )}
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between mb-2">
                      <div className={PLAN_ACCENT[plan.id]}>{PLAN_ICONS[plan.id]}</div>
                      {isCurrent && <Badge variant="outline" className="font-mono text-[10px]">CURRENT</Badge>}
                    </div>
                    <CardTitle className={`text-xl font-mono ${PLAN_ACCENT[plan.id]}`}>{plan.name.toUpperCase()}</CardTitle>
                    <div className="flex items-baseline gap-1">
                      {plan.price_inr === 0 ? (
                        <span className="text-3xl font-mono font-bold">FREE</span>
                      ) : (
                        <>
                          <span className="text-3xl font-mono font-bold">₹{plan.price_inr}</span>
                          <span className="text-sm text-muted-foreground font-mono">/month</span>
                        </>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <ul className="space-y-2">
                      {plan.features.map((f: string, i: number) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <CheckCircle2 className={`h-3.5 w-3.5 mt-0.5 shrink-0 ${PLAN_ACCENT[plan.id]}`} />
                          <span className="text-muted-foreground">{f}</span>
                        </li>
                      ))}
                    </ul>
                    {!isCurrent && plan.id !== "free" && (
                      <Button
                        className="w-full font-mono text-xs"
                        onClick={() => handleUpgrade(plan.id)}
                        disabled={upgrading === plan.id || checkoutMutation.isPending}
                      >
                        {upgrading === plan.id ? (
                          <RefreshCw className="h-3.5 w-3.5 mr-2 animate-spin" />
                        ) : (
                          <ArrowUpRight className="h-3.5 w-3.5 mr-2" />
                        )}
                        UPGRADE TO {plan.name.toUpperCase()}
                      </Button>
                    )}
                    {isCurrent && plan.id !== "free" && (
                      <Button variant="outline" className="w-full font-mono text-xs" onClick={handleManage}>
                        <CreditCard className="h-3.5 w-3.5 mr-2" />
                        MANAGE SUBSCRIPTION
                      </Button>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Usage History */}
        {usage && usage.events.length > 0 && (
          <div>
            <h2 className="text-lg font-bold mb-4 font-mono">USAGE HISTORY</h2>
            <Card className="bg-card/30 border-border/50">
              <CardContent className="p-0">
                <div className="divide-y divide-border/30">
                  {usage.events.slice(0, 20).map((event: any, i: number) => (
                    <div key={i} className="flex items-center justify-between px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="h-2 w-2 rounded-full bg-primary shrink-0" />
                        <span className="font-mono text-xs">{event.feature.replace(/_/g, " ").toUpperCase()}</span>
                        {event.project_id && (
                          <Badge variant="outline" className="font-mono text-[9px] py-0">proj #{event.project_id}</Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="font-mono text-xs text-muted-foreground">
                          {new Date(event.created_at).toLocaleString()}
                        </span>
                        <Badge variant="outline" className="font-mono text-[10px] text-chart-1">
                          -{event.credits_used} cr
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Security Note */}
        <Card className="bg-card/30 border-border/50">
          <CardContent className="p-4 flex items-start gap-3">
            <Shield className="h-5 w-5 text-chart-4 shrink-0 mt-0.5" />
            <div>
              <div className="font-mono text-xs font-semibold mb-1">SECURE PAYMENTS</div>
              <p className="text-xs text-muted-foreground">
                All payments are processed securely via Stripe. OrionOS never stores your card details.
                Webhook events are validated using Stripe signature verification to prevent replay attacks.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </ScrollArea>
  );
}
