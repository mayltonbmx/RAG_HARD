export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: SourceItem[];
}

export interface SourceItem {
  filename: string;
  score: number;
  type_label: string;
  file_type: string;
}

export interface ChatRequest {
  message: string;
  history?: { role: string; content: string }[];
  top_k?: number;
  persona_id?: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceItem[];
  model: string;
  chunks_used: number;
}

export interface FileItem {
  path: string;
  name: string;
  extension: string;
  mime_type: string;
  size_mb: number;
  modified: string;
  status: "active" | "deleted";
  vectors_count: number;
  on_disk: boolean;
  deleted_at: string;
  allowed_personas: string[];
}

export interface StatsData {
  total_vectors: number;
  dimension: number;
  index_fullness: number;
  model: string;
  total_files: number;
}

export interface UploadResult {
  success: string[];
  errors: { file: string; error: string }[];
}

// Personas (Especialistas Virtuais)
export interface Persona {
  id: string;
  name: string;
  description: string;
  identity: string;
  rules: string[];
  temperature: number;
  access_level: "public" | "logged_in";
  is_default: boolean;
}

export type ViewType = "chat" | "upload" | "files" | "stats" | "analytics" | "personas";
