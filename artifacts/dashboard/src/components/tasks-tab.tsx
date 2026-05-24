import React, { useState } from "react";
import { useGenerateTasks } from "@workspace/api-client-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";
import {
  ListChecks, RefreshCw, Server, Globe, TestTube, Rocket,
  Clock, Flag, ChevronRight,
} from "lucide-react";

interface TasksTabProps {
  projectId: number;
}

const PRIORITY_STYLES: Record<string, string> = {
  critical: "text-destructive border-destructive/30 bg-destructive/10",
  high: "text-chart-1 border-chart-1/30 bg-chart-1/10",
  medium: "text-chart-2 border-chart-2/30 bg-chart-2/10",
  low: "text-muted-foreground border-border bg-background/50",
};

const SECTION_CONFIG = [
  { key: "backend_tasks", label: "BACKEND", icon: Server, color: "text-chart-2" },
  { key: "frontend_tasks", label: "FRONTEND", icon: Globe, color: "text-primary" },
  { key: "testing_tasks", label: "TESTING", icon: TestTube, color: "text-chart-4" },
  { key: "deployment_tasks", label: "DEPLOYMENT", icon: Rocket, color: "text-chart-3" },
];

function TaskCard({ task }: { task: any }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-border/30 rounded bg-card/30">
      <button
        className="w-full flex items-center gap-2 p-2.5 text-left hover:bg-white/5 transition-colors"
        onClick={() => setOpen(!open)}
      >
        <span className="font-mono text-[10px] text-muted-foreground/50 w-14 shrink-0">{task.id}</span>
        <span className="flex-1 text-xs leading-snug text-left">{task.title}</span>
        <div className="flex items-center gap-1.5 shrink-0">
          <Badge variant="outline" className={`font-mono text-[10px] py-0 ${PRIORITY_STYLES[task.priority] || PRIORITY_STYLES.low}`}>
            {task.priority}
          </Badge>
          <span className="font-mono text-[10px] text-muted-foreground">{task.estimated_hours}h</span>
          {open ? <ChevronRight className="h-3 w-3 rotate-90 shrink-0" /> : <ChevronRight className="h-3 w-3 shrink-0" />}
        </div>
      </button>
      {open && (
        <div className="px-3 pb-3 border-t border-border/20 pt-2 space-y-2">
          <p className="text-xs text-muted-foreground leading-relaxed">{task.description}</p>
          {task.dependencies?.length > 0 && (
            <div className="flex items-center gap-1 flex-wrap">
              <span className="text-[10px] font-mono text-muted-foreground">Deps:</span>
              {task.dependencies.map((d: string) => (
                <Badge key={d} variant="outline" className="font-mono text-[10px] py-0">{d}</Badge>
              ))}
            </div>
          )}
          <div className="flex items-center gap-2">
            <Flag className="h-3 w-3 text-muted-foreground" />
            <span className="text-[10px] font-mono text-muted-foreground">{task.milestone}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default function TasksTab({ projectId }: TasksTabProps) {
  const { toast } = useToast();
  const [prompt, setPrompt] = useState("");
  const [taskResult, setTaskResult] = useState<any>(null);
  const [activeSection, setActiveSection] = useState("backend_tasks");

  const generateMutation = useGenerateTasks();

  const handleGenerate = () => {
    if (!prompt.trim()) {
      toast({ title: "No prompt", description: "Describe the feature to build.", variant: "destructive" });
      return;
    }
    generateMutation.mutate(
      { projectId, data: { prompt: prompt.trim() } },
      {
        onSuccess: (data: any) => {
          setTaskResult(data);
          toast({ title: "Tasks Generated", description: `${data.total_estimated_hours}h across ${data.recommended_sprint_weeks} sprint(s).` });
        },
        onError: () => {
          toast({ title: "Generation Failed", variant: "destructive" });
        },
      }
    );
  };

  const handleClear = () => {
    setPrompt("");
    setTaskResult(null);
  };

  const currentTasks = taskResult?.[activeSection] || [];

  return (
    <ScrollArea className="flex-1 p-4">
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <ListChecks className="h-4 w-4 text-muted-foreground" />
          <span className="font-mono text-xs font-semibold">TASK BREAKDOWN ENGINE</span>
        </div>

        {/* Prompt Input */}
        <div className="space-y-2">
          <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider">
            Describe the feature or epic to break down
          </label>
          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. Build a real-time notification system with WebSockets and email fallback"
            className="font-mono text-xs bg-background border-border/50 min-h-[80px] max-h-[150px] resize-none"
            disabled={generateMutation.isPending}
          />
        </div>

        <div className="flex gap-2">
          <Button
            className="flex-1 font-mono text-xs bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20"
            onClick={handleGenerate}
            disabled={generateMutation.isPending || !prompt.trim()}
          >
            {generateMutation.isPending ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <ListChecks className="h-4 w-4 mr-2" />
            )}
            {generateMutation.isPending ? "GENERATING..." : "GENERATE TASKS"}
          </Button>
          {taskResult && (
            <Button size="sm" variant="outline" className="font-mono text-xs" onClick={handleClear}>CLEAR</Button>
          )}
        </div>

        {/* Results */}
        {taskResult && (
          <div className="space-y-3 border-t border-border/20 pt-3">
            {/* Summary */}
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-background/50 border border-border/40 rounded-lg p-2.5 text-center">
                <Clock className="h-3.5 w-3.5 mx-auto mb-1 text-muted-foreground" />
                <div className="font-mono text-sm font-bold">{taskResult.total_estimated_hours}h</div>
                <div className="text-[10px] font-mono text-muted-foreground">TOTAL EFFORT</div>
              </div>
              <div className="bg-background/50 border border-border/40 rounded-lg p-2.5 text-center">
                <Flag className="h-3.5 w-3.5 mx-auto mb-1 text-muted-foreground" />
                <div className="font-mono text-sm font-bold">{taskResult.recommended_sprint_weeks}</div>
                <div className="text-[10px] font-mono text-muted-foreground">SPRINT WEEKS</div>
              </div>
            </div>

            {/* Milestones */}
            {taskResult.milestones?.length > 0 && (
              <div className="space-y-1.5">
                <h5 className="font-mono text-[10px] text-chart-2">MILESTONES</h5>
                {taskResult.milestones.map((m: string, i: number) => (
                  <div key={i} className="flex items-start gap-2 text-xs">
                    <div className="h-1.5 w-1.5 rounded-full bg-chart-2 mt-1.5 shrink-0" />
                    {m}
                  </div>
                ))}
              </div>
            )}

            {/* Section Tabs */}
            <div className="flex gap-1 border-b border-border/20 pb-2 overflow-x-auto">
              {SECTION_CONFIG.map(({ key, label, icon: Icon, color }) => {
                const count = taskResult[key]?.length || 0;
                return (
                  <button
                    key={key}
                    onClick={() => setActiveSection(key)}
                    className={`flex items-center gap-1 px-2 py-1 rounded font-mono text-[10px] whitespace-nowrap transition-colors ${
                      activeSection === key ? "bg-card border border-border/50 " + color : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <Icon className="h-2.5 w-2.5" />
                    {label} ({count})
                  </button>
                );
              })}
            </div>

            {/* Task List */}
            <div className="space-y-1.5">
              {currentTasks.map((task: any) => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!taskResult && !generateMutation.isPending && (
          <div className="text-center p-6 border border-dashed border-border/30 rounded-lg opacity-40">
            <ListChecks className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
            <p className="font-mono text-xs text-muted-foreground">Describe a feature and get a complete task breakdown with backend, frontend, testing, and deployment tasks.</p>
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
