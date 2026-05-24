"use client";

import { Server, Sparkles } from "lucide-react";
import type { Cluster } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/store/app-store";

export function ClusterSelector({ clusters }: { clusters: Cluster[] }) {
  const { selectedCluster, setSelectedCluster } = useAppStore();
  return (
    <div className="grid gap-3">
      {clusters.map((cluster) => (
        <div
          key={cluster.id}
          className="flex flex-col gap-4 rounded-lg border border-line bg-panel/70 p-4 md:flex-row md:items-center md:justify-between"
        >
          <div className="flex items-start gap-3">
            <div className="rounded-md bg-cyan/15 p-2 text-cyan">
              <Server size={18} />
            </div>
            <div>
              <div className="font-medium">{cluster.cluster_name}</div>
              <div className="mt-1 text-sm text-muted">
                {cluster.resource_group} · {cluster.location} · Kubernetes {cluster.kubernetes_version}
              </div>
              <div className="mt-2 text-xs text-muted">{cluster.status}</div>
            </div>
          </div>
          <Button
            variant={selectedCluster?.id === cluster.id ? "primary" : "secondary"}
            onClick={() => setSelectedCluster(cluster)}
          >
            <Sparkles size={16} />
            {selectedCluster?.id === cluster.id ? "Selected" : "Select"}
          </Button>
        </div>
      ))}
    </div>
  );
}
