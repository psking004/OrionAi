import React, { useState, useEffect, useRef } from "react";
import { 
  useGetProject, 
  useGetMessages, 
  useAddMessage, 
  useAnalyzeProjectStatus, 
  useGetNextSteps,
  getGetMessagesQueryKey,
  getGetProjectQueryKey
} from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Terminal, 
  Send, 
  Activity, 
  Map as MapIcon, 
  AlertTriangle, 
  CheckCircle2, 
  AlertCircle,
  HelpCircle,
  RefreshCw,
  Zap,
  ArrowRight
} from "lucide-react";
import { format } from "date-fns";
import { HealthGauge } from "@/components/health-gauge";
import { useToast } from "@/hooks/use-toast";

interface ProjectDetailProps {
  id: string;
}

function getProgressBadge(progress: string | undefined) {
  if (!progress) return null;
  
  const mapping: Record<string, { label: string, color: string, icon: React.ReactNode }> = {
    on_track: { label: "ON TRACK", color: "bg-chart-4/20 text-chart-4 border-chart-4/30", icon: <CheckCircle2 className="h-3 w-3 mr-1" /> },
    needs_attention: { label: "NEEDS ATTENTION", color: "bg-chart-2/20 text-chart-2 border-chart-2/30", icon: <AlertCircle className="h-3 w-3 mr-1" /> },
    at_risk: { label: "AT RISK", color: "bg-chart-1/20 text-chart-1 border-chart-1/30", icon: <AlertTriangle className="h-3 w-3 mr-1" /> },
    critical: { label: "CRITICAL", color: "bg-destructive/20 text-destructive border-destructive/30", icon: <AlertTriangle className="h-3 w-3 mr-1" /> },
  };

  const config = mapping[progress] || { label: progress.toUpperCase(), color: "bg-muted text-muted-foreground", icon: <HelpCircle className="h-3 w-3 mr-1" /> };

  return (
    <Badge variant="outline" className={`font-mono text-[10px] uppercase tracking-wider rounded-sm flex items-center ${config.color}`}>
      {config.icon}
      {config.label}
    </Badge>
  );
}

