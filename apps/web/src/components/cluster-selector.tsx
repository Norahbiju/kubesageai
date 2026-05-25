"use client";

import { Server, Sparkles } from "lucide-react";
import type { Cluster } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/store/app-store";

export function ClusterSelector({ clusters }: { clusters: Cluster[] }) {
  const { selectedCluster, setSelectedCluster } = useAppStore();

  if (!clusters.length) {
    return (
      <div className="rounded-2xl border border-line bg-panel2 p-6 text-sm leading-6 text-muted">
        No AKS clusters were found for your Azure account. Make sure your signed-in Azure user has Reader access to the subscription and AKS Cluster User permissions on the cluster.
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      {clusters.map((cluster) => (
        <div
          key={cluster.id}
          className="flex flex-col gap-4 rounded-2xl border border-line bg-panel/70 p-4 md:flex-row md:items-center md:justify-between"
        >
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-cyan/15 p-2 text-cyan">
              <Server size={18} />
            </div>
            <div>
              <div className="font-medium">{cluster.cluster_name}</div>
              <div className="mt-1 text-sm text-muted">
                {cluster.resource_group} / {cluster.location} / Kubernetes {cluster.kubernetes_version || "unknown"}
              </div>
              <div className="mt-2 text-xs text-muted">
                {cluster.subscription_id} / {cluster.status}
              </div>
            </div>
          </div>
          <Button
            variant={selectedCluster?.id === cluster.id ? "primary" : "secondary"}
            onClick={() => setSelectedCluster(cluster)}
          >
            <Sparkles size={16} />
            {selectedCluster?.id === cluster.id ? "Selected" : "Analyze"}
          </Button>
        </div>
      ))}
    </div>
  );
}
