import React from "react";
import { useGetDashboardOverview } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import {
  Activity, AlertTriangle, CheckCircle2, Zap, Github, Upload,
  TrendingUp, Shield, Users, Cpu, BarChart3, ArrowRight, Clock,
} from "lucide-react";
import { HealthGauge } from "@/components/health-gauge";

function StatCard({ label, value, sub, icon, accent }: {
  label: string; value: string | number; sub?: string;
  icon: React.ReactNode; accent?: string;
}) {
  return (
    <Card className="bg-card/30 border-border/50">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <span className="font-mono text-[10px] text-muted-foreground uppercase">{label}</span>
          <div className={accent || "text-muted-foreground"}>{icon}</div>
        </div>
        <div className={`text-2xl font-mono font-bold ${accent || ""}`}>{value}</div>
        {sub && <div className="text-[10px] font-mono text-muted-foreground mt-1">{sub}</div>}
      </CardContent>
    </Card>
  );
}

function AlertItem({ alert }: { alert: any }) {
  const styles: Record<string, string> = {
    problem: "border-destructive/20 bg-destructive/5 text-destructive",
    blocker: "border-chart-1/20 bg-chart-1/5 text-chart-1",
  };
  return (
    <div className={`flex items-start gap-2.5 p-2.5 rounded-lg border text-xs ${styles[alert.type] || styles.problem}`}>
      <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="font-mono text-[10px] mb-0.5 opacity-70">{alert.project_name}</div>
        <div className="leading-snug">{alert.message}</div>
      </div>
      <Link href={`/projects/${alert.project_id}`}>
        <ArrowRight className="h-3 w-3 opacity-50 hover:opacity-100 shrink-0" />
      </Link>
    </div>
  );
}

