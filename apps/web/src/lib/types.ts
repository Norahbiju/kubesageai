export type Severity = "low" | "medium" | "high" | "critical";

export interface Subscription {
  subscription_id: string;
  display_name: string;
  state: string;
}

export interface Cluster {
  id: string;
  subscription_id: string;
  resource_group: string;
  cluster_name: string;
  location: string;
  kubernetes_version: string;
  cluster_resource_id: string;
  status: string;
}

export interface Incident {
  id: string;
  cluster_id: string;
  namespace: string;
  workload_name: string;
  workload_type: string;
  issue_type: string;
  severity: Severity;
  status: string;
  detected_at: string;
}

export interface Analysis {
  summary: string;
  root_cause: string;
  severity: Severity;
  confidence_score: number;
  affected_services: string[];
  remediation: Array<{
    action_id?: string | null;
    title: string;
    description: string;
    risk: "low" | "medium" | "high";
    action_type: string;
    requires_approval: boolean;
    command_preview: string;
    action_payload: Record<string, unknown>;
  }>;
  timeline: Array<{ time: string; event: string }>;
  explanation: string;
  next_steps: string[];
}

export interface StreamEvent {
  type: string;
  user_id: string;
  payload: Record<string, unknown>;
  created_at: string;
}
