"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/app-shell";
import { ClusterSelector } from "@/components/cluster-selector";
import { StreamingAnalysisPanel } from "@/components/streaming-analysis-panel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useAppStore } from "@/store/app-store";
import { TimelineView } from "@/components/timeline-view";
import { RemediationCard } from "@/components/remediation-card";

export default function AnalysisPage() {
  const { data } = useQuery({ queryKey: ["clusters"], queryFn: api.clusters });
  const selectedCluster = useAppStore((state) => state.selectedCluster);
  const [incidentId, setIncidentId] = useState<string>();
  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Incident Analysis</h1>
        <p className="mt-2 text-muted">Stream AKS failure detection and AI root cause analysis.</p>
      </div>
      <div className="grid gap-5">
        <Card>
          <CardHeader><CardTitle>Cluster Context</CardTitle></CardHeader>
          <CardContent><ClusterSelector clusters={data ?? []} /></CardContent>
        </Card>
        <StreamingAnalysisPanel clusterId={selectedCluster?.id} onIncidentReady={setIncidentId} />
        <div className="grid gap-5 lg:grid-cols-2">
          <Card>
            <CardHeader><CardTitle>Incident Timeline</CardTitle></CardHeader>
            <CardContent>
              <TimelineView items={["Pod entered CrashLoopBackOff", "Deployment availability dropped", "Events normalized", "AI remediation prepared"]} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Safe Remediation</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <RemediationCard incidentId={incidentId ?? ""} action="rollout_restart_deployment" />
              <RemediationCard incidentId={incidentId ?? ""} action="delete_failed_pod" />
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
