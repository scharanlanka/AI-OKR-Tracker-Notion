"use client";

import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import type { Okr } from "@/lib/api";

type Tab = "objectives" | "key_results";

function statusClass(status?: string | null) {
  const s = (status || "").toLowerCase();
  if (s.includes("track") || s.includes("progress")) return "text-success border-success/40 bg-success/10";
  if (s.includes("risk") || s.includes("blocked")) return "text-warning border-warning/40 bg-warning/10";
  if (s.includes("off") || s.includes("delay")) return "text-danger border-danger/40 bg-danger/10";
  return "text-muted border-border bg-card";
}

function teamClass(team?: string | null) {
  const t = (team || "").toLowerCase();
  if (t.includes("frontend")) return "text-indigo-300 border-indigo-500/40 bg-indigo-500/10";
  if (t.includes("backend")) return "text-amber-300 border-amber-500/40 bg-amber-500/10";
  if (t.includes("platform")) return "text-cyan-300 border-cyan-500/40 bg-cyan-500/10";
  if (t.includes("growth")) return "text-emerald-300 border-emerald-500/40 bg-emerald-500/10";
  return "text-muted border-border bg-card";
}

function progressBarClass(progress: number) {
  if (progress < 0.35) return "bg-warning";
  if (progress < 0.7) return "bg-primary";
  return "bg-success";
}

function notionPageUrl(notionId?: string | null) {
  if (!notionId) return null;
  return `https://www.notion.so/${notionId.replace(/-/g, "")}`;
}

