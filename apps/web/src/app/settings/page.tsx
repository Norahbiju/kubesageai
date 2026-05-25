"use client";

import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const me = useQuery({ queryKey: ["me"], queryFn: api.me, retry: false });
  const connectivity = useQuery({ queryKey: ["azure-connectivity"], queryFn: api.connectivityCheck, retry: false });

  async function logout() {
    await api.logout();
    window.location.href = "/login";
  }

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Settings</h1>
        <p className="mt-2 text-muted">Signed-in account and Azure connectivity.</p>
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Signed-in User</CardTitle></CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="rounded-2xl border border-line bg-panel2 p-4">
              <div className="text-muted">Email</div>
              <div className="mt-1 font-medium">{me.data?.email ?? "Unknown"}</div>
            </div>
            <div className="rounded-2xl border border-line bg-panel2 p-4">
              <div className="text-muted">Azure tenant ID</div>
              <div className="mt-1 break-all font-medium">{me.data?.tenant_id ?? "Unknown"}</div>
            </div>
            <Button variant="secondary" onClick={logout}>Logout</Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Azure Connectivity</CardTitle></CardHeader>
          <CardContent className="space-y-4 text-sm">
            {connectivity.isLoading ? <div className="h-24 animate-pulse rounded-2xl bg-white/5" /> : null}
            {connectivity.data ? (
              <div className="rounded-2xl border border-line bg-panel2 p-4">
                <div className="font-medium text-lime">Connected</div>
                <div className="mt-2 text-muted">Subscriptions visible to this user: {connectivity.data.subscription_count}</div>
              </div>
            ) : null}
            {connectivity.isError ? (
              <div className="rounded-2xl border border-rose/40 bg-rose/10 p-4 text-rose">
                Azure login is required, or your Azure session expired. Please login again.
              </div>
            ) : null}
            <Button onClick={() => { window.location.href = api.loginUrl(); }}>Reconnect Azure</Button>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
