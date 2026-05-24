import React from "react";
import { useAuth } from "@/lib/auth";
import { useGetMe } from "@workspace/api-client-react";
import { Button } from "@/components/ui/button";
import { LogOut, Activity, Briefcase } from "lucide-react";
import { Link } from "wouter";

export function Layout({ children }: { children: React.ReactNode }) {
  const { logout } = useAuth();
  const { data: user, isLoading } = useGetMe();

  return (
    <div className="min-h-[100dvh] flex flex-col bg-background text-foreground font-sans">
      <header className="sticky top-0 z-40 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 max-w-screen-2xl items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2 font-mono font-bold text-lg text-primary tracking-tight" data-testid="link-home">
              <Activity className="h-5 w-5" />
              AI_TEAMMATE
            </Link>
          </div>
          
          <div className="flex items-center gap-4">
            {isLoading ? (
              <div className="h-4 w-24 bg-muted animate-pulse rounded"></div>
            ) : (
              <span className="text-sm text-muted-foreground font-mono" data-testid="text-username">
                {user?.username || user?.email}
              </span>
            )}
            <Button variant="ghost" size="icon" onClick={logout} title="Log out" data-testid="button-logout">
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1 flex flex-col">
        {children}
      </main>
    </div>
  );
}
