import { RefreshCw } from "lucide-react";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export function DashboardHeader({
  isSyncing,
  onSync,
  backendOnline,
}: {
  isSyncing: boolean;
  onSync: () => void;
  backendOnline: boolean;
}) {
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-bg/90 backdrop-blur">
      <div className="mx-auto flex max-w-[1800px] items-center justify-between px-6 py-5">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-2xl bg-primary/90 text-white grid place-items-center text-lg">◎</div>
          <div>
            <h1 className="text-base font-semibold leading-none">AI OKR Tracker</h1>
            <p className="mt-1 text-xs tracking-[0.22em] text-muted">MISSION CONTROL</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="rounded-full border border-border bg-card px-4 py-2 text-sm text-muted">
            <span className={`mr-2 inline-block h-2 w-2 rounded-full ${backendOnline ? "bg-success" : "bg-danger"}`} />
            {backendOnline ? "Backend online" : "Backend offline"}
          </div>
          <button
            onClick={onSync}
            disabled={isSyncing}
            className="inline-flex items-center gap-2 rounded-2xl border border-border bg-card px-5 py-3 text-lg font-medium shadow-soft disabled:opacity-50"
          >
            <RefreshCw className={`h-5 w-5 ${isSyncing ? "animate-spin" : ""}`} />
            {isSyncing ? "Syncing..." : "Sync Notion"}
          </button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
