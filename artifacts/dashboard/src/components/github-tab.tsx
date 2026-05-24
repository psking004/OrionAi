import React, { useState } from "react";
import {
  useGetGithubConnection,
  useConnectGithub,
  useSyncGithub,
  useDisconnectGithub,
} from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";
import {
  Github, RefreshCw, Link2, Link2Off, GitCommit,
  GitBranch, Users, Star, GitMerge, TrendingUp, AlertTriangle, Zap,
} from "lucide-react";

interface GitHubTabProps {
  projectId: number;
}

function MomentumBadge({ momentum }: { momentum: string }) {
  const map: Record<string, string> = {
    strong: "bg-chart-4/20 text-chart-4 border-chart-4/30",
    steady: "bg-chart-2/20 text-chart-2 border-chart-2/30",
    slow: "bg-chart-1/20 text-chart-1 border-chart-1/30",
    stalled: "bg-destructive/20 text-destructive border-destructive/30",
    unknown: "bg-muted text-muted-foreground border-border",
  };
  return (
    <Badge variant="outline" className={`font-mono text-[10px] uppercase ${map[momentum] || map.unknown}`}>
      {momentum}
    </Badge>
  );
}

export default function GitHubTab({ projectId }: GitHubTabProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [showConnect, setShowConnect] = useState(false);
  const [token, setToken] = useState("");
  const [owner, setOwner] = useState("");
  const [repo, setRepo] = useState("");
  const [syncResult, setSyncResult] = useState<any>(null);

  const { data: connection, refetch: refetchConnection, isLoading } = useGetGithubConnection(projectId);

  const connectMutation = useConnectGithub();
  const syncMutation = useSyncGithub();
  const disconnectMutation = useDisconnectGithub();

  const handleConnect = () => {
    if (!token || !owner || !repo) {
      toast({ title: "Missing fields", description: "Fill in all GitHub fields.", variant: "destructive" });
      return;
    }
    connectMutation.mutate(
      { projectId, data: { github_token: token, repo_owner: owner, repo_name: repo } },
      {
        onSuccess: () => {
          toast({ title: "GitHub Connected", description: `${owner}/${repo} linked successfully.` });
          setShowConnect(false);
          setToken("");
          refetchConnection();
        },
        onError: (err: any) => {
          toast({ title: "Connection Failed", description: err?.response?.data?.detail || "Check token and repo.", variant: "destructive" });
        },
      }
    );
  };

  const handleSync = () => {
    syncMutation.mutate(
      { projectId },
      {
        onSuccess: (data: any) => {
          setSyncResult(data);
          refetchConnection();
          toast({ title: "Sync Complete", description: "Repository analyzed." });
        },
        onError: () => {
          toast({ title: "Sync Failed", description: "Could not reach GitHub API.", variant: "destructive" });
        },
      }
    );
  };

  const handleDisconnect = () => {
    disconnectMutation.mutate(
      { projectId },
      {
        onSuccess: () => {
          toast({ title: "Disconnected", description: "GitHub repo unlinked." });
          setSyncResult(null);
          refetchConnection();
        },
      }
    );
  };

  if (isLoading) {
    return <div className="p-8 text-center font-mono text-xs text-muted-foreground animate-pulse">SCANNING GITHUB LINK...</div>;
  }

  return (
    <ScrollArea className="flex-1 p-4">
      <div className="space-y-4">
        {!connection ? (
          /* Connect Form */
          <div className="space-y-4">
            <div className="border border-dashed border-border/50 rounded-lg p-6 text-center">
              <Github className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
              <p className="font-mono text-sm font-semibold mb-1">NO GITHUB REPO LINKED</p>
              <p className="text-xs text-muted-foreground font-mono mb-4">Connect a repository to enable commit analysis, velocity tracking, and risk detection.</p>
              <Button
                size="sm"
                className="font-mono text-xs bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20"
                onClick={() => setShowConnect(true)}
              >
                <Link2 className="h-3 w-3 mr-2" /> CONNECT REPOSITORY
              </Button>
            </div>

            {showConnect && (
              <div className="space-y-3 border border-border/40 rounded-lg p-4 bg-card/30">
                <p className="font-mono text-[10px] text-muted-foreground uppercase tracking-widest">GitHub Personal Access Token (repo scope)</p>
                <Input
                  type="password"
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  className="font-mono text-xs bg-background border-border/50"
                />
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    placeholder="owner"
                    value={owner}
                    onChange={(e) => setOwner(e.target.value)}
                    className="font-mono text-xs bg-background border-border/50"
                  />
                  <Input
                    placeholder="repo-name"
                    value={repo}
                    onChange={(e) => setRepo(e.target.value)}
                    className="font-mono text-xs bg-background border-border/50"
                  />
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    className="flex-1 font-mono text-xs"
                    onClick={handleConnect}
                    disabled={connectMutation.isPending}
                  >
                    {connectMutation.isPending ? <RefreshCw className="h-3 w-3 mr-2 animate-spin" /> : <Link2 className="h-3 w-3 mr-2" />}
                    {connectMutation.isPending ? "LINKING..." : "LINK"}
                  </Button>
                  <Button size="sm" variant="outline" className="font-mono text-xs" onClick={() => setShowConnect(false)}>
                    CANCEL
                  </Button>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Connected State */
          <div className="space-y-4">
            {/* Repo Header */}
            <div className="border border-border/40 rounded-lg p-4 bg-card/30">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Github className="h-4 w-4 text-muted-foreground" />
                    <span className="font-mono text-sm font-bold">{connection.repo_owner}/{connection.repo_name}</span>
                  </div>
                  {connection.description && (
                    <p className="text-xs text-muted-foreground max-w-xs">{connection.description}</p>
                  )}
                </div>
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-7 w-7 text-destructive/70 hover:text-destructive hover:bg-destructive/10"
                  onClick={handleDisconnect}
                  disabled={disconnectMutation.isPending}
                  title="Disconnect"
                >
                  <Link2Off className="h-3.5 w-3.5" />
                </Button>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-background/50 border border-border/40 rounded p-2">
                  <Star className="h-3 w-3 mx-auto mb-1 text-muted-foreground" />
                  <div className="font-mono text-xs font-bold">{connection.stars}</div>
                  <div className="text-[9px] font-mono text-muted-foreground">STARS</div>
                </div>
                <div className="bg-background/50 border border-border/40 rounded p-2">
                  <GitCommit className="h-3 w-3 mx-auto mb-1 text-muted-foreground" />
                  <div className="font-mono text-xs font-bold">{connection.commit_count}</div>
                  <div className="text-[9px] font-mono text-muted-foreground">COMMITS</div>
                </div>
                <div className="bg-background/50 border border-border/40 rounded p-2">
                  <Users className="h-3 w-3 mx-auto mb-1 text-muted-foreground" />
                  <div className="font-mono text-xs font-bold">{connection.contributor_count}</div>
                  <div className="text-[9px] font-mono text-muted-foreground">DEVS</div>
                </div>
              </div>

              {connection.language && (
                <div className="mt-3 flex items-center gap-2">
                  <span className="text-[10px] font-mono text-muted-foreground">PRIMARY LANG:</span>
                  <Badge variant="outline" className="font-mono text-[10px] border-primary/30 text-primary">{connection.language}</Badge>
                  <Badge variant="outline" className="font-mono text-[10px]">{connection.default_branch}</Badge>
                </div>
              )}
            </div>

            <Button
              className="w-full font-mono text-xs bg-chart-2/10 text-chart-2 border border-chart-2/20 hover:bg-chart-2/20"
              onClick={handleSync}
              disabled={syncMutation.isPending}
            >
              {syncMutation.isPending ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              {syncMutation.isPending ? "ANALYZING REPO..." : "SYNC & ANALYZE"}
            </Button>

            {/* Sync Results */}
            {syncResult && (
              <div className="space-y-3">
                <h4 className="font-mono text-[10px] text-muted-foreground border-t border-border/20 pt-2 flex items-center gap-1.5">
                  <TrendingUp className="h-3 w-3" /> COMMIT_INTELLIGENCE
                </h4>

                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-background/50 border border-border/40 rounded p-2">
                    <div className={`text-lg font-mono font-bold ${syncResult.velocity_score >= 60 ? "text-chart-4" : "text-chart-1"}`}>
                      {syncResult.velocity_score?.toFixed(0)}
                    </div>
                    <div className="text-[9px] font-mono text-muted-foreground">VELOCITY</div>
                  </div>
                  <div className="bg-background/50 border border-border/40 rounded p-2">
                    <div className={`text-lg font-mono font-bold ${syncResult.momentum_score >= 60 ? "text-chart-4" : "text-chart-1"}`}>
                      {syncResult.momentum_score?.toFixed(0)}
                    </div>
                    <div className="text-[9px] font-mono text-muted-foreground">MOMENTUM</div>
                  </div>
                  <div className="bg-background/50 border border-border/40 rounded p-2">
                    <div className={`text-lg font-mono font-bold ${syncResult.risk_score <= 30 ? "text-chart-4" : "text-destructive"}`}>
                      {syncResult.risk_score?.toFixed(0)}
                    </div>
                    <div className="text-[9px] font-mono text-muted-foreground">RISK</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-muted-foreground">MOMENTUM:</span>
                  <MomentumBadge momentum={syncResult.commit_analysis?.momentum || "unknown"} />
                  <span className="text-[10px] font-mono text-muted-foreground ml-auto">
                    {syncResult.commit_analysis?.avg_per_week?.toFixed(1)} commits/wk
                  </span>
                </div>

                {syncResult.risky_commits?.length > 0 && (
                  <div className="space-y-1.5">
                    <h5 className="font-mono text-[10px] text-chart-1 flex items-center gap-1.5">
                      <AlertTriangle className="h-3 w-3" /> RISKY_COMMITS ({syncResult.risky_commits.length})
                    </h5>
                    {syncResult.risky_commits.slice(0, 3).map((c: any, i: number) => (
                      <div key={i} className="text-xs p-2 bg-chart-1/5 border border-chart-1/10 rounded font-mono text-foreground/80 truncate">
                        [{c.sha}] {c.message}
                      </div>
                    ))}
                  </div>
                )}

                {syncResult.recommendations?.length > 0 && (
                  <div className="space-y-1.5">
                    <h5 className="font-mono text-[10px] text-chart-4 flex items-center gap-1.5">
                      <Zap className="h-3 w-3" /> RECOMMENDATIONS
                    </h5>
                    {syncResult.recommendations.slice(0, 4).map((r: string, i: number) => (
                      <div key={i} className="text-xs p-2 bg-chart-4/5 border border-chart-4/20 rounded text-foreground/90">{r}</div>
                    ))}
                  </div>
                )}

                {syncResult.recent_activity?.length > 0 && (
                  <div className="space-y-1.5">
                    <h5 className="font-mono text-[10px] text-muted-foreground flex items-center gap-1.5">
                      <GitCommit className="h-3 w-3" /> RECENT_COMMITS
                    </h5>
                    {syncResult.recent_activity.slice(0, 5).map((c: any, i: number) => (
                      <div key={i} className="text-xs p-2 border border-border/30 rounded font-mono">
                        <span className="text-primary">[{c.sha}]</span>
                        <span className="ml-2 text-foreground/80 truncate">{c.message}</span>
                        <div className="text-[10px] text-muted-foreground mt-0.5">{c.author}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {connection.last_synced && !syncResult && (
              <p className="text-[10px] font-mono text-muted-foreground text-center">
                Last synced: {new Date(connection.last_synced).toLocaleString()}
              </p>
            )}
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
