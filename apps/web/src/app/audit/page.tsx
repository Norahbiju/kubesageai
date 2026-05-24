"use client";

import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function AuditLogsPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["audit-logs"], queryFn: api.auditLogs });
  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Audit Logs</h1>
        <p className="mt-2 text-muted">Security-sensitive actions, approvals, and integration events.</p>
      </div>
      <Card>
        <CardHeader><CardTitle>Recent Events</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <div className="h-48 animate-pulse rounded-md bg-white/5" /> : null}
          {isError ? <div className="rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">Audit logs could not be loaded.</div> : null}
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="text-muted">
                <tr>
                  <th className="border-b border-line py-3 pr-4">Time</th>
                  <th className="border-b border-line py-3 pr-4">Action</th>
                  <th className="border-b border-line py-3 pr-4">Resource</th>
                  <th className="border-b border-line py-3 pr-4">IP</th>
                </tr>
              </thead>
              <tbody>
                {(data ?? []).map((item) => (
                  <tr key={String(item.id)}>
                    <td className="border-b border-line/70 py-3 pr-4">{new Date(String(item.created_at)).toLocaleString()}</td>
                    <td className="border-b border-line/70 py-3 pr-4">{String(item.action)}</td>
                    <td className="border-b border-line/70 py-3 pr-4">{String(item.resource_type)} / {String(item.resource_id)}</td>
                    <td className="border-b border-line/70 py-3 pr-4">{String(item.ip_address ?? "")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </AppShell>
  );
}
