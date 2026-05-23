export type Severity = "low" | "medium" | "high" | "critical";

export interface Cluster {
  id: string;
  name: string;
  resource_group: string;
  subscription_id: string;
  location: string;
  kubernetes_version: string;
  status: string;
  failing_workloads: number;
}

export interface Incident {
  id: string;
  title: string;
  cluster_name: string;
  severity: Severity;
  status: string;
  created_at: string;
  confidence_score: number;
}

export interface Analysis {
  summary: string;
  root_cause: string;
  severity: Severity;
  confidence_score: number;
  affected_services: string[];
  remediation: string[];
  timeline: string[];
  recommended_action: string;
}

export interface StreamEvent {
  type: "progress" | "analysis_delta" | "analysis_complete" | "error" | "remediation";
  message?: string;
  incident_id?: string;
  analysis?: Analysis;
}
