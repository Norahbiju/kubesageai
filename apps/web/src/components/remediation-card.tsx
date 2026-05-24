"use client";

import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export function RemediationCard({
  incidentId,
  actionId,
  action,
  payload
}: {
  incidentId: string;
  actionId: string;
  action: string;
  payload: Record<string, unknown>;
}) {
  const [approved, setApproved] = useState(false);
  const [busy, setBusy] = useState(false);

  async function approve() {
    setBusy(true);
    try {
      await api.approveRemediation(incidentId, actionId, action, payload);
      setApproved(true);
    } finally {
      setBusy(false);
    }
  }

  async function execute() {
    setBusy(true);
    try {
      await api.executeRemediation(incidentId, actionId);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-line bg-panel p-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div className="font-medium">{action}</div>
        <div className="mt-1 text-sm text-muted">Requires explicit approval and audit logging.</div>
      </div>
      <div className="flex gap-2">
        <Button disabled={!incidentId || !actionId || approved || busy} onClick={approve}>
          <ShieldCheck size={16} /> Approve
        </Button>
        <Button disabled={!approved || busy} onClick={execute} variant="secondary">
          Execute
        </Button>
      </div>
    </div>
  );
}
