import type { Analysis, Cluster, Incident, Subscription } from "./types";

const configuredApiBase =
  process.env.NEXT_PUBLIC_API_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function apiBaseUrl() {
  return configuredApiBase === "same-origin" ? "" : configuredApiBase;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers({ "Content-Type": "application/json" });
  new Headers(init?.headers).forEach((value, key) => headers.set(key, value));

  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    credentials: "include",
    headers
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export const api = {
  loginUrl: () => `${apiBaseUrl()}/auth/login`,
  me: () => request<{ id: string; email: string; display_name: string; tenant_id: string }>("/auth/me"),
  subscriptions: () => request<Subscription[]>("/azure/subscriptions"),
  subscriptionClusters: (subscriptionId: string) => request<Cluster[]>(`/azure/subscriptions/${subscriptionId}/clusters`),
  clusters: () => request<Cluster[]>("/clusters"),
  incidents: () => request<Incident[]>("/incidents"),
  scanCluster: (clusterId: string) => request<{ incidents: Incident[] }>(`/clusters/${clusterId}/scan`, { method: "POST" }),
  analyzeIncident: (incidentId: string) => request<Analysis>(`/incidents/${incidentId}/analyze`, { method: "POST" }),
  approveRemediation: (incidentId: string, actionId: string, actionType: string, actionPayload: Record<string, unknown>) =>
    request(`/incidents/${incidentId}/remediations/${actionId}/approve`, {
      method: "POST",
      body: JSON.stringify({ action_type: actionType, action_payload: actionPayload })
    }),
  executeRemediation: (incidentId: string, actionId: string) =>
    request(`/incidents/${incidentId}/remediations/${actionId}/execute`, { method: "POST" }),
  auditLogs: () => request<Array<Record<string, unknown>>>("/audit-logs"),
  streamUrl: () => `${apiBaseUrl()}/stream/events`
};
