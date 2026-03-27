import { ChatRequest, ChatResponse, FileItem, StatsData, UploadResult } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
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
  const formData = new FormData();
  for (const file of Array.from(files)) {
    formData.append("files", file);
  }

  const res = await fetch(`${API_URL}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Upload error: ${res.status}`);
  }

  return res.json();
}

export async function healthCheck(): Promise<{ status: string }> {
  return request<{ status: string }>("/api/health");
}
