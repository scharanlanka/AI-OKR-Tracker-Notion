"use client";

import { useEffect, useMemo, useState } from "react";
import { AssistantWidget } from "@/components/assistant/assistant";
import { DashboardHeader } from "@/components/dashboard/header";
import { MetricsCards } from "@/components/dashboard/metrics";
import { OkrTabs } from "@/components/dashboard/okr-tabs";
import { getHealth, getOkrs, syncNotion, type Okr } from "@/lib/api";

export default function HomePage() {
  const [data, setData] = useState<Okr[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);

  async function loadData() {
    setLoading(true);
    try {
      const [health, okrs] = await Promise.all([getHealth(), getOkrs()]);
      setBackendOnline(health.status === "ok");
      setData(okrs);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  const metrics = useMemo(() => {
    const keyResults = data.flatMap((o) => o.key_results);
    const atRisk = keyResults.filter((k) => (k.risk || "").toLowerCase() === "high" || (k.status || "").toLowerCase().includes("risk") || k.is_blocked).length;
    const avgProgress = keyResults.length ? keyResults.reduce((a, b) => a + (b.progress || 0), 0) / keyResults.length : 0;
    return { objectives: data.length, keyResults: keyResults.length, atRisk, avgProgress };
  }, [data]);

  async function onSync() {
    setSyncing(true);
    try {
      await syncNotion();
      await loadData();
    } finally {
      setSyncing(false);
    }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_right,rgba(36,161,233,0.22),transparent_40%),radial-gradient(circle_at_bottom_left,rgba(22,125,213,0.16),transparent_32%)]">
      <DashboardHeader isSyncing={syncing} onSync={onSync} backendOnline={backendOnline} />

      <div className="mx-auto max-w-[1800px] space-y-6 px-4 py-6 sm:px-6 sm:py-8">
        <section>
          <h2 className="text-3xl font-semibold sm:text-4xl">OKR overview</h2>
          <p className="mt-1.5 text-sm text-muted">Quarterly progress, risks, and deadlines across teams — synced from Notion.</p>
        </section>

        {loading ? (
          <div className="rounded-3xl border border-border bg-card p-8 text-base text-muted">Loading dashboard...</div>
        ) : (
          <>
            <MetricsCards
              objectives={metrics.objectives}
              keyResults={metrics.keyResults}
              atRisk={metrics.atRisk}
              avgProgress={metrics.avgProgress}
            />
            <OkrTabs data={data} />
          </>
        )}
      </div>

      <AssistantWidget />
    </main>
  );
}
