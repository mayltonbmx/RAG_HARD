import { ChatRequest, ChatResponse, FileItem, StatsData, UploadResult } from "@/types";
import { getSession } from "next-auth/react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

/**
 * Get the access token from the current session.
 */
async function getAccessToken(): Promise<string | undefined> {
  const session = await getSession();
  return session?.accessToken;
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