export function OkrTabs({ data }: { data: Okr[] }) {
  const [tab, setTab] = useState<Tab>("objectives");
  const [query, setQuery] = useState("");

  const objectives = useMemo(() => {
    const q = query.toLowerCase().trim();
    return data.filter((o) => [o.title, o.owner || "", o.team || "", o.status || "", o.quarter || ""].join(" ").toLowerCase().includes(q));
  }, [data, query]);

  const keyResults = useMemo(() => {
    const q = query.toLowerCase().trim();
    return data.flatMap((o) => o.key_results.map((kr) => ({ ...kr, objectiveTitle: o.title }))).filter((kr) =>
      [kr.title, kr.owner || "", kr.team || "", kr.status || "", kr.risk || "", kr.blocker_notes || "", kr.objectiveTitle].join(" ").toLowerCase().includes(q)
    );
  }, [data, query]);

  return (
    <section className="rounded-[28px] border border-border bg-card shadow-soft">
      <div className="flex flex-col gap-4 border-b border-border p-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="inline-flex rounded-2xl border border-border bg-bg p-1">
          <button onClick={() => setTab("objectives")} className={`rounded-xl px-6 py-3 text-lg ${tab === "objectives" ? "bg-card font-semibold" : "text-muted"}`}>
            Objectives <span className="ml-2 text-muted">{data.length}</span>
          </button>
          <button onClick={() => setTab("key_results")} className={`rounded-xl px-6 py-3 text-lg ${tab === "key_results" ? "bg-card font-semibold" : "text-muted"}`}>
            Key Results <span className="ml-2 text-muted">{data.reduce((a, b) => a + b.key_results.length, 0)}</span>
          </button>
        </div>

        <label className="relative block w-full max-w-md">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by title, owner, team..."
            className="h-12 w-full rounded-2xl border border-border bg-bg pl-12 pr-4 text-base outline-none focus:ring-2 focus:ring-primary/30"
          />
        </label>
      </div>

      {tab === "objectives" ? (
        <>
          <div className="space-y-3 p-4 md:hidden">
            {objectives.map((o) => (
              <article key={o.id} className="rounded-2xl border border-border bg-bg p-4">
                <div className="text-base font-semibold">{o.title}</div>
                {notionPageUrl(o.notion_id) && (
                  <a href={notionPageUrl(o.notion_id) || "#"} target="_blank" rel="noreferrer" className="mt-1 inline-block text-xs text-primary hover:underline">
                    View in Notion
                  </a>
                )}
                <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-muted">Owner:</span> {o.owner || "—"}</div>
                  <div><span className="text-muted">Team:</span> {o.team || "—"}</div>
                  <div><span className="text-muted">Quarter:</span> {o.quarter || "—"}</div>
                  <div><span className={`inline-block rounded-full border px-2 py-0.5 text-xs ${statusClass(o.status)}`}>{o.status || "Unknown"}</span></div>
                </div>
              </article>
            ))}
          </div>
          <div className="hidden max-h-[62vh] overflow-x-auto overflow-y-scroll md:block">
            <table className="w-full min-w-[980px] table-fixed">
            <thead className="text-left text-xs uppercase tracking-[0.14em] text-muted">
              <tr className="border-b border-border">
                <th className="px-6 py-4">Objective</th><th className="px-6 py-4">Owner</th><th className="px-6 py-4">Team</th><th className="px-6 py-4">Quarter</th><th className="px-6 py-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {objectives.map((o) => (
                <tr key={o.id} className="border-b border-border/60">
                  <td className="px-6 py-5 text-base font-medium w-[44%] break-words">
                    <div className="space-y-1">
                      <div>{o.title}</div>
                      {notionPageUrl(o.notion_id) && (
                        <a
                          href={notionPageUrl(o.notion_id) || "#"}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-primary hover:underline"
                        >
                          View in Notion
                        </a>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-5 text-base w-[18%] whitespace-nowrap">{o.owner || "—"}</td>
                  <td className="px-6 py-5"><span className="rounded-full border border-border px-3 py-1 text-sm">{o.team || "—"}</span></td>
                  <td className="px-6 py-5 text-base w-[10%] whitespace-nowrap">{o.quarter || "—"}</td>
                  <td className="px-6 py-5"><span className={`rounded-full border px-3 py-1 text-sm ${statusClass(o.status)}`}>{o.status || "Unknown"}</span></td>
                </tr>
              ))}
            </tbody>
            </table>
          </div>
        </>
      ) : (
        <>
          <div className="space-y-3 p-4 md:hidden">
            {keyResults.map((kr) => (
              <article key={kr.id} className="rounded-2xl border border-border bg-bg p-4">
                <div className="text-base font-semibold">{kr.title}</div>
                <div className="text-xs text-muted">{kr.objectiveTitle}</div>
                {notionPageUrl(kr.notion_id) && (
                  <a href={notionPageUrl(kr.notion_id) || "#"} target="_blank" rel="noreferrer" className="mt-1 inline-block text-xs text-primary hover:underline">
                    View in Notion
                  </a>
                )}
                <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-muted">Owner:</span> {kr.owner || "—"}</div>
                  <div><span className="text-muted">Team:</span> {kr.team || "—"}</div>
                  <div><span className="text-muted">Risk:</span> {kr.risk || "—"}</div>
                  <div><span className={`inline-block rounded-full border px-2 py-0.5 text-xs ${statusClass(kr.status)}`}>{kr.status || "Unknown"}</span></div>
                  <div><span className="text-muted">Due:</span> {kr.deadline || "—"}</div>
                  <div><span className="text-muted">Progress:</span> {Math.round((kr.progress || 0) * 100)}%</div>
                </div>
                <div className="mt-3 h-2.5 w-full rounded-full bg-card">
                  <div className={`h-full rounded-full ${progressBarClass(kr.progress || 0)}`} style={{ width: `${Math.max(4, Math.round((kr.progress || 0) * 100))}%` }} />
                </div>
                {kr.blocker_notes && <div className="mt-3 text-sm"><span className="text-muted">Blocker:</span> {kr.blocker_notes}</div>}
              </article>
            ))}
          </div>
          <div className="hidden max-h-[62vh] overflow-auto md:block">
            <table className="w-full min-w-[1500px]">
            <thead className="text-left text-xs uppercase tracking-[0.14em] text-muted">
              <tr className="border-b border-border">
                <th className="px-6 py-4">Key Result</th><th className="px-6 py-4">Owner</th><th className="px-6 py-4">Team</th><th className="px-6 py-4">Risk</th><th className="px-6 py-4">Status</th><th className="px-6 py-4">Progress</th><th className="px-6 py-4">Due</th><th className="px-6 py-4">Blocker</th>
              </tr>
            </thead>
            <tbody>
              {keyResults.map((kr) => (
                <tr key={kr.id} className="border-b border-border/60">
                  <td className="px-6 py-5">
                    <div className="text-base font-medium leading-snug">{kr.title}</div>
                    <div className="text-sm text-muted">{kr.objectiveTitle}</div>
                    {notionPageUrl(kr.notion_id) && (
                      <a
                        href={notionPageUrl(kr.notion_id) || "#"}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-1 inline-block text-xs text-primary hover:underline"
                      >
                        View in Notion
                      </a>
                    )}
                  </td>
                  <td className="px-6 py-5 text-base whitespace-nowrap">{kr.owner || "—"}</td>
                  <td className="px-6 py-5">
                    <span className={`whitespace-nowrap rounded-full border px-3 py-1 text-sm ${teamClass(kr.team)}`}>{kr.team || "—"}</span>
                  </td>
                  <td className="px-6 py-5 text-base whitespace-nowrap">{kr.risk || "—"}</td>
                  <td className="px-6 py-5">
                    <span className={`whitespace-nowrap rounded-full border px-3 py-1 text-sm ${statusClass(kr.status)}`}>{kr.status || "Unknown"}</span>
                  </td>
                  <td className="px-6 py-5 min-w-[220px]">
                    <div className="flex items-center gap-3">
                      <div className="h-2.5 w-40 rounded-full bg-bg">
                        <div
                          className={`h-full rounded-full ${progressBarClass(kr.progress || 0)}`}
                          style={{ width: `${Math.max(4, Math.round((kr.progress || 0) * 100))}%` }}
                        />
                      </div>
                      <span className="text-sm whitespace-nowrap">{Math.round((kr.progress || 0) * 100)}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-5 text-base whitespace-nowrap">{kr.deadline || "—"}</td>
                  <td className="px-6 py-5 text-base">{kr.blocker_notes || "—"}</td>
                </tr>
              ))}
            </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