export default function OverviewPage() {
  const { data, isLoading } = useGetDashboardOverview();

  if (isLoading) {
    return (
      <div className="container max-w-screen-xl p-6 space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <Skeleton key={i} className="h-28" />)}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (!data) return null;

  const overview = data as any;
  const { projects, ai_alerts, credits, github_velocity, recent_scans, top_recommendations, top_risks } = overview;
  const dailyPct = credits ? (credits.daily_remaining / credits.daily_limit) * 100 : 100;

  return (
    <ScrollArea className="flex-1">
      <div className="container max-w-screen-xl p-4 md:p-6 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Command Center
            </h1>
            <p className="text-muted-foreground text-sm mt-0.5">
              {overview.user?.username} · <span className="font-mono uppercase">{credits?.plan}</span> plan
            </p>
          </div>
          <div className="text-[10px] font-mono text-muted-foreground flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {new Date((data as any).generated_at).toLocaleTimeString()}
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="Total Projects"
            value={projects.total}
            sub={`${projects.active} active`}
            icon={<Cpu className="h-4 w-4" />}
            accent="text-primary"
          />
          <StatCard
            label="Avg Health Score"
            value={projects.avg_health_score}
            sub={`${projects.health_distribution.healthy} healthy`}
            icon={<Activity className="h-4 w-4" />}
            accent={projects.avg_health_score >= 70 ? "text-chart-4" : projects.avg_health_score >= 45 ? "text-chart-2" : "text-destructive"}
          />
          <StatCard
            label="Daily Credits Left"
            value={credits.daily_remaining}
            sub={`${credits.daily_limit - credits.daily_remaining} used`}
            icon={<Zap className="h-4 w-4" />}
            accent={dailyPct > 50 ? "text-chart-4" : dailyPct > 20 ? "text-chart-2" : "text-destructive"}
          />
          <StatCard
            label="Repos Synced"
            value={github_velocity.connected_repos}
            sub={`${github_velocity.total_commits} total commits`}
            icon={<Github className="h-4 w-4" />}
          />
        </div>

        {/* Health Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card className="bg-card/30 border-border/50 col-span-1">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-mono text-muted-foreground">HEALTH DISTRIBUTION</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-chart-4">Healthy (≥70)</span>
                  <span>{projects.health_distribution.healthy}</span>
                </div>
                <Progress value={projects.total > 0 ? (projects.health_distribution.healthy / projects.total) * 100 : 0} className="h-1.5" />
              </div>
              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-chart-2">Needs Attention</span>
                  <span>{projects.health_distribution.needs_attention}</span>
                </div>
                <Progress value={projects.total > 0 ? (projects.health_distribution.needs_attention / projects.total) * 100 : 0} className="h-1.5" />
              </div>
              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-destructive">Critical (&lt;40)</span>
                  <span>{projects.health_distribution.critical}</span>
                </div>
                <Progress value={projects.total > 0 ? (projects.health_distribution.critical / projects.total) * 100 : 0} className="h-1.5" />
              </div>
            </CardContent>
          </Card>

          {/* At-Risk Projects */}
          <Card className="bg-card/30 border-border/50 col-span-1">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-mono text-muted-foreground flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5 text-destructive" /> AT-RISK PROJECTS
              </CardTitle>
            </CardHeader>
            <CardContent>
              {projects.at_risk.length === 0 ? (
                <div className="text-center py-4 text-xs text-muted-foreground font-mono opacity-50">
                  <CheckCircle2 className="h-6 w-6 mx-auto mb-2 text-chart-4" />
                  All projects healthy
                </div>
              ) : (
                <div className="space-y-2">
                  {projects.at_risk.map((p: any) => (
                    <Link key={p.project_id} href={`/projects/${p.project_id}`}>
                      <div className="flex items-center justify-between p-2 border border-destructive/20 bg-destructive/5 rounded-lg hover:bg-destructive/10 transition-colors cursor-pointer">
                        <div>
                          <div className="font-mono text-xs font-semibold">{p.name}</div>
                          <div className="text-[10px] text-muted-foreground font-mono">{p.progress?.toUpperCase()}</div>
                        </div>
                        <HealthGauge score={p.health_score} size={36} strokeWidth={3} />
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Credits Usage */}
          <Card className="bg-card/30 border-border/50 col-span-1">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-mono text-muted-foreground flex items-center gap-1.5">
                <BarChart3 className="h-3.5 w-3.5" /> CREDIT USAGE (30d)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {Object.keys(credits.usage_breakdown || {}).length === 0 ? (
                <div className="text-center py-4 text-xs text-muted-foreground font-mono opacity-50">No usage yet</div>
              ) : (
                <div className="space-y-2">
                  {Object.entries(credits.usage_breakdown as Record<string, number>)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 6)
                    .map(([feature, total]) => (
                      <div key={feature} className="flex items-center justify-between text-xs font-mono">
                        <span className="text-muted-foreground">{feature.replace(/_/g, " ")}</span>
                        <span className="text-foreground">{total} cr</span>
                      </div>
                    ))}
                </div>
              )}
              <Link href="/billing">
                <Button size="sm" variant="outline" className="w-full mt-3 font-mono text-[10px]">
                  VIEW FULL BILLING
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* AI Alerts + Recommendations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card className="bg-card/30 border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-mono text-muted-foreground flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5 text-chart-1" /> AI ALERTS
              </CardTitle>
            </CardHeader>
            <CardContent>
              {ai_alerts.length === 0 ? (
                <div className="text-center py-6 text-xs text-muted-foreground font-mono opacity-50">
                  <CheckCircle2 className="h-6 w-6 mx-auto mb-2 text-chart-4" />
                  No active alerts
                </div>
              ) : (
                <div className="space-y-2">
                  {ai_alerts.map((alert: any, i: number) => <AlertItem key={i} alert={alert} />)}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="bg-card/30 border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-mono text-muted-foreground flex items-center gap-1.5">
                <Zap className="h-3.5 w-3.5 text-chart-4" /> AI RECOMMENDATIONS
              </CardTitle>
            </CardHeader>
            <CardContent>
              {top_recommendations.length === 0 ? (
                <div className="text-center py-6 text-xs text-muted-foreground font-mono opacity-50">
                  Upload a ZIP to get AI recommendations
                </div>
              ) : (
                <div className="space-y-2">
                  {top_recommendations.map((r: string, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-xs p-2 bg-chart-4/5 border border-chart-4/20 rounded">
                      <ArrowRight className="h-3 w-3 mt-0.5 text-chart-4 shrink-0" />
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* GitHub Velocity */}
        {github_velocity.repos.length > 0 && (
          <Card className="bg-card/30 border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-mono text-muted-foreground flex items-center gap-1.5">
                <Github className="h-3.5 w-3.5" /> GITHUB VELOCITY
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {github_velocity.repos.map((repo: any) => (
                  <Link key={repo.project_id} href={`/projects/${repo.project_id}`}>
                    <div className="border border-border/40 rounded-lg p-3 hover:bg-card/50 transition-colors cursor-pointer">
                      <div className="font-mono text-xs font-semibold mb-1 text-primary">{repo.repo}</div>
                      <div className="text-muted-foreground text-[10px] mb-2">{repo.project_name}</div>
                      <div className="grid grid-cols-2 gap-2 text-center">
                        <div>
                          <div className="font-mono text-sm font-bold">{repo.commits}</div>
                          <div className="text-[9px] font-mono text-muted-foreground">COMMITS</div>
                        </div>
                        <div>
                          <div className="font-mono text-sm font-bold">{repo.contributors}</div>
                          <div className="text-[9px] font-mono text-muted-foreground">DEVS</div>
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recent Scans */}
        {recent_scans.length > 0 && (
          <Card className="bg-card/30 border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-mono text-muted-foreground flex items-center gap-1.5">
                <Upload className="h-3.5 w-3.5" /> RECENT SCANS (7d)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {recent_scans.map((scan: any) => (
                  <Link key={scan.id} href={`/projects/${scan.project_id}`}>
                    <div className="flex items-center justify-between p-2.5 border border-border/30 rounded-lg hover:bg-card/50 transition-colors cursor-pointer">
                      <div className="flex items-center gap-3">
                        <Upload className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                        <span className="font-mono text-xs truncate max-w-[200px]">{scan.filename}</span>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        {scan.health_score != null && (
                          <span className={`font-mono text-xs font-bold ${scan.health_score >= 70 ? "text-chart-4" : scan.health_score >= 45 ? "text-chart-2" : "text-destructive"}`}>
                            {scan.health_score.toFixed(0)}
                          </span>
                        )}
                        <Badge variant="outline" className="font-mono text-[9px]">{scan.status}</Badge>
                        <span className="text-[10px] font-mono text-muted-foreground hidden md:block">
                          {new Date(scan.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </ScrollArea>
  );
}
