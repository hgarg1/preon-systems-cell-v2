"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Cable, ChevronRight, LogOut, Plus, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { OrganismsProvider, useOrganisms } from "@/lib/organisms-context";
import { getCurrentUser, logout } from "@/lib/api";
import type { AuthUser, LifecycleState } from "@/lib/api";

const AUTH_PATHS = ["/login", "/signup", "/forgot-password", "/reset-password", "/verify-email", "/auth"];

function lifecycleDot(state: LifecycleState): string {
  switch (state) {
    case "active":     return "bg-green-500";
    case "hibernated": return "bg-yellow-500";
    case "degraded":   return "bg-orange-500";
    case "terminated": return "bg-red-500";
    default:           return "bg-neutral-500";
  }
}

function SidebarInner() {
  const { organisms, health, loading } = useOrganisms();
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [signingOut, setSigningOut] = useState(false);

  useEffect(() => {
    getCurrentUser().then(setUser).catch(() => setUser(null));
  }, []);

  async function handleSignOut() {
    setSigningOut(true);
    try {
      await logout();
    } finally {
      router.push("/login");
    }
  }

  return (
    <aside className="flex h-full w-56 flex-shrink-0 flex-col border-r border-white/10 bg-neutral-900">
      {/* Logo */}
      <div className="flex items-center gap-2.5 border-b border-white/10 px-4 py-4">
        <div className="flex h-6 w-6 items-center justify-center rounded bg-emerald-500/20 text-xs font-bold text-emerald-400">P</div>
        <span className="text-sm font-semibold text-white">Preon Runtime</span>
        {health ? (
          <Badge
            variant="outline"
            className={`ml-auto text-[10px] px-1.5 py-0 ${health.storage.degraded ? "border-amber-400/50 text-amber-400" : "border-emerald-400/30 text-emerald-400"}`}
          >
            {health.storage.mode}
          </Badge>
        ) : null}
      </div>

      {/* Organism list */}
      <div className="flex-1 overflow-y-auto px-2 py-3">
        <div className="mb-1.5 flex items-center justify-between px-2">
          <span className="text-[10px] font-semibold uppercase tracking-widest text-neutral-500">Organisms</span>
          <Link href="/">
            <Button variant="ghost" size="icon" className="h-5 w-5 text-neutral-500 hover:text-white">
              <Plus className="size-3" />
            </Button>
          </Link>
        </div>

        {loading ? (
          <div className="space-y-1 px-1">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-8 rounded-md bg-white/5 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="space-y-0.5">
            {organisms.map((o) => {
              const active = pathname.startsWith(`/organisms/${o.organism_id}`);
              return (
                <Link
                  key={o.organism_id}
                  href={`/organisms/${o.organism_id}/console`}
                  className={`group flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors ${
                    active ? "bg-white/10 text-white" : "text-neutral-400 hover:bg-white/5 hover:text-neutral-100"
                  }`}
                >
                  <span className={`size-1.5 flex-shrink-0 rounded-full ${lifecycleDot(o.lifecycle_state)}`} />
                  <span className="truncate">{o.identity_profile.name}</span>
                  {active ? <ChevronRight className="ml-auto size-3 text-neutral-500" /> : null}
                </Link>
              );
            })}
          </div>
        )}

        {/* Global navigation */}
        <div className="mt-3 border-t border-white/10 pt-3 space-y-0.5">
          {([
            { href: "/contracts", label: "Contracts", Icon: Cable },
            { href: "/growth",    label: "Growth",    Icon: Sparkles },
          ] as const).map(({ href, label, Icon }) => (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors ${
                pathname.startsWith(href)
                  ? "bg-white/10 text-white"
                  : "text-neutral-400 hover:bg-white/5 hover:text-neutral-100"
              }`}
            >
              <Icon className="size-4" />
              {label}
            </Link>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-white/10 px-2 py-2 space-y-1">
        {user && (
          <div className="px-2 py-1">
            <p className="truncate text-xs font-medium text-neutral-300">{user.name ?? user.email}</p>
            {user.name && <p className="truncate text-[10px] text-neutral-600">{user.email}</p>}
          </div>
        )}
        <button
          onClick={() => void handleSignOut()}
          disabled={signingOut}
          className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-neutral-500 hover:bg-white/5 hover:text-neutral-300 transition-colors disabled:opacity-40"
        >
          <LogOut className="size-4" />
          {signingOut ? "Signing out…" : "Sign out"}
        </button>
      </div>
    </aside>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuth = AUTH_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"));

  if (isAuth) return <>{children}</>;

  return (
    <OrganismsProvider>
      <div className="flex h-full">
        <SidebarInner />
        <main className="flex-1 overflow-auto bg-neutral-950">{children}</main>
      </div>
    </OrganismsProvider>
  );
}
