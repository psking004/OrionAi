import React, { useState } from "react";
import { useDebugProject } from "@workspace/api-client-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";
import { Bug, RefreshCw, AlertTriangle, Shield, Zap, ChevronRight, FileCode } from "lucide-react";

interface DebugTabProps {
  projectId: number;
}

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-destructive/20 text-destructive border-destructive/30",
  high: "bg-chart-1/20 text-chart-1 border-chart-1/30",
  medium: "bg-chart-2/20 text-chart-2 border-chart-2/30",
  low: "bg-chart-4/20 text-chart-4 border-chart-4/30",
};

export default function DebugTab({ projectId }: DebugTabProps) {
  const { toast } = useToast();
  const [logs, setLogs] = useState("");
  const [errorTrace, setErrorTrace] = useState("");
  const [debugResult, setDebugResult] = useState<any>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const debugMutation = useDebugProject();

  const handleAnalyze = () => {
    if (!logs.trim()) {
      toast({ title: "No logs provided", description: "Paste logs or a stack trace to analyze.", variant: "destructive" });
      return;
    }

    debugMutation.mutate(
      {
        projectId,
        data: {
          logs: logs.trim(),
          error_trace: errorTrace.trim() || null,
        },
      },
      {
        onSuccess: (data: any) => {
          setDebugResult(data);
          toast({ title: "Debug Analysis Complete", description: `Severity: ${data.severity?.toUpperCase()}` });
        },
        onError: () => {
          toast({ title: "Analysis Failed", variant: "destructive" });
        },
      }
    );
  };

  const handleClear = () => {
    setLogs("");
    setErrorTrace("");
    setDebugResult(null);
  };

  return (
    <ScrollArea className="flex-1 p-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Bug className="h-4 w-4 text-muted-foreground" />
          <span className="font-mono text-xs font-semibold">AI DEBUG ENGINE</span>
        </div>

        {/* Input Area */}
        <div className="space-y-2">
          <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider">
            Paste logs, error output, or stack trace
          </label>
          <Textarea
            value={logs}
            onChange={(e) => setLogs(e.target.value)}
            placeholder={`Example:
Traceback (most recent call last):
  File "app.py", line 42, in run
    db.connect()
ConnectionRefusedError: [Errno 111] Connection refused`}
            className="font-mono text-xs bg-background border-border/50 min-h-[120px] max-h-[200px] resize-none"
            disabled={debugMutation.isPending}
          />
        </div>

        <button
          className="text-[10px] font-mono text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? <ChevronRight className="h-3 w-3 rotate-90" /> : <ChevronRight className="h-3 w-3" />}
          Additional context (optional)
        </button>

        {showAdvanced && (
          <Textarea
            value={errorTrace}
            onChange={(e) => setErrorTrace(e.target.value)}
            placeholder="Full stack trace, HTTP response body, or additional context..."
            className="font-mono text-xs bg-background border-border/50 min-h-[80px] max-h-[120px] resize-none"
            disabled={debugMutation.isPending}
          />
        )}

        <div className="flex gap-2">
          <Button
            className="flex-1 font-mono text-xs bg-destructive/10 text-destructive border border-destructive/20 hover:bg-destructive/20"
            onClick={handleAnalyze}
            disabled={debugMutation.isPending || !logs.trim()}
          >
            {debugMutation.isPending ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Bug className="h-4 w-4 mr-2" />
            )}
            {debugMutation.isPending ? "ANALYZING..." : "ANALYZE LOGS"}
          </Button>
          {debugResult && (
            <Button size="sm" variant="outline" className="font-mono text-xs" onClick={handleClear}>
              CLEAR
            </Button>
          )}
        </div>

        {/* Debug Result */}
        {debugResult && (
          <div className="space-y-3 border-t border-border/20 pt-3">
            {/* Severity + Error Type */}
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="outline" className={`font-mono text-[10px] uppercase ${SEVERITY_STYLES[debugResult.severity] || SEVERITY_STYLES.medium}`}>
                <AlertTriangle className="h-2.5 w-2.5 mr-1" />
                {debugResult.severity?.toUpperCase()} SEVERITY
              </Badge>
              {debugResult.error_type && (
                <Badge variant="outline" className="font-mono text-[10px] bg-background">
                  {debugResult.error_type.replace(/_/g, " ").toUpperCase()}
                </Badge>
              )}
            </div>

            {/* Root Cause */}
            <div className="space-y-1.5">
              <h5 className="font-mono text-[10px] text-destructive flex items-center gap-1.5">
                <Bug className="h-3 w-3" /> ROOT_CAUSE
              </h5>
              <div className="text-xs p-3 bg-destructive/5 border border-destructive/15 rounded leading-relaxed font-mono">
                {debugResult.root_cause}
              </div>
            </div>

            {/* Affected Modules */}
            {debugResult.affected_modules?.length > 0 && (
              <div className="space-y-1.5">
                <h5 className="font-mono text-[10px] text-muted-foreground flex items-center gap-1.5">
                  <FileCode className="h-3 w-3" /> AFFECTED_MODULES
                </h5>
                <div className="flex flex-wrap gap-1">
                  {debugResult.affected_modules.map((m: string, i: number) => (
                    <Badge key={i} variant="outline" className="font-mono text-[10px]">{m}</Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Suggested Fixes */}
            {debugResult.suggested_fixes?.length > 0 && (
              <div className="space-y-1.5">
                <h5 className="font-mono text-[10px] text-chart-4 flex items-center gap-1.5">
                  <Zap className="h-3 w-3" /> SUGGESTED_FIXES
                </h5>
                {debugResult.suggested_fixes.map((fix: string, i: number) => (
                  <div key={i} className="text-xs p-2.5 bg-chart-4/5 border border-chart-4/20 rounded flex items-start gap-2 leading-snug">
                    <span className="font-mono text-chart-4 text-[10px] mt-0.5 shrink-0">{i+1}.</span>
                    {fix}
                  </div>
                ))}
              </div>
            )}

            {/* Prevention Strategies */}
            {debugResult.prevention_strategies?.length > 0 && (
              <div className="space-y-1.5">
                <h5 className="font-mono text-[10px] text-chart-2 flex items-center gap-1.5">
                  <Shield className="h-3 w-3" /> PREVENTION
                </h5>
                {debugResult.prevention_strategies.map((p: string, i: number) => (
                  <div key={i} className="text-xs p-2 bg-chart-2/5 border border-chart-2/15 rounded leading-snug">{p}</div>
                ))}
              </div>
            )}

            {/* Similar Patterns */}
            {debugResult.similar_patterns?.length > 0 && (
              <div className="space-y-1.5">
                <h5 className="font-mono text-[10px] text-muted-foreground flex items-center gap-1.5">
                  <ChevronRight className="h-3 w-3" /> SIMILAR_PATTERNS
                </h5>
                {debugResult.similar_patterns.map((p: string, i: number) => (
                  <div key={i} className="text-xs p-2 border border-border/30 rounded text-muted-foreground leading-snug">{p}</div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!debugResult && !debugMutation.isPending && (
          <div className="text-center p-6 border border-dashed border-border/30 rounded-lg opacity-40">
            <Bug className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
            <p className="font-mono text-xs text-muted-foreground">Paste an error log and the AI will identify root cause, affected modules, and fixes.</p>
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
