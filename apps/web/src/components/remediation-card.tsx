"use client";

import { ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export function RemediationCard({ incidentId, action }: { incidentId: string; action: string }) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-line bg-panel p-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div className="font-medium">{action}</div>
        <div className="mt-1 text-sm text-muted">Requires explicit approval and audit logging.</div>
      </div>
      <Button disabled={!incidentId} onClick={() => api.approveRemediation(incidentId, action)}>
        <ShieldCheck size={16} /> Approve
      </Button>
    </div>
  );
}
