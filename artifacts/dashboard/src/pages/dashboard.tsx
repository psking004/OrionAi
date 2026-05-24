import React, { useState } from "react";
import { Link } from "wouter";
import { useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import {
  useListProjects,
  useCreateProject,
  useDeleteProject,
  getListProjectsQueryKey,
  ProjectInputStatus,
} from "@workspace/api-client-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Trash2, Clock, Code, Activity, Search } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";

const createProjectSchema = z.object({
  name: z.string().min(1, "Name is required").max(200),
  description: z.string().optional(),
  tech_stack: z.string().optional(),
  status: z.enum(["active", "paused", "completed", "archived"]).default("active"),
});

type CreateProjectValues = z.infer<typeof createProjectSchema>;

function getStatusColor(status: string) {
  switch (status) {
    case "active":
      return "bg-chart-2/20 text-chart-2 border-chart-2/30";
    case "paused":
      return "bg-chart-1/20 text-chart-1 border-chart-1/30";
    case "completed":
      return "bg-chart-4/20 text-chart-4 border-chart-4/30";
    case "archived":
      return "bg-muted text-muted-foreground border-border";
    default:
      return "bg-secondary text-secondary-foreground border-border";
  }
}

export default function Dashboard() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const { data: projects, isLoading } = useListProjects();
  const createProject = useCreateProject();
  const deleteProject = useDeleteProject();

  const form = useForm<CreateProjectValues>({
    resolver: zodResolver(createProjectSchema),
    defaultValues: {
      name: "",
      description: "",
      tech_stack: "",
      status: "active",
    },
  });

  const onSubmit = (data: CreateProjectValues) => {
    createProject.mutate(
      { data: data as any }, // Type casting to match ProjectInput
      {
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: getListProjectsQueryKey() });
          setIsCreateOpen(false);
          form.reset();
          toast({
            title: "Project Initialized",
            description: `Tracking pulse for ${data.name}.`,
          });
        },
        onError: () => {
          toast({
            title: "Error",
            description: "Failed to initialize project.",
            variant: "destructive",
          });
        },
      }
    );
  };

  const handleDelete = (id: number, name: string, e: React.MouseEvent) => {
    e.preventDefault(); // Prevent navigating to the project
    if (confirm(`Are you sure you want to terminate ${name}? This action cannot be undone.`)) {
      deleteProject.mutate(
        { projectId: id },
        {
          onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: getListProjectsQueryKey() });
            toast({
              title: "Project Terminated",
              description: `${name} has been removed from the grid.`,
            });
          },
        }
      );
    }
  };

  const filteredProjects = projects?.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (p.tech_stack && p.tech_stack.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="flex-1 p-6 md:p-8 xl:p-10 max-w-7xl mx-auto w-full space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Ops Grid</h1>
          <p className="text-muted-foreground mt-1">Monitor and manage your active missions.</p>
        </div>
        
        <div className="flex w-full md:w-auto items-center gap-2">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Filter grid..."
              className="pl-9 bg-background/50 border-border/50 font-mono text-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              data-testid="input-search"
            />
          </div>
          
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button data-testid="button-new-project">
                <Plus className="h-4 w-4 mr-2" />
                NEW PROJECT
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px] border-primary/20 shadow-[0_0_40px_rgba(249,115,22,0.1)]">
              <DialogHeader>
                <DialogTitle>Initialize Project</DialogTitle>
                <DialogDescription>
                  Define parameters for the new mission tracking system.
                </DialogDescription>
              </DialogHeader>
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 pt-4">
                  <FormField
                    control={form.control}
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="font-mono text-xs">PROJECT_NAME</FormLabel>
                        <FormControl>
                          <Input placeholder="e.g. Apollo" {...field} className="font-mono" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="description"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="font-mono text-xs">MISSION_BRIEF</FormLabel>
                        <FormControl>
                          <Textarea 
                            placeholder="Describe the objective..." 
                            {...field} 
                            className="resize-none font-mono text-sm h-20"
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="tech_stack"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="font-mono text-xs">TECH_STACK</FormLabel>
                        <FormControl>
                          <Input placeholder="e.g. React, Node.js, Postgres" {...field} className="font-mono" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="status"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="font-mono text-xs">CURRENT_STATUS</FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger className="font-mono text-sm">
                              <SelectValue placeholder="Select status" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="active">ACTIVE</SelectItem>
                            <SelectItem value="paused">PAUSED</SelectItem>
                            <SelectItem value="completed">COMPLETED</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <DialogFooter className="pt-4">
                    <Button type="submit" disabled={createProject.isPending} data-testid="button-submit-project">
                      INITIALIZE
                    </Button>
                  </DialogFooter>
                </form>
              </Form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="h-64 border-border/50">
              <CardHeader className="space-y-2">
                <Skeleton className="h-5 w-1/2" />
                <Skeleton className="h-4 w-1/3" />
              </CardHeader>
              <CardContent className="space-y-4">
                <Skeleton className="h-16 w-full" />
                <div className="flex gap-2">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-4 w-16" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredProjects?.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center border border-dashed border-border/50 rounded-xl bg-card/20">
          <Activity className="h-10 w-10 text-muted-foreground mb-4 opacity-50" />
          <h3 className="text-lg font-medium text-foreground mb-2">Grid Empty</h3>
          <p className="text-sm text-muted-foreground mb-6 max-w-sm">
            {searchQuery 
              ? "No projects match your current filter parameters." 
              : "No active missions found. Initialize a new project to begin tracking."}
          </p>
          {!searchQuery && (
            <Button onClick={() => setIsCreateOpen(true)} variant="outline">
              INITIALIZE FIRST PROJECT
            </Button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-max">
          {filteredProjects?.map((project) => (
            <Link key={project.id} href={`/projects/${project.id}`}>
              <Card className="group relative h-full flex flex-col cursor-pointer overflow-hidden border-border/40 hover:border-primary/50 transition-all duration-300 hover:shadow-[0_0_20px_rgba(249,115,22,0.05)] bg-card/40 hover:bg-card/80 backdrop-blur-sm" data-testid={`project-card-${project.id}`}>
                <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-primary/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                
                <CardHeader className="pb-3 flex flex-row items-start justify-between space-y-0">
                  <div className="space-y-1.5 overflow-hidden pr-2">
                    <CardTitle className="truncate font-bold tracking-tight text-xl group-hover:text-primary transition-colors">
                      {project.name}
                    </CardTitle>
                    <Badge variant="outline" className={`font-mono text-[10px] uppercase tracking-wider rounded-sm ${getStatusColor(project.status)}`}>
                      {project.status}
                    </Badge>
                  </div>
                  
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8 text-muted-foreground opacity-0 group-hover:opacity-100 hover:text-destructive hover:bg-destructive/10 -mt-1 -mr-2 transition-all shrink-0 z-10"
                    onClick={(e) => handleDelete(project.id, project.name, e)}
                    data-testid={`button-delete-${project.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </CardHeader>
                
                <CardContent className="pb-4 flex-1">
                  <p className="text-sm text-muted-foreground line-clamp-3 mb-4 leading-relaxed">
                    {project.description || "No mission brief provided."}
                  </p>
                  
                  {project.tech_stack && (
                    <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground mt-auto">
                      <Code className="h-3 w-3 shrink-0" />
                      <span className="truncate">{project.tech_stack}</span>
                    </div>
                  )}
                </CardContent>
                
                <CardFooter className="pt-0 text-xs text-muted-foreground/60 font-mono border-t border-border/20 mt-4 pt-3 flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Clock className="h-3 w-3" />
                    <span>UPDATED {format(new Date(project.updated_at), "MMM d, yyyy")}</span>
                  </div>
                </CardFooter>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
