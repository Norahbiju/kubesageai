import { Card, CardContent } from "@/components/ui/card";

export function MetricCard({ label, value, hint }: { label: string; value: string | number; hint: string }) {
  return (
    <Card>
      <CardContent>
        <div className="text-sm text-muted">{label}</div>
        <div className="mt-3 text-3xl font-semibold">{value}</div>
        <div className="mt-2 text-xs text-muted">{hint}</div>
      </CardContent>
    </Card>
  );
}
