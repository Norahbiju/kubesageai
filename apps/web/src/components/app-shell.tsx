"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Route } from "next";
import type { ReactNode } from "react";
import { Activity, Bell, Bot, Cloud, FileClock, History, LayoutDashboard, LogOut, Settings, Server, ShieldCheck, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

const nav: Array<{ href: Route; label: string; icon: LucideIcon }> = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/azure", label: "Azure", icon: Cloud },
  { href: "/subscriptions", label: "Subscriptions", icon: Cloud },
  { href: "/clusters", label: "Clusters", icon: Server },
  { href: "/analysis", label: "Analysis", icon: Bot },
  { href: "/remediation", label: "Remediation", icon: ShieldCheck },
  { href: "/history", label: "History", icon: History },
  { href: "/audit", label: "Audit Logs", icon: FileClock },
  { href: "/settings", label: "Settings", icon: Settings }
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="min-h-screen bg-background px-4 py-5 text-text sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-2.5rem)] max-w-7xl overflow-hidden rounded-[28px] border border-white/10 bg-[#1d1a30]/92 shadow-glow">
        <aside className="hidden w-64 shrink-0 border-r border-white/10 bg-[#1a172b] lg:flex lg:flex-col">
          <div className="flex h-20 items-center gap-3 px-5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-lime text-[#08140e]">
              <Activity size={18} />
            </div>
            <div>
              <div className="font-semibold">KubeSage</div>
              <div className="text-xs text-muted">AKS copilot</div>
            </div>
          </div>
          <nav className="flex-1 space-y-1 px-3">
            {nav.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-xl px-3 py-3 text-sm text-muted transition hover:bg-white/[0.07] hover:text-text",
                    active && "bg-lime/15 text-lime"
                  )}
                >
                  <item.icon size={17} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="p-3">
            <Link className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm text-muted hover:bg-white/[0.07] hover:text-text" href="/login">
              <LogOut size={17} />
              Logout
            </Link>
          </div>
        </aside>
        <main className="min-w-0 flex-1 bg-[#201d33]">
          <header className="flex h-20 items-center justify-between border-b border-white/10 px-5 sm:px-7">
            <div className="lg:hidden">
              <div className="font-semibold">KubeSage</div>
              <div className="text-xs text-muted">AKS copilot</div>
            </div>
            <div className="hidden max-w-xs flex-1 rounded-full bg-black/20 px-4 py-2 text-sm text-muted lg:block">
              Search clusters, incidents, analysis
            </div>
            <div className="flex items-center gap-3">
              <button className="flex h-10 w-10 items-center justify-center rounded-full bg-black/20 text-muted transition hover:text-text" type="button">
                <Bell size={17} />
              </button>
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-amber to-rose text-sm font-semibold text-black">
                KS
              </div>
            </div>
          </header>
          <div className="soft-scroll min-h-[calc(100vh-7.5rem)] overflow-y-auto px-5 py-6 sm:px-7">{children}</div>
        </main>
      </div>
    </div>
  );
}
