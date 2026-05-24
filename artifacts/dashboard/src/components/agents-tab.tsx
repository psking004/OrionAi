import React, { useState } from "react";
import { useGetAgentTeam } from "@workspace/api-client-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { RefreshCw, Users, ChevronDown, ChevronRight, AlertTriangle, Zap, CheckCircle2, ArrowRight } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

interface AgentsTabProps {
  projectId: number;
}

const AGENT_ICONS: Record<string, string> = {
  "CTO Agent": "⚙️",
  "PM Agent": "📋",
  "QA Agent": "🧪",
  "DevOps Agent": "🚀",
  "Security Agent": "🔒",
};

const AGENT_COLORS: Record<string, string> = {
  "CTO Agent": "text-chart-2 border-chart-2/30 bg-chart-2/5",
  "PM Agent": "text-primary border-primary/30 bg-primary/5",
  "QA Agent": "text-chart-4 border-chart-4/30 bg-chart-4/5",
  "DevOps Agent": "text-chart-3 border-chart-3/30 bg-chart-3/5",
  "Security Agent": "text-destructive border-destructive/30 bg-destructive/5",
};

function ScoreRing({ score, agent }: { score: number; agent: string }) {
  const r = 20, c = 2 * Math.PI * r;
  const filled = (score / 100) * c;
  const color = score >= 70 ? "#22c55e" : score >= 45 ? "#f59e0b" : "#ef4444";

  return (
    <div className="relative w-12 h-12 flex items-center justify-center shrink-0">
      <svg className="absolute -rotate-90" width="48" height="48">
        <circle cx="24" cy="24" r={r} fill="none" stroke="currentColor" strokeWidth="3" className="text-border/30" />
        <circle cx="24" cy="24" r={r} fill="none" stroke={color} strokeWidth="3"
          strokeDasharray={`${filled} ${c}`} strokeLinecap="round" />
      </svg>
      <span className="font-mono text-[10px] font-bold relative z-10">{score.toFixed(0)}</span>
    </div>
  );
}

