import type { Cluster, Incident } from "./types";

const configuredApiBase =
  process.env.NEXT_PUBLIC_API_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "same-origin";

function authHeaders() {
  if (typeof window === "undefined") return {};
  const token = window.localStorage.getItem("kubesage_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function apiBaseUrl() {
  if (configuredApiBase === "same-origin" || configuredApiBase === "") return "";
  if (typeof window === "undefined") return configuredApiBase;

  const isLocalApi =
    configuredApiBase.includes("localhost") ||
    configuredApiBase.includes("127.0.0.1") ||
    configuredApiBase.includes("0.0.0.0");
  const isRemoteBrowserHost = !["localhost", "127.0.0.1", "0.0.0.0"].includes(window.location.hostname);

  if (isLocalApi && isRemoteBrowserHost) {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }

  return configuredApiBase;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(init?.headers ?? {})
    }
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export const api = {
  loginUrl: () => `${apiBaseUrl()}/api/auth/azure/login`,
  me: () => request<{ id: string; email: string; display_name: string }>("/api/auth/me"),
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
  streamUrl: (clusterId: string) => `${apiBaseUrl()}/api/incidents/analyze/stream?cluster_id=${clusterId}`
};
