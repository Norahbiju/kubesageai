"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowDownRight, ArrowUpRight, CheckCircle2, Clock3, Cpu, ShieldCheck } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import { AppShell } from "@/components/app-shell";
import { MetricCard } from "@/components/metric-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SeverityBadge } from "@/components/severity-badge";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const { data: clusters } = useQuery({ queryKey: ["clusters"], queryFn: api.clusters });
  const { data: incidents } = useQuery({ queryKey: ["incidents"], queryFn: api.incidents });
  const severity = (incidents ?? []).reduce<Record<string, number>>((acc, incident) => {
    acc[incident.severity] = (acc[incident.severity] ?? 0) + 1;
    return acc;
  }, {});
  const chart = ["Low", "Medium", "High", "Critical"].map((name) => ({ name, value: severity[name.toLowerCase()] ?? 0 }));
  const recent = (incidents ?? []).slice(0, 6);

  return (
    <AppShell>
      <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="text-sm text-muted">Overview</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-normal">Dashboard</h1>
        </div>
        <div className="flex items-center gap-2 rounded-full bg-black/20 px-4 py-2 text-sm text-muted">
          <Clock3 size={15} />
          Live AKS posture
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-[1fr_1fr_.9fr]">
        <MetricCard label="Connected clusters" value={clusters?.length ?? "-"} hint="Azure AKS only" tone="green" />
        <MetricCard label="Total incidents" value={incidents?.length ?? "-"} hint="Detected by scans" tone="blue" />
        <Card className="bg-[#29263f]">
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted">Remediation</div>
              <ShieldCheck className="text-lime" size={18} />
            </div>
            <div className="mt-3 text-3xl font-semibold">Approval</div>
            <div className="mt-2 text-xs text-muted">SDK-only execution</div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[1.15fr_.85fr]">
        <Card className="bg-[#19172a]">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Incidents</CardTitle>
            <span className="rounded-full bg-white/5 px-3 py-1 text-xs text-muted">Latest</span>
          </CardHeader>
          <CardContent className="space-y-3">
            {recent.length ? (
              recent.map((incident, index) => {
                const positive = incident.severity === "low" || incident.status === "resolved";
                return (
                  <div key={incident.id} className="flex items-center gap-3 rounded-2xl bg-white/[0.035] p-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-panel2 text-sm font-semibold">
                      {index + 1}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium">{incident.namespace}/{incident.workload_name}</div>
                      <div className="mt-1 truncate text-xs text-muted">{incident.issue_type}</div>
                    </div>
                    <SeverityBadge severity={incident.severity} />
                    <div className={positive ? "text-lime" : "text-rose"}>
                      {positive ? <ArrowUpRight size={17} /> : <ArrowDownRight size={17} />}
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="rounded-2xl bg-white/[0.035] p-8 text-center text-sm text-muted">No incidents detected</div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-5">
          <Card className="bg-[#29263f]">
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-muted">AI analysis</div>
                  <div className="mt-2 text-2xl font-semibold">OpenAI</div>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-lime/15 text-lime">
                  <Cpu size={22} />
                </div>
              </div>
              <div className="mt-5 flex items-center gap-2 text-xs text-muted">
                <CheckCircle2 size={15} className="text-lime" />
                Structured JSON analysis ready
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#19172a]">
            <CardHeader><CardTitle>Saved This Month</CardTitle></CardHeader>
            <CardContent className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chart}>
                  <XAxis dataKey="name" stroke="#9FA5B8" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#211F35", border: "1px solid rgba(255,255,255,.10)", borderRadius: "14px" }} />
                  <Area type="monotone" dataKey="value" stroke="#32D583" fill="#32D583" fillOpacity={0.16} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="mt-5">
        <Card className="bg-[#19172a]">
          <CardHeader><CardTitle>Severity Distribution</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chart}>
                <XAxis dataKey="name" stroke="#9FA5B8" tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: "#211F35", border: "1px solid rgba(255,255,255,.10)", borderRadius: "14px" }} />
                <Area type="monotone" dataKey="value" stroke="#4DA3FF" fill="#4DA3FF" fillOpacity={0.14} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
