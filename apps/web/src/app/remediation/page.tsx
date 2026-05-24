"use client";

import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function RemediationApprovalPage() {
  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Remediation Approval</h1>
        <p className="mt-2 text-muted">Approval controls are attached to AI-generated remediation actions.</p>
      </div>
      <Card>
        <CardHeader><CardTitle>Approval Queue</CardTitle></CardHeader>
        <CardContent className="text-sm leading-6 text-muted">
          Run an incident analysis to populate approval-ready actions. Each action is validated by the backend allowlist before approval and executed through the Kubernetes SDK only after approval.
        </CardContent>
      </Card>
    </AppShell>
  );
}
