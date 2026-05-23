import type { Cluster, Incident } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export const api = {
  loginUrl: () => `${API_BASE}/api/auth/azure/login`,
  dashboard: () => request<{
    clusters: number;
    incidents: number;
    remediation_success_rate: number;
    confidence_average: number;
    severity: Record<string, number>;
    recent_incidents: Incident[];
  }>("/api/incidents/dashboard"),
  clusters: () => request<Cluster[]>("/api/azure/clusters"),
  incidents: () => request<Incident[]>("/api/incidents"),
  approveRemediation: (incidentId: string, action: string) =>
    request(`/api/remediation/approve`, {
      method: "POST",
      body: JSON.stringify({ incident_id: incidentId, action_type: action, parameters: {} })
    }),
  streamUrl: (clusterId: string) => `${API_BASE}/api/incidents/analyze/stream?cluster_id=${clusterId}`
};
