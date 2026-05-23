import { cn } from "@/lib/utils";
import type { Severity } from "@/lib/types";

const styles: Record<Severity, string> = {
  low: "bg-lime/15 text-lime border-lime/30",
  medium: "bg-amber/15 text-amber border-amber/30",
  high: "bg-rose/15 text-rose border-rose/30",
  critical: "bg-rose text-black border-rose"
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={cn("rounded-full border px-2.5 py-1 text-xs font-semibold capitalize", styles[severity])}>
      {severity}
    </span>
  );
}
