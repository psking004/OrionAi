import React from "react";
import { useGetBillingStatus } from "@workspace/api-client-react";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Zap } from "lucide-react";
import { Link } from "wouter";

export function CreditsWidget() {
  const { data: status } = useGetBillingStatus();

  if (!status) return null;

  const dailyPct = (status.daily_used / status.daily_limit) * 100;
  const isLow = dailyPct > 80;
  const isCritical = dailyPct > 95;

  return (
    <Link href="/billing">
      <div className="flex items-center gap-2 px-2 py-1 rounded-lg border border-border/40 bg-background/50 hover:bg-card/50 transition-colors cursor-pointer group">
        <Zap className={`h-3.5 w-3.5 shrink-0 ${isCritical ? "text-destructive" : isLow ? "text-chart-2" : "text-chart-4"}`} />
        <div className="hidden sm:block">
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className="font-mono text-[10px] text-muted-foreground">CREDITS</span>
            <Badge variant="outline" className="font-mono text-[9px] py-0 uppercase">{status.plan}</Badge>
          </div>
          <div className="flex items-center gap-1.5">
            <Progress
              value={Math.max(0, 100 - dailyPct)}
              className="h-1 w-16"
            />
            <span className={`font-mono text-[10px] tabular-nums ${isCritical ? "text-destructive" : isLow ? "text-chart-2" : "text-foreground"}`}>
              {status.daily_remaining}/{status.daily_limit}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
