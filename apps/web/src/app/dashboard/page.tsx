"use client";

import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import { AppShell } from "@/components/app-shell";
import { MetricCard } from "@/components/metric-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { SeverityBadge } from "@/components/severity-badge";

export default function DashboardPage() {
  const { data } = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard });
  const chart = [
    { name: "Low", value: data?.severity.low ?? 0 },
    { name: "Medium", value: data?.severity.medium ?? 0 },
    { name: "High", value: data?.severity.high ?? 0 },
    { name: "Critical", value: data?.severity.critical ?? 0 }
  ];
  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Operations Dashboard</h1>
        <p className="mt-2 text-muted">AKS health, AI confidence, and remediation posture.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Connected clusters" value={data?.clusters ?? "—"} hint="Azure AKS only" />
        <MetricCard label="Total incidents" value={data?.incidents ?? "—"} hint="Last 30 days" />
        <MetricCard label="AI confidence" value={`${data?.confidence_average ?? 0}%`} hint="Mean analysis score" />
        <MetricCard label="Remediation success" value={`${data?.remediation_success_rate ?? 0}%`} hint="Approved actions" />
      </div>
      <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_.8fr]">
        <Card>
          <CardHeader><CardTitle>Severity Distribution</CardTitle></CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chart}>
                <XAxis dataKey="name" stroke="#8D99AA" />
                <Tooltip contentStyle={{ background: "#111722", border: "1px solid #222A38" }} />
                <Area type="monotone" dataKey="value" stroke="#5CE1E6" fill="#5CE1E6" fillOpacity={0.18} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Recent Failures</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {(data?.recent_incidents ?? []).map((incident) => (
              <div key={incident.id} className="rounded-md border border-line bg-panel2 p-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-medium">{incident.title}</div>
                  <SeverityBadge severity={incident.severity} />
                </div>
                <div className="mt-2 text-xs text-muted">{incident.cluster_name} · {incident.status}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
