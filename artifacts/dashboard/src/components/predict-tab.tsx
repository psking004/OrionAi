import React from "react";
import { usePredictFailures } from "@workspace/api-client-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";
import { AlertTriangle, RefreshCw, Shield, Zap, Activity, Server, Cpu } from "lucide-react";

interface PredictTabProps {
  projectId: number;
}

const RISK_STYLES: Record<string, { badge: string; bar: string }> = {
  critical: { badge: "bg-destructive/20 text-destructive border-destructive/30", bar: "bg-destructive" },
  high: { badge: "bg-chart-1/20 text-chart-1 border-chart-1/30", bar: "bg-chart-1" },
  medium: { badge: "bg-chart-2/20 text-chart-2 border-chart-2/30", bar: "bg-chart-2" },
  low: { badge: "bg-chart-4/20 text-chart-4 border-chart-4/30", bar: "bg-chart-4" },
};

interface RiskSectionProps {
  title: string;
  items: string[];
  icon: React.ReactNode;
  color: string;
  bg: string;
}

function RiskSection({ title, items, icon, color, bg }: RiskSectionProps) {
  if (!items?.length) return null;
  return (
    <div className="space-y-1.5">
      <h5 className={`font-mono text-[10px] flex items-center gap-1.5 ${color}`}>
        {icon} {title} ({items.length})
      </h5>
      {items.map((item: string, i: number) => (
        <div key={i} className={`text-xs p-2.5 border rounded leading-snug ${bg}`}>{item}</div>
      ))}
    </div>
  );
}

export default function PredictTab({ projectId }: PredictTabProps) {
  const { toast } = useToast();

  const { data: prediction, isLoading, refetch } = usePredictFailures(projectId);

  const handleRefresh = () => {
    refetch();
    toast({ title: "Refreshing prediction model..." });
  };

  const riskStyle = RISK_STYLES[prediction?.risk_level || "medium"] || RISK_STYLES.medium;

  return (
    <ScrollArea className="flex-1 p-4">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-muted-foreground" />
            <span className="font-mono text-xs font-semibold">FAILURE PREDICTION</span>
          </div>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 font-mono text-[10px] text-muted-foreground hover:text-foreground"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            {isLoading ? <RefreshCw className="h-3 w-3 mr-1 animate-spin" /> : <RefreshCw className="h-3 w-3 mr-1" />}
            REFRESH
          </Button>
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {[1,2,3,4].map(i => <div key={i} className="h-10 border border-border/30 rounded animate-pulse bg-card/30" />)}
          </div>
        ) : prediction ? (
          <>
            {/* Risk Score Gauge */}
            <div className="border border-border/40 rounded-lg p-4 bg-card/30 flex items-center gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-mono text-[10px] text-muted-foreground">OVERALL RISK SCORE</span>
                  <Badge variant="outline" className={`font-mono text-[10px] uppercase ${riskStyle.badge}`}>
                    {prediction.risk_level}
                  </Badge>
                </div>
                <div className="h-2 bg-border/30 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${riskStyle.bar}`}
                    style={{ width: `${prediction.overall_risk_score}%` }}
                  />
                </div>
                <div className="mt-1 font-mono text-[10px] text-muted-foreground text-right">
                  {prediction.overall_risk_score.toFixed(1)} / 100
                </div>
              </div>
            </div>

            {/* Risk Sections */}
            <RiskSection
              title="DEPLOYMENT_RISKS"
              items={prediction.deployment_risks}
              icon={<Server className="h-3 w-3" />}
              color="text-destructive"
              bg="bg-destructive/5 border-destructive/15"
            />
            <RiskSection
              title="SECURITY_VULNERABILITIES"
              items={prediction.security_vulnerabilities}
              icon={<Shield className="h-3 w-3" />}
              color="text-chart-1"
              bg="bg-chart-1/5 border-chart-1/15"
            />
            <RiskSection
              title="SCALABILITY_ISSUES"
              items={prediction.scalability_issues}
              icon={<Cpu className="h-3 w-3" />}
              color="text-chart-2"
              bg="bg-chart-2/5 border-chart-2/15"
            />
            <RiskSection
              title="FUTURE_BOTTLENECKS"
              items={prediction.future_bottlenecks}
              icon={<AlertTriangle className="h-3 w-3" />}
              color="text-chart-2"
              bg="bg-chart-2/5 border-chart-2/15"
            />
            <RiskSection
              title="UNSTABLE_MODULES"
              items={prediction.unstable_modules}
              icon={<Activity className="h-3 w-3" />}
              color="text-muted-foreground"
              bg="border-border/30"
            />

            {/* Mitigation Strategies */}
            {prediction.mitigation_strategies?.length > 0 && (
              <div className="space-y-1.5 pt-2 border-t border-border/20">
                <h5 className="font-mono text-[10px] text-chart-4 flex items-center gap-1.5">
                  <Zap className="h-3 w-3" /> MITIGATION_STRATEGIES
                </h5>
                {prediction.mitigation_strategies.map((s: string, i: number) => (
                  <div key={i} className="text-xs p-2.5 bg-chart-4/5 border border-chart-4/20 rounded leading-snug flex gap-2">
                    <span className="font-mono text-chart-4 text-[10px] shrink-0">{i+1}.</span>
                    {s}
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="text-center p-8 opacity-40">
            <Activity className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
            <p className="font-mono text-xs text-muted-foreground">
              Upload a ZIP or connect GitHub to enable failure prediction.<br />
              The AI analyzes your codebase for deployment risks and security vulnerabilities.
            </p>
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
