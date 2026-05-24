"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export default function SubscriptionsPage() {
  const [subscriptionId, setSubscriptionId] = useState("");
  const subscriptions = useQuery({ queryKey: ["subscriptions"], queryFn: api.subscriptions, retry: false });
  const clusters = useQuery({
    queryKey: ["subscription-clusters", subscriptionId],
    queryFn: () => api.subscriptionClusters(subscriptionId),
    enabled: Boolean(subscriptionId)
  });

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Subscriptions</h1>
        <p className="mt-2 text-muted">Load real Azure subscriptions and discover AKS clusters by subscription.</p>
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Azure Subscriptions</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {subscriptions.isLoading ? <div className="h-32 animate-pulse rounded-md bg-white/5" /> : null}
            {(subscriptions.data ?? []).map((item) => (
              <button
                key={item.subscription_id}
                onClick={() => setSubscriptionId(item.subscription_id)}
                className="w-full rounded-md border border-line bg-panel2 p-4 text-left transition hover:border-cyan"
              >
                <div className="font-medium">{item.display_name}</div>
                <div className="mt-1 text-sm text-muted">{item.subscription_id} / {item.state}</div>
              </button>
            ))}
            {subscriptions.isError ? <div className="rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">Unable to load subscriptions. Check Azure permissions and login state.</div> : null}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>AKS Clusters</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {!subscriptionId ? <div className="text-sm text-muted">Select a subscription to load clusters.</div> : null}
            {clusters.isFetching ? <div className="h-32 animate-pulse rounded-md bg-white/5" /> : null}
            {(clusters.data ?? []).map((cluster) => (
              <div key={cluster.id} className="rounded-md border border-line bg-panel2 p-4">
                <div className="font-medium">{cluster.cluster_name}</div>
                <div className="mt-1 text-sm text-muted">{cluster.resource_group} / {cluster.location} / {cluster.status}</div>
              </div>
            ))}
            {clusters.data?.length === 0 ? <div className="text-sm text-muted">No AKS clusters found for this subscription.</div> : null}
            {subscriptionId ? <Button onClick={() => clusters.refetch()}>Refresh Clusters</Button> : null}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
