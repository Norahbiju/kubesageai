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
  loginUrl: () => `${apiBaseUrl()}/api/auth/login`,
  logout: () => request<{ status: string }>("/api/auth/logout", { method: "POST" }),
  me: () => request<{ id: string; email: string; display_name: string; tenant_id: string }>("/api/me"),
  subscriptions: () => request<Subscription[]>("/api/azure/subscriptions"),
  subscriptionClusters: (subscriptionId: string) => request<Cluster[]>(`/api/azure/subscriptions/${subscriptionId}/clusters`),
  clusters: () => request<Cluster[]>("/api/azure/clusters"),
  connectivityCheck: () => request<{ authenticated: boolean; azure_connected: boolean; subscription_count: number; tenant_id: string }>("/api/azure/connectivity-check"),
  incidents: () => request<Incident[]>("/api/incidents"),
  scanCluster: (clusterId: string) => request<{ incidents: Incident[] }>(`/api/clusters/${clusterId}/scan`, { method: "POST" }),
  analyzeIncident: (incidentId: string) => request<Analysis>(`/api/incidents/${incidentId}/analyze`, { method: "POST" }),
  approveRemediation: (incidentId: string, actionId: string, actionType: string, actionPayload: Record<string, unknown>) =>
    request(`/api/incidents/${incidentId}/remediations/${actionId}/approve`, {
      method: "POST",
      body: JSON.stringify({ action_type: actionType, action_payload: actionPayload })
    }),
  executeRemediation: (incidentId: string, actionId: string) =>
    request(`/api/incidents/${incidentId}/remediations/${actionId}/execute`, { method: "POST" }),
  auditLogs: () => request<Array<Record<string, unknown>>>("/api/audit-logs"),
  streamUrl: () => `${apiBaseUrl()}/api/stream/events`
};
