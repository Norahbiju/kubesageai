export function TimelineView({ items }: { items: string[] }) {
  return (
    <div className="space-y-3">
      {items.map((item, index) => (
        <div key={item} className="flex gap-3">
          <div className="mt-1 h-2.5 w-2.5 rounded-full bg-cyan" />
          <div>
            <div className="text-xs text-muted">Step {index + 1}</div>
            <div className="text-sm">{item}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
