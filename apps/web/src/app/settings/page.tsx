import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Settings</h1>
        <p className="mt-2 text-muted">Configure AI analysis and Azure connection posture.</p>
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>OpenAI</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <input className="h-10 w-full rounded-md border border-line bg-panel2 px-3 text-sm outline-none" placeholder="OPENAI_API_KEY configured on backend" />
            <select className="h-10 w-full rounded-md border border-line bg-panel2 px-3 text-sm outline-none" defaultValue="gpt-4.1-mini">
              <option value="gpt-4.1-mini">gpt-4.1-mini</option>
              <option value="gpt-4.1">gpt-4.1</option>
            </select>
            <Button>Save AI Settings</Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Azure Connection</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-md border border-line bg-panel2 p-4 text-sm text-muted">Microsoft Identity Platform connected. Tokens are exchanged server-side and not exposed to remediation workflows.</div>
            <Button variant="secondary">Reconnect Azure</Button>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
