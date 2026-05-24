import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Link, useLocation } from "wouter";
import { useRegister } from "@workspace/api-client-react";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Loader2 } from "lucide-react";

const registerSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
  username: z.string().min(3, { message: "Username must be at least 3 characters" }).max(50),
  password: z.string().min(8, { message: "Password must be at least 8 characters" }),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function Register() {
  const [, setLocation] = useLocation();
  const { login: setAuthToken } = useAuth();
  
  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      username: "",
      password: "",
    },
  });

  const registerMutation = useRegister();

  const onSubmit = (data: RegisterFormValues) => {
    registerMutation.mutate(
      { data },
      {
        onSuccess: (response) => {
          setAuthToken(response.access_token);
          setLocation("/");
        },
        onError: (error: any) => {
          form.setError("root", {
            message: error.data?.detail || "Registration failed. Please try again.",
          });
        },
      }
    );
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4 selection:bg-primary selection:text-primary-foreground">
      <div className="absolute inset-0 z-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary/10 via-background to-background pointer-events-none" />
      
      <div className="z-10 w-full max-w-md space-y-8">
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="w-12 h-12 rounded-lg bg-primary/20 flex items-center justify-center border border-primary/50 text-primary mb-4 shadow-[0_0_15px_rgba(249,115,22,0.5)]">
            <Activity className="h-6 w-6" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Request Access</h1>
          <p className="text-muted-foreground">Register for the AI operations center</p>
        </div>

        <Card className="border-border/50 bg-card/50 backdrop-blur-xl shadow-2xl">
          <CardHeader>
            <CardTitle className="text-xl">New Clearance</CardTitle>
            <CardDescription>Enter your details to create an account</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-muted-foreground font-mono text-xs uppercase tracking-wider">EMAIL_ADDRESS</FormLabel>
                      <FormControl>
                        <Input 
                          placeholder="operator@system.io" 
                          {...field} 
                          className="bg-background/50 font-mono text-sm border-border/50 focus-visible:ring-primary/50"
                          data-testid="input-email"
                        />
                      </FormControl>
                      <FormMessage className="text-destructive font-mono text-xs" />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="username"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-muted-foreground font-mono text-xs uppercase tracking-wider">OPERATIVE_ID</FormLabel>
                      <FormControl>
                        <Input 
                          placeholder="ghost_protocol" 
                          {...field} 
                          className="bg-background/50 font-mono text-sm border-border/50 focus-visible:ring-primary/50"
                          data-testid="input-username"
                        />
                      </FormControl>
                      <FormMessage className="text-destructive font-mono text-xs" />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-muted-foreground font-mono text-xs uppercase tracking-wider">NEW_ACCESS_KEY</FormLabel>
                      <FormControl>
                        <Input 
                          type="password" 
                          placeholder="••••••••" 
                          {...field} 
                          className="bg-background/50 font-mono text-sm border-border/50 focus-visible:ring-primary/50"
                          data-testid="input-password"
                        />
                      </FormControl>
                      <FormMessage className="text-destructive font-mono text-xs" />
                    </FormItem>
                  )}
                />

                {form.formState.errors.root && (
                  <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md text-destructive text-sm font-mono" data-testid="error-message">
                    {form.formState.errors.root.message}
                  </div>
                )}

                <Button 
                  type="submit" 
                  className="w-full font-mono uppercase tracking-widest text-xs font-bold"
                  disabled={registerMutation.isPending}
                  data-testid="button-submit-register"
                >
                  {registerMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ESTABLISHING_LINK...
                    </>
                  ) : (
                    "GRANT CLEARANCE"
                  )}
                </Button>
              </form>
            </Form>
          </CardContent>
        </Card>

        <p className="text-center text-sm text-muted-foreground">
          Already have clearance?{" "}
          <Link href="/login" className="text-primary hover:underline hover:text-primary-border font-medium transition-colors" data-testid="link-login">
            Authenticate
          </Link>
        </p>
      </div>
    </div>
  );
}
