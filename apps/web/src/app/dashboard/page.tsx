"use client";

import { useQuery } from "@tanstack/react-query";
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
  const chart = ["low", "medium", "high", "critical"].map((name) => ({ name, value: severity[name] ?? 0 }));

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Operations Dashboard</h1>
        <p className="mt-2 text-muted">AKS health, incident posture, and remediation activity.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Connected clusters" value={clusters?.length ?? "-"} hint="Azure AKS only" />
        <MetricCard label="Total incidents" value={incidents?.length ?? "-"} hint="Detected by scans" />
        <MetricCard label="AI analysis" value="OpenAI" hint="Structured JSON" />
        <MetricCard label="Remediation" value="Approval" hint="SDK-only execution" />
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
          <CardHeader><CardTitle>Recent Incidents</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {(incidents ?? []).slice(0, 6).map((incident) => (
              <div key={incident.id} className="rounded-md border border-line bg-panel2 p-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-medium">{incident.namespace}/{incident.workload_name}</div>
                  <SeverityBadge severity={incident.severity} />
                </div>
                <div className="mt-2 text-xs text-muted">{incident.issue_type} / {incident.status}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