function AgentCard({ agent }: { agent: any }) {
  const [open, setOpen] = useState(false);
  const color = AGENT_COLORS[agent.agent] || "text-muted-foreground border-border bg-card";
  const icon = AGENT_ICONS[agent.agent] || "🤖";

  return (
    <div className={`border rounded-lg overflow-hidden ${color}`}>
      <button
        className="w-full flex items-center gap-3 p-3 text-left hover:bg-white/5 transition-colors"
        onClick={() => setOpen(!open)}
      >
        <span className="text-base">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="font-mono text-xs font-bold">{agent.agent}</div>
          <div className="text-[10px] font-mono text-muted-foreground">{agent.role}</div>
        </div>
        <ScoreRing score={agent.score} agent={agent.agent} />
        {open ? <ChevronDown className="h-3 w-3 shrink-0" /> : <ChevronRight className="h-3 w-3 shrink-0" />}
      </button>

      {open && (
        <div className="px-3 pb-3 space-y-3 border-t border-current/10">
          {agent.risks?.length > 0 && (
            <div className="space-y-1.5 pt-2">
              <div className="font-mono text-[10px] text-destructive flex items-center gap-1">
                <AlertTriangle className="h-2.5 w-2.5" /> RISKS
              </div>
              {agent.risks.slice(0, 3).map((r: string, i: number) => (
                <div key={i} className="text-xs p-1.5 bg-destructive/5 border border-destructive/10 rounded leading-snug">{r}</div>
              ))}
            </div>
          )}

          {agent.priorities?.length > 0 && (
            <div className="space-y-1.5">
              <div className="font-mono text-[10px] text-chart-1 flex items-center gap-1">
                <AlertTriangle className="h-2.5 w-2.5" /> PRIORITIES
              </div>
              {agent.priorities.slice(0, 3).map((p: string, i: number) => (
                <div key={i} className="text-xs p-1.5 border border-chart-1/10 rounded leading-snug">{p}</div>
              ))}
            </div>
          )}

          {agent.recommendations?.length > 0 && (
            <div className="space-y-1.5">
              <div className="font-mono text-[10px] text-chart-4 flex items-center gap-1">
                <Zap className="h-2.5 w-2.5" /> RECOMMENDATIONS
              </div>
              {agent.recommendations.slice(0, 3).map((r: string, i: number) => (
                <div key={i} className="text-xs p-1.5 bg-chart-4/5 border border-chart-4/15 rounded leading-snug">{r}</div>
              ))}
            </div>
          )}

          {agent.actions?.length > 0 && (
            <div className="space-y-1.5">
              <div className="font-mono text-[10px] text-primary flex items-center gap-1">
                <ArrowRight className="h-2.5 w-2.5" /> ACTIONS
              </div>
              {agent.actions.slice(0, 3).map((a: string, i: number) => (
                <div key={i} className="text-xs p-1.5 bg-primary/5 border border-primary/20 rounded leading-snug flex items-start gap-1.5">
                  <ArrowRight className="h-2.5 w-2.5 mt-0.5 text-primary shrink-0" />
                  {a}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function AgentsTab({ projectId }: AgentsTabProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: teamData, isLoading, refetch } = useGetAgentTeam(projectId);

  const handleRefresh = () => {
    refetch();
    toast({ title: "Refreshing agents...", description: "AI team is re-evaluating." });
  };

  const agents = teamData ? [teamData.cto, teamData.pm, teamData.qa, teamData.devops, teamData.security] : [];

  return (
    <ScrollArea className="flex-1 p-4">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span className="font-mono text-xs font-semibold">AI TEAM COUNCIL</span>
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
            {[1,2,3,4,5].map(i => (
              <div key={i} className="h-14 border border-border/30 rounded-lg animate-pulse bg-card/30" />
            ))}
          </div>
        ) : teamData ? (
          <>
            {/* Risk Level Banner */}
            <div className={`flex items-center gap-2 p-2.5 rounded-lg border font-mono text-xs ${
              teamData.overall_risk_level === "critical" ? "bg-destructive/10 border-destructive/30 text-destructive" :
              teamData.overall_risk_level === "high" ? "bg-chart-1/10 border-chart-1/30 text-chart-1" :
              teamData.overall_risk_level === "medium" ? "bg-chart-2/10 border-chart-2/30 text-chart-2" :
              "bg-chart-4/10 border-chart-4/30 text-chart-4"
            }`}>
              <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
              OVERALL RISK: {teamData.overall_risk_level.toUpperCase()}
            </div>

            {/* Consensus Priorities */}
            {teamData.consensus_priorities?.length > 0 && (
              <div className="space-y-2 bg-background/30 border border-border/40 rounded-lg p-3">
                <div className="font-mono text-[10px] text-muted-foreground flex items-center gap-1.5">
                  <CheckCircle2 className="h-3 w-3" /> TEAM_CONSENSUS_PRIORITIES
                </div>
                {teamData.consensus_priorities.slice(0, 5).map((p: string, i: number) => (
                  <div key={i} className="flex items-start gap-2 text-xs">
                    <span className="font-mono text-muted-foreground/50 text-[10px] mt-0.5 w-4 shrink-0">{i+1}.</span>
                    <span className="leading-snug">{p}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Agent Cards */}
            <div className="space-y-2">
              {agents.map((agent: any) => agent && <AgentCard key={agent.agent} agent={agent} />)}
            </div>
          </>
        ) : (
          <div className="text-center p-8 text-muted-foreground opacity-50">
            <Users className="h-10 w-10 mx-auto mb-3" />
            <p className="font-mono text-xs">Upload a ZIP or connect GitHub to activate agents.</p>
            <Button size="sm" className="mt-4 font-mono text-xs" onClick={handleRefresh}>
              <RefreshCw className="h-3 w-3 mr-1" /> LOAD AGENTS
            </Button>
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