export default function ProjectDetail({ id }: ProjectDetailProps) {
  const projectId = parseInt(id, 10);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const scrollRef = useRef<HTMLDivElement>(null);
  
  const [messageText, setMessageText] = useState("");
  const [activeTab, setActiveTab] = useState("analysis");

  // Queries
  const { data: project, isLoading: isProjectLoading } = useGetProject(projectId, { 
    query: { enabled: !!projectId, queryKey: getGetProjectQueryKey(projectId) } 
  });
  
  const { data: messages, isLoading: isMessagesLoading } = useGetMessages(projectId, {
    query: { enabled: !!projectId, queryKey: getGetMessagesQueryKey(projectId) }
  });

  // Since we don't have separate endpoints to fetch JUST the status or roadmap without triggering generation,
  // we will store the generated results in local state. In a real app, these would be fetched via GET endpoints.
  const [status, setStatus] = useState<any>(null);
  const [nextSteps, setNextSteps] = useState<any>(null);

  // Mutations
  const addMessage = useAddMessage();
  const analyzeStatus = useAnalyzeProjectStatus();
  const getNextStepsMutation = useGetNextSteps();

  // Scroll to bottom of chat when messages change
  useEffect(() => {
    if (scrollRef.current) {
      const scrollContainer = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages]);

  const handleSendMessage = () => {
    if (!messageText.trim()) return;

    addMessage.mutate(
      { 
        projectId, 
        data: { role: "user", content: messageText } 
      },
      {
        onSuccess: () => {
          setMessageText("");
          queryClient.invalidateQueries({ queryKey: getGetMessagesQueryKey(projectId) });
        },
        onError: () => {
          toast({
            title: "Transmission Failed",
            description: "Could not send message to AI copilot.",
            variant: "destructive"
          });
        }
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleAnalyze = () => {
    analyzeStatus.mutate(
      { projectId },
      {
        onSuccess: (data) => {
          setStatus(data);
          setActiveTab("analysis");
          toast({ title: "Analysis Complete", description: "Health score updated." });
        },
        onError: () => {
          toast({ title: "Analysis Failed", variant: "destructive" });
        }
      }
    );
  };

  const handleGenerateRoadmap = () => {
    getNextStepsMutation.mutate(
      { projectId },
      {
        onSuccess: (data) => {
          setNextSteps(data);
          setActiveTab("roadmap");
          toast({ title: "Roadmap Generated", description: "Strategic path updated." });
        },
        onError: () => {
          toast({ title: "Generation Failed", variant: "destructive" });
        }
      }
    );
  };

  if (isProjectLoading) {
    return <div className="p-8"><Skeleton className="h-12 w-64 mb-8" /><Skeleton className="h-[600px] w-full" /></div>;
  }

  if (!project) {
    return <div className="p-8 text-center text-muted-foreground">Project not found.</div>;
  }

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-3.5rem)] overflow-hidden">
      {/* Header Area */}
      <div className="border-b border-border/40 bg-card/30 shrink-0">
        <div className="container max-w-screen-2xl p-4 md:p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight">{project.name}</h1>
              <Badge variant="outline" className="font-mono text-xs text-primary border-primary/30 bg-primary/5">
                {project.status.toUpperCase()}
              </Badge>
            </div>
            <p className="text-muted-foreground text-sm max-w-2xl">{project.description || "No mission brief."}</p>
          </div>
          
          <div className="flex items-center gap-4 shrink-0 bg-background/50 p-2 rounded-xl border border-border/50">
            {status ? (
              <>
                <div className="flex flex-col items-end mr-2">
                  <span className="text-[10px] font-mono text-muted-foreground mb-1">PULSE STATUS</span>
                  {getProgressBadge(status.progress)}
                </div>
                <HealthGauge score={status.health_score} size={48} strokeWidth={4} />
              </>
            ) : (
              <div className="flex items-center gap-3 px-2">
                <span className="text-xs font-mono text-muted-foreground">NO RECENT ANALYSIS</span>
                <HealthGauge score={0} size={48} strokeWidth={4} />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Area - Split View */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden container max-w-screen-2xl p-0 md:p-4 lg:p-6 gap-0 md:gap-4 lg:gap-6">
        
        {/* Left: Chat Terminal */}
        <Card className="flex-1 flex flex-col h-full rounded-none md:rounded-xl border-x-0 md:border border-border/50 bg-card/30 backdrop-blur-sm overflow-hidden">
          <CardHeader className="py-3 px-4 border-b border-border/40 flex flex-row items-center justify-between bg-card/50">
            <CardTitle className="text-sm font-mono flex items-center gap-2 text-muted-foreground">
              <Terminal className="h-4 w-4" />
              TERMINAL // {project.name.toUpperCase()}
            </CardTitle>
          </CardHeader>
          
          <CardContent className="flex-1 p-0 flex flex-col overflow-hidden">
            <ScrollArea className="flex-1 p-4" ref={scrollRef}>
              <div className="space-y-6">
                {isMessagesLoading ? (
                  <div className="space-y-4">
                    <Skeleton className="h-16 w-3/4" />
                    <Skeleton className="h-20 w-3/4 ml-auto" />
                    <Skeleton className="h-16 w-2/3" />
                  </div>
                ) : messages?.length === 0 ? (
                  <div className="text-center p-8 text-muted-foreground font-mono text-sm border border-dashed border-border/40 rounded-lg">
                    NO COMMS HISTORY FOUND.
                    <br />INITIATE PROTOCOL.
                  </div>
                ) : (
                  messages?.map((msg) => (
                    <div 
                      key={msg.id} 
                      className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'}`}
                    >
                      <div className="flex items-center gap-2 mb-1.5 px-1">
                        <span className={`text-[10px] font-mono tracking-widest ${msg.role === 'user' ? 'text-primary' : 'text-chart-2'}`}>
                          {msg.role.toUpperCase()}
                        </span>
                        <span className="text-[9px] font-mono text-muted-foreground/50">
                          {format(new Date(msg.timestamp), "HH:mm:ss")}
                        </span>
                      </div>
                      <div 
                        className={`p-3 rounded-lg text-sm font-mono leading-relaxed whitespace-pre-wrap ${
                          msg.role === 'user' 
                            ? 'bg-primary/10 border border-primary/20 text-foreground rounded-tr-sm' 
                            : msg.role === 'system'
                            ? 'bg-destructive/10 border border-destructive/20 text-destructive-foreground rounded-tl-sm'
                            : 'bg-card border border-border/50 text-card-foreground rounded-tl-sm shadow-sm'
                        }`}
                      >
                        {msg.content}
                      </div>
                    </div>
                  ))
                )}
                {/* Invisible element to pad bottom */}
                <div className="h-2" />
              </div>
            </ScrollArea>
            
            <div className="p-4 border-t border-border/40 bg-background/50">
              <div className="relative flex items-end gap-2">
                <Textarea
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Transmit to copilot... (Shift+Enter for newline)"
                  className="min-h-[60px] max-h-[200px] resize-none font-mono text-sm bg-card border-border/50 focus-visible:ring-primary/50 pr-12"
                  disabled={addMessage.isPending}
                  data-testid="input-chat"
                />
                <Button 
                  size="icon" 
                  className="absolute right-2 bottom-2 h-8 w-8 bg-primary/20 text-primary hover:bg-primary hover:text-primary-foreground border border-primary/30"
                  onClick={handleSendMessage}
                  disabled={addMessage.isPending || !messageText.trim()}
                  data-testid="button-send-chat"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Right: Insights Panel */}
        <Card className="flex-1 lg:max-w-[450px] xl:max-w-[500px] flex flex-col h-full rounded-none md:rounded-xl border-x-0 md:border border-t-0 md:border-t border-border/50 bg-card/30 backdrop-blur-sm overflow-hidden shrink-0">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
            <div className="px-4 py-2 border-b border-border/40 bg-card/50 flex items-center justify-between">
              <TabsList className="bg-background/50 border border-border/50">
                <TabsTrigger value="analysis" className="font-mono text-xs data-[state=active]:bg-card data-[state=active]:text-primary" data-testid="tab-analysis">
                  <Activity className="h-3 w-3 mr-2" />
                  ANALYSIS
                </TabsTrigger>
                <TabsTrigger value="roadmap" className="font-mono text-xs data-[state=active]:bg-card data-[state=active]:text-chart-2" data-testid="tab-roadmap">
                  <MapIcon className="h-3 w-3 mr-2" />
                  ROADMAP
                </TabsTrigger>
              </TabsList>
            </div>

            {/* Analysis Tab */}
            <TabsContent value="analysis" className="flex-1 overflow-hidden m-0 flex flex-col data-[state=active]:flex">
              <div className="p-4 border-b border-border/20 flex gap-2">
                <Button 
                  onClick={handleAnalyze} 
                  disabled={analyzeStatus.isPending} 
                  className="w-full font-mono text-xs bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20"
                  data-testid="button-analyze"
                >
                  {analyzeStatus.isPending ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Activity className="h-4 w-4 mr-2" />
                  )}
                  {analyzeStatus.isPending ? "COMPUTING..." : "RUN DIAGNOSTICS"}
                </Button>
              </div>

              <ScrollArea className="flex-1 p-4">
                {!status ? (
                  <div className="h-full flex flex-col items-center justify-center text-center p-8 opacity-50">
                    <Activity className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="font-mono text-sm text-muted-foreground">Run diagnostics to generate health report.</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-background/50 border border-border/50 p-4 rounded-lg flex flex-col items-center justify-center text-center">
                        <span className="text-[10px] font-mono text-muted-foreground mb-2">SYSTEM HEALTH</span>
                        <span className="text-3xl font-mono font-bold text-primary">{status.health_score}</span>
                      </div>
                      <div className="bg-background/50 border border-border/50 p-4 rounded-lg flex flex-col items-center justify-center text-center">
                        <span className="text-[10px] font-mono text-muted-foreground mb-2">CURRENT VECTOR</span>
                        {getProgressBadge(status.progress)}
                      </div>
                    </div>

                    {status.problems?.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-mono text-xs font-semibold text-destructive flex items-center">
                          <AlertTriangle className="h-3 w-3 mr-2" /> IDENTIFIED_ISSUES
                        </h4>
                        <ul className="space-y-2">
                          {status.problems.map((item: string, i: number) => (
                            <li key={i} className="text-sm bg-destructive/5 border border-destructive/10 p-2.5 rounded text-foreground/80 leading-snug">
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {status.stuck_points?.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-mono text-xs font-semibold text-chart-1 flex items-center">
                          <AlertCircle className="h-3 w-3 mr-2" /> BLOCKERS
                        </h4>
                        <ul className="space-y-2">
                          {status.stuck_points.map((item: string, i: number) => (
                            <li key={i} className="text-sm bg-chart-1/5 border border-chart-1/10 p-2.5 rounded text-foreground/80 leading-snug">
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {status.missing_features?.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-mono text-xs font-semibold text-muted-foreground flex items-center">
                          <HelpCircle className="h-3 w-3 mr-2" /> GAPS
                        </h4>
                        <ul className="space-y-2">
                          {status.missing_features.map((item: string, i: number) => (
                            <li key={i} className="text-sm border border-border/40 p-2.5 rounded text-muted-foreground leading-snug">
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {status.next_steps?.length > 0 && (
                      <div className="space-y-2 pt-2 border-t border-border/20">
                        <h4 className="font-mono text-xs font-semibold text-chart-4 flex items-center">
                          <Zap className="h-3 w-3 mr-2" /> TACTICAL_ACTIONS
                        </h4>
                        <ul className="space-y-2">
                          {status.next_steps.map((item: string, i: number) => (
                            <li key={i} className="text-sm bg-chart-4/5 border border-chart-4/20 p-2.5 rounded text-foreground/90 leading-snug flex items-start">
                              <ArrowRight className="h-3 w-3 mr-2 mt-1 text-chart-4 shrink-0" />
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </ScrollArea>
            </TabsContent>

            {/* Roadmap Tab */}
            <TabsContent value="roadmap" className="flex-1 overflow-hidden m-0 flex flex-col data-[state=active]:flex">
              <div className="p-4 border-b border-border/20 flex gap-2">
                <Button 
                  onClick={handleGenerateRoadmap} 
                  disabled={getNextStepsMutation.isPending} 
                  className="w-full font-mono text-xs bg-chart-2/10 text-chart-2 border border-chart-2/20 hover:bg-chart-2/20"
                  data-testid="button-generate-roadmap"
                >
                  {getNextStepsMutation.isPending ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <MapIcon className="h-4 w-4 mr-2" />
                  )}
                  {getNextStepsMutation.isPending ? "COMPILING..." : "GENERATE STRATEGY"}
                </Button>
              </div>

              <ScrollArea className="flex-1 p-4">
                {!nextSteps ? (
                  <div className="h-full flex flex-col items-center justify-center text-center p-8 opacity-50">
                    <MapIcon className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="font-mono text-sm text-muted-foreground">Generate strategy to view tactical roadmap.</p>
                  </div>
                ) : (
                  <div className="space-y-8">
                    {nextSteps.roadmap?.length > 0 && (
                      <div className="space-y-4">
                        <h4 className="font-mono text-xs font-semibold text-chart-2 tracking-widest border-b border-border/20 pb-2">STRATEGIC_VECTOR</h4>
                        <div className="relative pl-4 border-l border-border/50 space-y-6">
                          {nextSteps.roadmap.map((item: string, i: number) => (
                            <div key={i} className="relative">
                              <div className="absolute w-2 h-2 bg-chart-2 rounded-full -left-[21px] top-1.5 ring-4 ring-background" />
                              <p className="text-sm leading-relaxed">{item}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {nextSteps.steps?.length > 0 && (
                      <div className="space-y-4">
                        <h4 className="font-mono text-xs font-semibold text-chart-4 tracking-widest border-b border-border/20 pb-2">IMMEDIATE_EXECUTION</h4>
                        <div className="space-y-3">
                          {nextSteps.steps.map((item: string, i: number) => (
                            <div key={i} className="flex gap-3 bg-background/50 border border-border/50 p-3 rounded-md">
                              <div className="font-mono text-xs text-muted-foreground mt-0.5 w-6 shrink-0">
                                {(i + 1).toString().padStart(2, '0')}
                              </div>
                              <p className="text-sm flex-1">{item}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </Card>
      </div>
    </div>
  );
}
