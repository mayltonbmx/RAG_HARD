import { ChatRequest, ChatResponse, FileItem, Persona, StatsData, UploadResult } from "@/types";
import { getSession } from "next-auth/react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

/**
 * Get the access token from the current session.
 * Checks Azure session first, then admin JWT from localStorage.
 */
async function getAccessToken(): Promise<string | undefined> {
  // Try Azure session first
  const session = await getSession();
  if (session?.accessToken) return session.accessToken;

  // Fallback to admin JWT
  if (typeof window !== "undefined") {
    const adminToken = localStorage.getItem("admin_token");
    if (adminToken) return adminToken;
  }

  return undefined;
}

/**
 * Authenticated API request helper.
 * Automatically includes Bearer token if available.
 */
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = await getAccessToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));

    if (res.status === 401) {
      throw new Error("Sessão expirada. Faça login novamente.");
    }
    if (res.status === 403) {
      throw new Error("Acesso negado. Permissão insuficiente.");
    }

    throw new Error(body.detail || `API error: ${res.status}`);
  }

  return res.json();
}

export async function sendChat(data: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export interface StreamCallbacks {
  onToken: (token: string) => void;
  onMeta: (meta: { sources: ChatResponse["sources"]; model: string; chunks_used: number }) => void;
  onError: (error: string) => void;
  onDone: () => void;
}

export async function sendChatStream(data: ChatRequest, callbacks: StreamCallbacks): Promise<void> {
  const token = await getAccessToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}/api/chat/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    if (res.status === 401) throw new Error("Sessão expirada. Faça login novamente.");
    if (res.status === 403) throw new Error("Acesso negado. Permissão insuficiente.");
    throw new Error(body.detail || `API error: ${res.status}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("Streaming não suportado");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const event = JSON.parse(line.slice(6));
          if (event.type === "token") {
            callbacks.onToken(event.content);
          } else if (event.type === "meta") {
            callbacks.onMeta(event);
          } else if (event.type === "error") {
            callbacks.onError(event.content);
          } else if (event.type === "done") {
            callbacks.onDone();
          }
        } catch {
          // Ignore malformed JSON
        }
      }
    }
  }
}

export async function getFiles(): Promise<{ files: FileItem[] }> {
  return request<{ files: FileItem[] }>("/api/files");
}

export async function getStats(): Promise<StatsData> {
  return request<StatsData>("/api/stats");
}

export async function uploadFiles(files: FileList): Promise<UploadResult> {
  const token = await getAccessToken();
  const formData = new FormData();
  for (const file of Array.from(files)) {
    formData.append("files", file);
  }

  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}/api/upload`, {
    method: "POST",
    body: formData,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    if (res.status === 401) throw new Error("Sessão expirada. Faça login novamente.");
    if (res.status === 403) throw new Error("Acesso negado. Apenas administradores podem fazer upload.");
    throw new Error(body.detail || `Upload error: ${res.status}`);
  }

  return res.json();
}

export async function healthCheck(): Promise<{ status: string }> {
  return request<{ status: string }>("/api/health");
}

// Analytics
export interface TopQuery {
  query: string;
  count: number;
  query_hash: string;
}

export interface AnalyticsStats {
  total_queries: number;
  avg_latency_ms: number;
  avg_chunks_used: number;
  avg_score: number;
  intent_distribution: Record<string, number>;
  queries_per_day: Record<string, number>;
  period_days: number;
}

export async function getTopQueries(limit = 20, days = 30): Promise<{ queries: TopQuery[]; days: number }> {
  return request<{ queries: TopQuery[]; days: number }>(`/api/analytics/top-queries?limit=${limit}&days=${days}`);
}

export async function getAnalyticsStats(days = 30): Promise<AnalyticsStats> {
  return request<AnalyticsStats>(`/api/analytics/stats?days=${days}`);
}

// Admin Auth
export async function adminLogin(username: string, password: string): Promise<{ token: string; role: string }> {
  const res = await fetch(`${API_URL}/api/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Login falhou");
  }

  const data = await res.json();
  if (typeof window !== "undefined") {
    localStorage.setItem("admin_token", data.token);
  }
  return data;
}

export function adminLogout() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("admin_token");
  }
}

export function getAdminToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("admin_token");
  }
  return null;
}

// File management
export async function deleteFile(filename: string): Promise<{ action: string; filename: string; vectors_removed: number }> {
  return request(`/api/files/${encodeURIComponent(filename)}`, { method: "DELETE" });
}

export async function clearFileHistory(filename: string): Promise<{ action: string; filename: string; tombstones_removed: number }> {
  return request(`/api/files/${encodeURIComponent(filename)}/history`, { method: "DELETE" });
}

// Personas (Especialistas Virtuais)
export async function getPersonas(): Promise<{ personas: Persona[] }> {
  return request<{ personas: Persona[] }>("/api/personas");
}

export async function createPersona(data: Omit<Persona, "id">): Promise<Persona> {
  return request<Persona>("/api/personas", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updatePersona(id: string, data: Partial<Persona>): Promise<Persona> {
  return request<Persona>(`/api/personas/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deletePersona(id: string): Promise<{ detail: string }> {
  return request<{ detail: string }>(`/api/personas/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

// ======================== File Personas ========================

export async function updateFilePersonas(
  filename: string,
  personaIds: string[]
): Promise<{ message: string; vectors_updated: number }> {
  return request<{ message: string; vectors_updated: number }>(
    `/api/files/${encodeURIComponent(filename)}/personas`,
    {
      method: "PUT",
      body: JSON.stringify({ persona_ids: personaIds }),
    }
  );
}
