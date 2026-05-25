"use client";

import { Bot, Send, X } from "lucide-react";
import { useState } from "react";
import { askAssistant } from "@/lib/api";

type Message = { role: "user" | "assistant"; text: string; agent?: string };

export function AssistantWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: "Hi — I'm your OKR copilot. Ask about progress, risks, deadlines, owners, teams, blockers, or status.", agent: "router" },
  ]);

  async function sendMessage(text?: string) {
    const q = (text ?? input).trim();
    if (!q || loading) return;

    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setLoading(true);

    try {
      const res = await askAssistant(q);
      setMessages((m) => [...m, { role: "assistant", text: res.answer, agent: res.agent }]);
    } catch (error) {
      setMessages((m) => [...m, { role: "assistant", text: `Request failed: ${(error as Error).message}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-40 grid h-14 w-14 place-items-center rounded-full bg-primary text-white shadow-soft"
      >
        <Bot className="h-8 w-8" />
      </button>

      {open && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm">
          <div className="absolute right-6 top-6 flex h-[calc(100vh-3rem)] w-full max-w-xl flex-col overflow-hidden rounded-3xl border border-border bg-card shadow-soft">
            <div className="flex items-center justify-between border-b border-border p-4">
              <div className="flex items-center gap-3">
                <div className="grid h-11 w-11 place-items-center rounded-full bg-primary/20 text-primary"><Bot /></div>
                <div>
                  <div className="text-lg font-semibold">OKR Copilot</div>
                  <div className="text-sm text-muted">Multi-agent routed via /ask</div>
                </div>
              </div>
              <button onClick={() => setOpen(false)} className="rounded-xl p-2 hover:bg-bg"><X /></button>
            </div>

            <div className="flex-1 space-y-4 overflow-y-auto p-4">
              {messages.map((m, idx) => (
                <div key={idx} className={`max-w-[90%] rounded-2xl border px-4 py-3 ${m.role === "assistant" ? "border-border bg-bg" : "ml-auto border-primary/30 bg-primary/10"}`}>
                  <p className="whitespace-pre-wrap text-base">{m.text}</p>
                  {m.agent && <p className="mt-2 text-xs text-muted">agent: {m.agent}</p>}
                </div>
              ))}
              {loading && <div className="text-sm text-muted">Thinking...</div>}
            </div>

            <div className="space-y-3 border-t border-border p-4">
              <div className="flex flex-wrap gap-2 text-sm">
                {[
                  "Which KRs are most at risk this quarter?",
                  "Show upcoming deadlines with progress",
                  "Objectives owned by Laura Johnson",
                ].map((q) => (
                  <button key={q} onClick={() => sendMessage(q)} className="rounded-full border border-border bg-bg px-3 py-1">{q}</button>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  placeholder="Ask about progress, risks, deadlines..."
                  className="h-12 flex-1 rounded-2xl border border-border bg-bg px-4 outline-none focus:ring-2 focus:ring-primary/30"
                />
                <button onClick={() => sendMessage()} disabled={loading} className="grid h-12 w-12 place-items-center rounded-2xl bg-primary text-white disabled:opacity-50">
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
