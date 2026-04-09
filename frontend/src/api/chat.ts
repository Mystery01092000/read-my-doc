import type { ChatSession, ChatSessionDetailResponse, Message, PaginatedResponse, TokenUsage } from "@/types";
import { createApiClient } from "./client";
import { useAuthStore } from "@/store/useAuthStore";

function client() {
  return createApiClient(() => useAuthStore.getState().accessToken);
}

export const chatApi = {
  listSessions: async (page = 1, limit = 20): Promise<PaginatedResponse<ChatSession>> => {
    const { data } = await client().get<PaginatedResponse<ChatSession>>("/chat/sessions", {
      params: { page, limit },
    });
    return data;
  },

  createSession: async (documentIds: string[], title?: string): Promise<ChatSession> => {
    const { data } = await client().post<ChatSession>("/chat/sessions", {
      document_ids: documentIds,
      title,
    });
    return data;
  },

  getSession: async (sessionId: string): Promise<ChatSessionDetailResponse> => {
    const { data } = await client().get<ChatSessionDetailResponse>(`/chat/sessions/${sessionId}`);
    return data;
  },

  deleteSession: async (sessionId: string): Promise<void> => {
    await client().delete(`/chat/sessions/${sessionId}`);
  },

  sendMessage: (
    sessionId: string,
    content: string,
    onToken: (token: string) => void,
    onCitations: (citations: Message["citations"]) => void,
    onTokenUsage: (usage: TokenUsage) => void,
    onDone: () => void,
    onError: (err: string) => void
  ): void => {
    const token = useAuthStore.getState().accessToken;
    const es = new EventSource(
      `/api/chat/sessions/${sessionId}/messages?content=${encodeURIComponent(content)}`,
      // Note: EventSource doesn't support POST — we use fetch with streams instead
    );
    // Use fetch + ReadableStream for POST SSE
    es.close();

    const BASE_URL = import.meta.env.VITE_API_URL ?? "/api";
    fetch(`${BASE_URL}/chat/sessions/${sessionId}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ content }),
    })
      .then(async (res) => {
        if (!res.ok || !res.body) {
          onError(`Request failed: ${res.status}`);
          return;
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const data = line.slice(6).trim();
            if (data === "[DONE]") {
              onDone();
              return;
            }
            try {
              const parsed = JSON.parse(data) as {
                type: "token" | "citations" | "token_usage";
                content?: string;
                citations?: Message["citations"];
                token_usage?: TokenUsage;
              };
              if (parsed.type === "token" && parsed.content) {
                onToken(parsed.content);
              } else if (parsed.type === "citations" && parsed.citations) {
                onCitations(parsed.citations);
              } else if (parsed.type === "token_usage" && parsed.token_usage) {
                const u = parsed.token_usage as Record<string, number>;
                onTokenUsage({
                  promptTokens: u.prompt_tokens ?? 0,
                  completionTokens: u.completion_tokens ?? 0,
                  llmTokens: u.llm_tokens ?? 0,
                  embeddingTokens: u.embedding_tokens ?? 0,
                  rerankTokens: u.rerank_tokens ?? 0,
                  totalTokens: u.total_tokens ?? 0,
                });
              }
            } catch {
              // ignore malformed lines
            }
          }
        }
        onDone();
      })
      .catch((err) => onError(String(err)));
  },
};
