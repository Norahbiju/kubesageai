import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function MetricCard({
  label,
  value,
  hint,
  tone = "dark"
}: {
  label: string;
  value: string | number;
  hint: string;
  tone?: "green" | "blue" | "dark";
}) {
  return (
    <Card
      className={cn(
        "overflow-hidden border-0",
        tone === "green" && "bg-lime text-[#08140e]",
        tone === "blue" && "bg-cyan text-[#08111f]",
        tone === "dark" && "bg-panel"
      )}
    >
      <CardContent>
        <div className={cn("text-sm", tone === "dark" ? "text-muted" : "text-black/60")}>{label}</div>
        <div className="mt-3 text-3xl font-semibold">{value}</div>
        <div className={cn("mt-2 text-xs", tone === "dark" ? "text-muted" : "text-black/55")}>{hint}</div>
      </CardContent>
    </Card>
  );
}
