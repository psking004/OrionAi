import React, { useCallback, useState, useRef } from "react";
import { useUploadProjectZip, useListUploads, useGetLatestUpload } from "@workspace/api-client-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import {
  Upload, FileArchive, CheckCircle2, AlertTriangle, Clock,
  Cpu, Shield, Zap, BarChart3, RefreshCw, Code2, Globe, Database,
} from "lucide-react";

interface UploadTabProps {
  projectId: number;
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    complete: "bg-chart-4/20 text-chart-4 border-chart-4/30",
    processing: "bg-chart-2/20 text-chart-2 border-chart-2/30",
    pending: "bg-muted text-muted-foreground border-border",
    failed: "bg-destructive/20 text-destructive border-destructive/30",
  };
  return (
    <Badge variant="outline" className={`font-mono text-[10px] uppercase ${map[status] || map.pending}`}>
      {status}
    </Badge>
  );
}

function ScoreBar({ label, score, color }: { label: string; score: number; color: string }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center">
        <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">{label}</span>
        <span className={`text-sm font-mono font-bold ${color}`}>{score.toFixed(0)}</span>
      </div>
      <Progress value={score} className="h-1.5" />
    </div>
  );
}

export default function UploadTab({ projectId }: UploadTabProps) {
  const { toast } = useToast();
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadMutation = useUploadProjectZip();
  const { data: uploads = [], refetch: refetchUploads } = useListUploads(projectId);
  const { data: latest } = useGetLatestUpload(projectId);

  const handleFile = (file: File) => {
    if (!file.name.endsWith(".zip")) {
      toast({ title: "Invalid file", description: "Only .zip files are supported.", variant: "destructive" });
      return;
    }
    if (file.size > 100 * 1024 * 1024) {
      toast({ title: "File too large", description: "Max size: 100MB.", variant: "destructive" });
      return;
    }

    uploadMutation.mutate(
      { projectId, data: { file } },
      {
        onSuccess: () => {
          toast({ title: "Upload started", description: "AI analysis running in background." });
          refetchUploads();
        },
        onError: () => {
          toast({ title: "Upload failed", description: "Could not process ZIP.", variant: "destructive" });
        },
      }
    );
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [projectId]);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  };

  const uploadsList = Array.isArray(uploads) ? uploads : (uploads as any)?.data || [];

  return (
    <ScrollArea className="flex-1 p-4">
      <div className="space-y-4">
        {/* Drop Zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
            isDragging
              ? "border-primary bg-primary/10"
              : "border-border/50 hover:border-primary/50 hover:bg-card/50"
          } ${uploadMutation.isPending ? "pointer-events-none opacity-60" : ""}`}
        >
          <input ref={fileInputRef} type="file" accept=".zip" className="hidden" onChange={onFileChange} />
          {uploadMutation.isPending ? (
            <>
              <RefreshCw className="h-10 w-10 mx-auto mb-3 text-primary animate-spin" />
              <p className="font-mono text-sm text-primary">UPLOADING & ANALYZING...</p>
            </>
          ) : (
            <>
              <FileArchive className={`h-10 w-10 mx-auto mb-3 ${isDragging ? "text-primary" : "text-muted-foreground"}`} />
              <p className="font-mono text-sm font-semibold mb-1">DROP ZIP HERE</p>
              <p className="text-xs text-muted-foreground font-mono">or click to browse · max 100MB</p>
            </>
          )}
        </div>

        {/* Latest Analysis */}
        {latest && latest.status === "complete" && (
          <div className="space-y-3">
            <h4 className="font-mono text-xs font-semibold text-chart-4 flex items-center gap-2 border-b border-border/20 pb-2">
              <CheckCircle2 className="h-3 w-3" /> LATEST_ANALYSIS
            </h4>

            {/* Score Grid */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div className="bg-background/50 border border-border/50 p-3 rounded-lg text-center">
                <div className="text-[10px] font-mono text-muted-foreground mb-1">HEALTH SCORE</div>
                <div className={`text-2xl font-mono font-bold ${latest.health_score >= 70 ? "text-chart-4" : latest.health_score >= 45 ? "text-chart-2" : "text-destructive"}`}>
                  {latest.health_score.toFixed(0)}
                </div>
              </div>
              <div className="bg-background/50 border border-border/50 p-3 rounded-lg text-center">
                <div className="text-[10px] font-mono text-muted-foreground mb-1">FILES SCANNED</div>
                <div className="text-2xl font-mono font-bold text-foreground">{latest.file_count}</div>
              </div>
            </div>

            <div className="space-y-2 bg-background/30 border border-border/40 p-3 rounded-lg">
              <ScoreBar label="Architecture" score={latest.architecture_score} color="text-chart-2" />
              <ScoreBar label="Stability" score={latest.stability_score} color="text-chart-4" />
              <ScoreBar label="Debt Score" score={latest.debt_score} color="text-chart-1" />
            </div>

            {/* Languages & Frameworks */}
            {latest.languages.length > 0 && (
              <div className="flex flex-wrap gap-1">
                <Code2 className="h-3 w-3 text-muted-foreground mt-0.5" />
                {latest.languages.slice(0, 6).map((l: string) => (
                  <Badge key={l} variant="outline" className="font-mono text-[10px] py-0">{l}</Badge>
                ))}
              </div>
            )}
            {latest.frameworks.length > 0 && (
              <div className="flex flex-wrap gap-1">
                <Globe className="h-3 w-3 text-muted-foreground mt-0.5" />
                {latest.frameworks.slice(0, 6).map((f: string) => (
                  <Badge key={f} variant="outline" className="font-mono text-[10px] py-0 border-primary/30 text-primary">{f}</Badge>
                ))}
              </div>
            )}

            {/* Architecture Summary */}
            {latest.architecture_summary && (
              <p className="text-xs text-muted-foreground border border-border/30 p-2.5 rounded bg-background/30 leading-relaxed">
                {latest.architecture_summary}
              </p>
            )}

            {/* Issues */}
            {latest.security_issues.length > 0 && (
              <div className="space-y-1.5">
                <h5 className="font-mono text-[10px] text-destructive flex items-center gap-1.5">
                  <Shield className="h-3 w-3" /> SECURITY_ISSUES ({latest.security_issues.length})
                </h5>
                {latest.security_issues.slice(0, 4).map((issue: string, i: number) => (
                  <div key={i} className="text-xs p-2 bg-destructive/5 border border-destructive/10 rounded text-foreground/80">{issue}</div>
                ))}
              </div>
            )}

            {latest.issues.length > 0 && (
              <div className="space-y-1.5">
                <h5 className="font-mono text-[10px] text-chart-1 flex items-center gap-1.5">
                  <AlertTriangle className="h-3 w-3" /> CODE_ISSUES ({latest.issues.length})
                </h5>
                {latest.issues.slice(0, 4).map((issue: string, i: number) => (
                  <div key={i} className="text-xs p-2 bg-chart-1/5 border border-chart-1/10 rounded text-foreground/80">{issue}</div>
                ))}
              </div>
            )}

            {/* Recommendations */}
            {latest.recommendations.length > 0 && (
              <div className="space-y-1.5">
                <h5 className="font-mono text-[10px] text-chart-4 flex items-center gap-1.5">
                  <Zap className="h-3 w-3" /> RECOMMENDATIONS
                </h5>
                {latest.recommendations.slice(0, 4).map((r: string, i: number) => (
                  <div key={i} className="text-xs p-2 bg-chart-4/5 border border-chart-4/20 rounded text-foreground/90">{r}</div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Upload History */}
        {uploadsList.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-mono text-[10px] text-muted-foreground flex items-center gap-1.5 border-t border-border/20 pt-2">
              <Clock className="h-3 w-3" /> UPLOAD_HISTORY
            </h4>
            {uploadsList.slice(0, 5).map((u: any) => (
              <div key={u.id} className="flex items-center justify-between p-2 border border-border/30 rounded text-xs font-mono">
                <span className="text-muted-foreground truncate max-w-[180px]">{u.filename}</span>
                <div className="flex items-center gap-2 shrink-0">
                  {u.status === "complete" && <span className="text-chart-4">{u.health_score?.toFixed(0)}</span>}
                  <StatusBadge status={u.status} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
