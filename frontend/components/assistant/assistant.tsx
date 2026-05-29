"use client";

import { Bot, Send, X } from "lucide-react";
import { useEffect, useState } from "react";
import { askAssistant, askAssistantStream } from "@/lib/api";

type Message = { id: string; role: "user" | "assistant"; text: string; agent?: string };

export function AssistantWidget() {
  const MAX_INPUT_CHARS = 300;
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mindIndex, setMindIndex] = useState(0);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "Hi — I'm your OKR copilot. Ask about progress, risks, deadlines, owners, teams, blockers, or status.",
      agent: "router",
    },
  ]);
  const mindMessages = ["Reading signals...", "Ready for queries", "Write actions enabled"];

  useEffect(() => {
    const id = setInterval(() => {
      setMindIndex((x) => (x + 1) % mindMessages.length);
    }, 2200);
    return () => clearInterval(id);
  }, []);

  async function sendMessage(text?: string) {
    const q = (text ?? input).trim().slice(0, MAX_INPUT_CHARS);
    if (!q || loading) return;

    setMessages((m) => [...m, { id: `u-${Date.now()}`, role: "user", text: q }]);
    setInput("");
    setLoading(true);
    let streamId: string | null = null;

    try {
      const currentStreamId = `a-${Date.now()}`;
      streamId = currentStreamId;
      setMessages((m) => [...m, { id: currentStreamId, role: "assistant", text: "", agent: "router" }]);
      await askAssistantStream(q, {
        onMeta: (agent) => {
          setMessages((m) =>
            m.map((msg) => (msg.id === currentStreamId ? { ...msg, agent } : msg)),
          );
        },
        onToken: (text) => {
          setMessages((m) =>
            m.map((msg) => (msg.id === currentStreamId ? { ...msg, text: `${msg.text}${text}` } : msg)),
          );
        },
      });
    } catch {
      if (streamId) {
        setMessages((m) => m.filter((msg) => msg.id !== streamId));
      }
      try {
        const res = await askAssistant(q);
        setMessages((m) => [
          ...m,
          { id: `a-fb-${Date.now()}`, role: "assistant", text: res.answer, agent: res.agent },
        ]);
      } catch (fallbackError) {
        setMessages((m) => [
          ...m,
          {
            id: `a-err-${Date.now()}`,
            role: "assistant",
            text: `Request failed: ${(fallbackError as Error).message}`,
          },
        ]);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="fixed bottom-4 right-4 z-40 flex items-center gap-2 sm:bottom-6 sm:right-6">
        <div className="rounded-full border border-primary/30 bg-white/92 px-3 py-1.5 text-xs text-fg shadow-soft backdrop-blur dark:border-emerald-800/70 dark:bg-emerald-950/90 dark:text-emerald-200">
          <span className="mr-2 inline-block h-2 w-2 animate-pulse rounded-full bg-primary dark:bg-emerald-500" />
          <span key={mindIndex} className="inline-block animate-pulse">{mindMessages[mindIndex]}</span>
        </div>
        <button
          onClick={() => setOpen(true)}
          className="relative grid h-12 w-12 place-items-center rounded-full bg-primary text-white shadow-soft sm:h-14 sm:w-14"
          aria-label="Open OKR Copilot"
        >
          <span className="pointer-events-none absolute -inset-1 rounded-full border border-primary/50 animate-pulse" />
          <span className="pointer-events-none absolute -inset-3 rounded-full border border-primary/25 animate-ping" />
          <Bot className="h-8 w-8" />
        </button>
      </div>

      {open && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm">
          <div className="absolute inset-x-0 bottom-0 top-16 flex h-[calc(100vh-4rem)] w-full flex-col overflow-hidden rounded-t-3xl border border-border bg-card shadow-soft sm:inset-auto sm:right-6 sm:top-6 sm:h-[calc(100vh-3rem)] sm:max-w-xl sm:rounded-3xl">
            <div className="flex items-center justify-between border-b border-border p-4">
              <div className="flex items-center gap-3">
                <div className="grid h-11 w-11 place-items-center rounded-full bg-primary/20 text-primary"><Bot /></div>
                <div>
                  <div className="text-lg font-semibold">OKR Copilot</div>
                  <div className="flex items-center gap-2 text-sm text-muted">
                    <span className="relative inline-flex h-2.5 w-2.5">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success/70" />
                      <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-success" />
                    </span>
                    Online and ready
                  </div>
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
                  onChange={(e) => setInput(e.target.value.slice(0, MAX_INPUT_CHARS))}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  placeholder="Ask about progress, risks, deadlines..."
                  maxLength={MAX_INPUT_CHARS}
                  className="h-12 flex-1 rounded-2xl border border-border bg-bg px-4 outline-none focus:ring-2 focus:ring-primary/30"
                />
                <button onClick={() => sendMessage()} disabled={loading} className="grid h-12 w-12 place-items-center rounded-2xl bg-primary text-white disabled:opacity-50">
                  <Send className="h-4 w-4" />
                </button>
              </div>
              <div className="text-right text-xs text-muted">
                {input.length}/{MAX_INPUT_CHARS}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
