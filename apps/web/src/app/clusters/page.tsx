"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/app-shell";
import { ClusterSelector } from "@/components/cluster-selector";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function ClustersPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["clusters"], queryFn: api.clusters, retry: false });
  return (
    <AppShell>
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold">AKS Clusters</h1>
          <p className="mt-2 text-muted">Real AKS clusters visible to your signed-in Azure account.</p>
        </div>
        <Link
          href="/analysis"
          className="inline-flex h-10 items-center justify-center rounded-md bg-cyan px-4 text-sm font-medium text-black transition hover:bg-cyan/90"
        >
          Start Analysis
        </Link>
      </div>
      <Card>
        <CardHeader><CardTitle>Discovered from Azure</CardTitle></CardHeader>
        <CardContent>
          {isError ? (
            <div className="mb-4 rounded-2xl border border-rose/40 bg-rose/10 p-4 text-sm text-rose">
              Unable to load AKS clusters. Your Azure account may not have permission to list subscriptions or AKS clusters.
            </div>
          ) : null}
          {isLoading ? <div className="h-40 animate-pulse rounded-md bg-white/5" /> : <ClusterSelector clusters={data ?? []} />}
        </CardContent>
      </Card>
    </AppShell>
  );
}
