"use client";

import { useEffect, useMemo, useState } from "react";
import { Bot, Terminal } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Analysis, StreamEvent } from "@/lib/types";
import { api } from "@/lib/api";
import { SeverityBadge } from "@/components/severity-badge";

export function StreamingAnalysisPanel({
  clusterId,
  onIncidentReady
}: {
  clusterId?: string;
  onIncidentReady?: (incidentId: string) => void;
}) {
  const [progress, setProgress] = useState<string[]>([]);
  const [analysis, setAnalysis] = useState<Analysis>();
  const [streamingText, setStreamingText] = useState("");

  useEffect(() => {
    if (!clusterId) return;
    setProgress([]);
    setAnalysis(undefined);
    setStreamingText("");
    const source = new EventSource(api.streamUrl(clusterId));
    source.onmessage = (event) => {
      const payload = JSON.parse(event.data) as StreamEvent;
      if (payload.type === "progress" && payload.message) {
        setProgress((items) => [...items, payload.message!]);
      }
      if (payload.type === "analysis_delta" && payload.message) {
        setStreamingText((text) => `${text}${payload.message}`);
      }
      if (payload.type === "analysis_complete" && payload.analysis) {
        setAnalysis(payload.analysis);
        if (payload.incident_id) onIncidentReady?.(payload.incident_id);
        source.close();
      }
      if (payload.type === "error") source.close();
    };
    return () => source.close();
  }, [clusterId, onIncidentReady]);

  const current = useMemo(() => progress.at(-1) ?? "Select a cluster to begin analysis.", [progress]);

  return (
    <div className="grid gap-5 lg:grid-cols-[.8fr_1.2fr]">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Terminal size={16} /> Live Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
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
                  <div key={item} className="rounded-md border border-line bg-panel2 p-3 text-sm text-muted">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <pre className="min-h-80 whitespace-pre-wrap rounded-md border border-line bg-black/40 p-4 text-sm leading-6 text-muted">
              {streamingText || "AI findings will stream here progressively."}
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
