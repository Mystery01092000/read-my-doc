import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { chatApi } from "@/api/chat";
import type { Message, Citation } from "@/types";
import { MessageBubble } from "./MessageBubble";

export function ChatPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadSession = useCallback(async () => {
    if (!sessionId) return;
    try {
      const session = await chatApi.getSession(sessionId);
      setMessages(session.messages);
    } catch {
      setError("Failed to load session");
    }
  }, [sessionId]);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const handleSend = () => {
    if (!sessionId || !input.trim() || isStreaming) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: input,
      citations: [],
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsStreaming(true);
    setStreamingContent("");
    setError(null);

    chatApi.sendMessage(
      sessionId,
      userMessage.content,
      (token) => setStreamingContent((prev) => prev + token),
      (citations) => {
        // Citations arrive at end — merge into the streamed message
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === "assistant") {
            return [
              ...prev.slice(0, -1),
              { ...last, citations },
            ];
          }
          return prev;
        });
      },
      () => {
        setIsStreaming(false);
        setMessages((prev) => {
          const assistantMessage: Message = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: streamingContent,
            citations: [],
            createdAt: new Date().toISOString(),
          };
          // Replace streaming placeholder with final message
          return [...prev, assistantMessage];
        });
        setStreamingContent("");
        loadSession(); // Refresh to get server-persisted message with citations
      },
      (err) => {
        setIsStreaming(false);
        setStreamingContent("");
        setError(`Error: ${err}`);
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 && !isStreaming && (
          <p className="text-center text-sm text-gray-400 mt-20">
            Ask a question about your documents.
          </p>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Streaming placeholder */}
        {isStreaming && streamingContent && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-2xl rounded-bl-sm px-4 py-3 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100">
              <p className="whitespace-pre-wrap">{streamingContent}</p>
              <span className="inline-block w-1.5 h-4 bg-gray-400 animate-pulse ml-1 align-middle" />
            </div>
          </div>
        )}

        {error && (
          <div className="text-center text-sm text-red-500">{error}</div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 px-4 py-3">
        <div className="flex gap-2 items-end max-w-3xl mx-auto">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question… (Enter to send, Shift+Enter for newline)"
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500"
            style={{ maxHeight: "120px", overflowY: "auto" }}
          />
          <button
            onClick={handleSend}
            disabled={isStreaming || !input.trim()}
            className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isStreaming ? "…" : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}
