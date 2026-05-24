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
              <TimelineView
                items={
                  incidentId
                    ? ["Incident detected from live cluster data", "Signals persisted", "OpenAI analysis completed", "Approval-ready remediation prepared"]
                    : ["Run a scan to populate the incident timeline"]
                }
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Approval Gate</CardTitle></CardHeader>
            <CardContent className="text-sm leading-6 text-muted">
              Remediation actions appear with the AI analysis only after they have been stored by the backend. Execution remains blocked until an operator approves a specific action.
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
