"use client";

import { Cloud, ShieldCheck } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export default function AzureConnectionPage() {
  const { data, isError } = useQuery({ queryKey: ["me"], queryFn: api.me, retry: false });
  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Azure Connection</h1>
        <p className="mt-2 text-muted">Connect with Microsoft Entra ID to discover subscriptions and AKS clusters.</p>
      </div>
      <div className="grid gap-5 lg:grid-cols-[.8fr_1.2fr]">
        <Card>
          <CardHeader><CardTitle>Account Status</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-md border border-line bg-panel2 p-4">
              <div className="flex items-center gap-2 text-sm font-medium">
                {data ? <ShieldCheck size={16} className="text-lime" /> : <Cloud size={16} className="text-muted" />}
                {data ? "Connected" : "Not connected"}
              </div>
              <div className="mt-2 text-sm text-muted">{data?.email ?? "Sign in with Azure Entra ID to continue."}</div>
            </div>
            <Button onClick={() => { window.location.href = api.loginUrl(); }}>
              Connect Azure
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Permission Check</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm text-muted">
            <div className="rounded-md border border-line bg-panel2 p-3">Azure Resource Manager access is requested through delegated user permissions.</div>
            <div className="rounded-md border border-line bg-panel2 p-3">AKS credentials are requested only for clusters selected by the signed-in user.</div>
            {isError ? <div className="rounded-md border border-red-500/40 bg-red-500/10 p-3 text-red-200">Authentication is required.</div> : null}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
