export type Objective = {
  id: number;
  notion_id: string;
  title: string;
  owner?: string | null;
  team?: string | null;
  quarter?: string | null;
  status?: string | null;
  progress: number;
};

export type KeyResult = {
  id: number;
  notion_id: string;
  objective_id: number;
  title: string;
  owner?: string | null;
  team?: string | null;
  risk?: string | null;
  status?: string | null;
  progress: number;
  deadline?: string | null;
  is_blocked: boolean;
  blocker_notes?: string | null;
};

export type Okr = Objective & { key_results: KeyResult[] };

export type AskResponse = {
  agent: string;
  answer: string;
};

const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export async function getHealth() {
  return request<{ status: string }>("/health");
}

export async function syncNotion() {
  return request<{ message: string; objectives_synced: number; key_results_synced: number }>("/sync/notion", {
    method: "POST",
  });
}

export async function getOkrs() {
  return request<Okr[]>("/okrs");
}

export async function askAssistant(question: string) {
  return request<AskResponse>("/ask", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}
