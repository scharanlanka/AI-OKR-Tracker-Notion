import { AlertTriangle, CheckCircle2, Sparkles, Target } from "lucide-react";

export function MetricsCards({
  objectives,
  keyResults,
  atRisk,
  avgProgress,
}: {
  objectives: number;
  keyResults: number;
  atRisk: number;
  avgProgress: number;
}) {
  const cards = [
    { label: "Active objectives", value: objectives, sub: "Synced", icon: Target, accent: "text-success" },
    { label: "Key results", value: keyResults, sub: "Across all objectives", icon: CheckCircle2, accent: "text-muted" },
    { label: "At-risk KRs", value: atRisk, sub: atRisk > 0 ? "Needs review" : "Healthy", icon: AlertTriangle, accent: atRisk > 0 ? "text-danger" : "text-success" },
    { label: "Avg. progress", value: `${Math.round(avgProgress * 100)}%`, sub: "Overall completion", icon: Sparkles, accent: "text-success" },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      {cards.map(({ label, value, sub, icon: Icon, accent }) => (
        <div key={label} className="rounded-3xl border border-border bg-card p-5 shadow-soft">
          <div className="flex items-center gap-2 text-sm text-muted"><Icon className="h-4 w-4" /> {label}</div>
          <div className="mt-3 text-4xl font-semibold leading-none">{value}</div>
          <div className={`mt-3 text-sm ${accent}`}>{sub}</div>
        </div>
      ))}
    </div>
  );
}
