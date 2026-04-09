// ── Auth ─────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  name: string;
  phone: string | null;
  email: string;
  createdAt: string;
}

export interface TokenPair {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
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
  tokensEmbedded: number | null;
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

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  llmTokens: number;
  embeddingTokens: number;
  rerankTokens: number;
  totalTokens: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  tokenUsage: TokenUsage | null;
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
