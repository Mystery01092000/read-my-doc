// ── Auth ─────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  createdAt: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ── Documents ─────────────────────────────────────────────────────────────────

export type DocumentStatus = "pending" | "processing" | "ready" | "failed";
export type FileType = "pdf" | "txt" | "md" | "csv" | "xlsx" | "pptx";

export interface Document {
  id: string;
  filename: string;
  fileType: FileType;
  fileSizeBytes: number;
  status: DocumentStatus;
  errorMessage: string | null;
  pageCount: number | null;
  createdAt: string;
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export interface Citation {
  chunkId: string;
  documentId: string;
  filename: string;
  page: number | null;
  snippet: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  createdAt: string;
}

export interface ChatSession {
  id: string;
  title: string;
  documentIds: string[];
  createdAt: string;
  updatedAt: string;
}

export interface ChatSessionDetailResponse extends ChatSession {
  messages: Message[];
}

// ── API Envelope ──────────────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}
