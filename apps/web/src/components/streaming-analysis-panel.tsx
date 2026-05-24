"use client";

import { useEffect, useMemo, useState } from "react";
import { Bot, Terminal } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Analysis, StreamEvent } from "@/lib/types";
import { api } from "@/lib/api";
import { SeverityBadge } from "@/components/severity-badge";
import { Button } from "@/components/ui/button";
import { RemediationCard } from "@/components/remediation-card";

export function StreamingAnalysisPanel({
  clusterId,
  onIncidentReady
}: {
  clusterId?: string;
  onIncidentReady?: (incidentId: string) => void;
}) {
  const [progress, setProgress] = useState<string[]>([]);
  const [analysis, setAnalysis] = useState<Analysis>();
  const [currentIncidentId, setCurrentIncidentId] = useState("");
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    const source = new EventSource(api.streamUrl(), { withCredentials: true });
    source.onmessage = (event) => {
      const payload = JSON.parse(event.data) as StreamEvent;
      setProgress((items) => [...items, `${payload.type}: ${JSON.stringify(payload.payload)}`]);
    };
    return () => source.close();
  }, []);

  async function runScan() {
    if (!clusterId) return;
    setIsRunning(true);
    setAnalysis(undefined);
    setProgress((items) => [...items, "cluster.scan.requested"]);
    try {
      const scan = await api.scanCluster(clusterId);
      const firstIncident = scan.incidents[0];
      if (!firstIncident) {
        setProgress((items) => [...items, "cluster.scan.completed: no issues detected"]);
        return;
      }
      setCurrentIncidentId(firstIncident.id);
      onIncidentReady?.(firstIncident.id);
      const result = await api.analyzeIncident(firstIncident.id);
      setAnalysis(result);
    } finally {
      setIsRunning(false);
    }
  }

  const current = useMemo(() => progress.at(-1) ?? "Select a cluster, then start a real AKS scan.", [progress]);

  return (
    <div className="grid gap-5 lg:grid-cols-[.8fr_1.2fr]">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Terminal size={16} /> Live Progress
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button disabled={!clusterId || isRunning} onClick={runScan}>
            {isRunning ? "Scanning..." : "Scan Selected Cluster"}
          </Button>
          <div className="rounded-md border border-line bg-black/40 p-4 font-mono text-sm">
            <div className="mb-4 text-cyan">{current}</div>
            <div className="max-h-72 space-y-2 overflow-auto terminal-scroll">
              {progress.map((item, index) => (
                <div key={`${item}-${index}`} className="text-muted">
                  <span className="text-lime">$</span> {item}
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot size={16} /> AI Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          {analysis ? (
            <div className="space-y-5">
              <div className="flex items-center justify-between gap-3">
                <SeverityBadge severity={analysis.severity} />
                <div className="text-sm text-muted">{analysis.confidence_score}% confidence</div>
              </div>
              <div>
                <h4 className="text-sm font-semibold">Summary</h4>
                <p className="mt-2 text-sm leading-6 text-muted">{analysis.summary}</p>
              </div>
              <div>
                <h4 className="text-sm font-semibold">Root Cause</h4>
                <p className="mt-2 text-sm leading-6 text-muted">{analysis.root_cause}</p>
              </div>
              <div className="grid gap-2">
                {analysis.remediation.map((item) => (
                  <div key={item.title} className="rounded-md border border-line bg-panel2 p-3 text-sm text-muted">
                    <div className="font-medium text-text">{item.title}</div>
                    <div className="mt-1">{item.description}</div>
                    <div className="mt-2 text-xs">{item.action_type} / {item.risk} risk</div>
                    <div className="mt-3">
                      <RemediationCard
                        incidentId={currentIncidentId}
                        actionId={item.action_id ?? ""}
                        action={item.action_type}
                        payload={item.action_payload}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <pre className="min-h-80 whitespace-pre-wrap rounded-md border border-line bg-black/40 p-4 text-sm leading-6 text-muted">
              AI findings will appear after a real scan detects an incident.
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
