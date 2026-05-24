"use client";

import { Search } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { SeverityBadge } from "@/components/severity-badge";

export default function HistoryPage() {
  const { data } = useQuery({ queryKey: ["incidents"], queryFn: api.incidents });
  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Incident History</h1>
        <p className="mt-2 text-muted">Previous analyses, approvals, and remediation outcomes.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Search Incidents</CardTitle>
          <div className="mt-4 flex items-center gap-2 rounded-md border border-line bg-panel2 px-3">
            <Search size={16} className="text-muted" />
            <input className="h-10 flex-1 bg-transparent text-sm outline-none" placeholder="Filter by cluster, workload, severity" />
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {(data ?? []).map((incident) => (
            <div key={incident.id} className="grid gap-3 rounded-md border border-line bg-panel2 p-4 md:grid-cols-[1fr_auto_auto] md:items-center">
              <div>
                <div className="font-medium">{incident.namespace}/{incident.workload_name}</div>
                <div className="mt-1 text-sm text-muted">{incident.issue_type} / {new Date(incident.detected_at).toLocaleString()}</div>
              </div>
              <SeverityBadge severity={incident.severity} />
              <div className="text-sm text-muted">{incident.status}</div>
            </div>
          ))}
        </CardContent>
      </Card>
    </AppShell>
  );
}
