import React from "react";
import { useAuth } from "@/lib/auth";
import { useGetMe } from "@workspace/api-client-react";
import { Button } from "@/components/ui/button";
import { LogOut, Activity, LayoutDashboard, Briefcase, CreditCard } from "lucide-react";
import { Link, useLocation } from "wouter";
import { CreditsWidget } from "@/components/credits-widget";

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  const [location] = useLocation();
  const isActive = location === href;
  return (
    <Link
      href={href}
      className={`flex items-center gap-1.5 font-mono text-xs px-2 py-1 rounded transition-colors ${
        isActive
          ? "text-primary bg-primary/10"
          : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
      }`}
    >
      {children}
    </Link>
  );
}

export function Layout({ children }: { children: React.ReactNode }) {
  const { logout } = useAuth();
  const { data: user, isLoading } = useGetMe();

  return (
    <div className="min-h-[100dvh] flex flex-col bg-background text-foreground font-sans">
      <header className="sticky top-0 z-40 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 max-w-screen-2xl items-center justify-between gap-4">
          <div className="flex items-center gap-1">
            <Link href="/" className="flex items-center gap-2 font-mono font-bold text-base text-primary tracking-tight mr-3" data-testid="link-home">
              <Activity className="h-5 w-5" />
              <span className="hidden sm:inline">ORION<span className="text-foreground">OS</span></span>
            </Link>
            <nav className="flex items-center gap-0.5">
              <NavLink href="/overview">
                <LayoutDashboard className="h-3.5 w-3.5" />
                <span className="hidden md:inline">OVERVIEW</span>
              </NavLink>
              <NavLink href="/">
                <Briefcase className="h-3.5 w-3.5" />
                <span className="hidden md:inline">PROJECTS</span>
              </NavLink>
              <NavLink href="/billing">
                <CreditCard className="h-3.5 w-3.5" />
                <span className="hidden md:inline">BILLING</span>
              </NavLink>
            </nav>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <CreditsWidget />
            {isLoading ? (
              <div className="h-4 w-20 bg-muted animate-pulse rounded" />
            ) : (
              <span className="text-xs text-muted-foreground font-mono hidden sm:block" data-testid="text-username">
                {user?.username || user?.email}
              </span>
            )}
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={logout} title="Log out" data-testid="button-logout">
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
