import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { chatApi } from "@/api/chat";
import { documentsApi } from "@/api/documents";
import type { Document, Message, TokenUsage } from "@/types";
import { MessageBubble } from "./MessageBubble";
import { 
  Cpu, 
  MessageSquare, 
  Database, 
  Zap, 
  Send, 
  Activity, 
  ArrowLeft,
  ChevronRight,
  ShieldCheck,
  Globe
} from "lucide-react";

export function ChatPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionDocuments, setSessionDocuments] = useState<Document[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [streamingTokenUsage, setStreamingTokenUsage] = useState<TokenUsage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadSession = useCallback(async () => {
    if (!sessionId) return;
    try {
      const session = await chatApi.getSession(sessionId);
      setMessages(session.messages);
      // Load document details for the session
      const docs = await Promise.all(
        session.documentIds.map((id) => documentsApi.get(id).catch(() => null))
      );
      setSessionDocuments(docs.filter((d): d is Document => d !== null));
    } catch {
      setError("Failed to synchronize session streams.");
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
      tokenUsage: null,
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsStreaming(true);
    setStreamingContent("");
    setStreamingTokenUsage(null);
    setError(null);

    chatApi.sendMessage(
      sessionId,
      userMessage.content,
      (token) => setStreamingContent((prev) => prev + token),
      (citations) => {
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
      (usage) => setStreamingTokenUsage(usage),
      () => {
        setIsStreaming(false);
        setStreamingContent("");
        setStreamingTokenUsage(null);
        loadSession();
      },
      (err) => {
        setIsStreaming(false);
        setStreamingContent("");
        setStreamingTokenUsage(null);
        setError(`Telemetry Fault: ${err}`);
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const totalTokens = messages.reduce((acc, msg) => acc + (msg.tokenUsage?.totalTokens || 0), 0);

  return (
    <div className="flex h-screen bg-black overflow-hidden relative">
      
      {/* 1. Intelligence Sidebar (col-span-3) */}
      <aside className="w-80 border-r border-white/5 bg-[#0a0a0a] flex flex-col shrink-0">
        <div className="p-6 border-b border-white/5">
          <Link to="/documents" className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors group mb-6">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-[10px] font-bold uppercase tracking-widest">Repository Atlas</span>
          </Link>
          <div className="space-y-1">
             <div className="flex items-center gap-2 text-primary">
                <Cpu className="w-4 h-4" />
                <span className="text-[10px] font-bold uppercase tracking-[0.3em]">Neural Session</span>
             </div>
             <h2 className="text-xl font-bold text-[#e2e2e2] truncate">Active Intelligence</h2>
             <p className="text-[10px] text-on-surface-variant font-mono">ID: {sessionId?.slice(0, 8)}</p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-8">
           {/* Metric Tiles */}
           <div className="space-y-4">
              <div className="glass-panel p-4 rounded-xl border-white/5">
                 <div className="flex justify-between items-center mb-2">
                    <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-widest">Total Compute</span>
                    <Zap className="w-3 h-3 text-primary" />
                 </div>
                 <div className="text-2xl font-bold text-[#e2e2e2] tabular-nums">{totalTokens.toLocaleString()}</div>
                 <p className="text-[9px] text-on-surface-variant mt-1">Intelligence Units (IU)</p>
              </div>

              <div className="glass-panel p-4 rounded-xl border-white/5 bg-emerald-400/5">
                 <div className="flex justify-between items-center mb-2">
                    <span className="text-[9px] font-bold text-emerald-400/60 uppercase tracking-widest">System Status</span>
                    <ShieldCheck className="w-3 h-3 text-emerald-400" />
                 </div>
                 <div className="text-sm font-bold text-emerald-400 uppercase tracking-tighter">Link Optimized</div>
              </div>
           </div>

           {/* Active Documents List */}
           <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest flex items-center gap-2">
                   <Database className="w-3 h-3" /> Source Matrix
                </h3>
                <span className="text-[10px] font-mono text-primary">Ready</span>
              </div>
              <div className="space-y-2">
                 {sessionDocuments.length === 0 ? (
                   <p className="text-[9px] text-on-surface-variant italic text-center py-4 border border-dashed border-white/5 rounded-lg">
                     Awaiting knowledge shards...
                   </p>
                 ) : (
                   sessionDocuments.map((doc) => (
                     <div key={doc.id} className="p-3 rounded-lg bg-white/5 border border-white/5 flex items-center justify-between group hover:bg-white/10 transition-colors cursor-default">
                       <div className="flex items-center gap-3">
                         <Database className="w-4 h-4 text-on-surface-variant" />
                         <span className="text-xs text-[#e2e2e2] font-medium truncate max-w-[120px]">{doc.filename}</span>
                       </div>
                       <ChevronRight className="w-3 h-3 text-on-surface-variant translate-x-2 opacity-0 group-hover:opacity-100 transition-all" />
                     </div>
                   ))
                 )}
              </div>
           </div>
        </div>

        <div className="p-6 border-t border-white/5 bg-black/20">
           <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-[0.2em]">Neural Uplink Stable</span>
           </div>
        </div>
      </aside>

      {/* 2. Neural Exchange (col-span-9) */}
      <main className="flex-1 flex flex-col bg-black relative">
        {/* Top Header */}
        <header className="h-16 border-b border-white/5 px-8 flex justify-between items-center bg-black/40 backdrop-blur-md z-20">
           <div className="flex items-center gap-4">
              <MessageSquare className="w-5 h-5 text-primary" />
              <h1 className="text-sm font-bold text-[#e2e2e2] uppercase tracking-[0.3em]">Neural Exchange</h1>
           </div>
           <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                 <Globe className="w-4 h-4 text-on-surface-variant" />
                 <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Global Protocol</span>
              </div>
              <button className="glass-panel px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-widest hover:bg-surface-container-high transition-all">
                 Share Stream
              </button>
           </div>
        </header>

        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto px-8 py-12 space-y-2">
           <div className="max-w-4xl mx-auto w-full">
            {messages.length === 0 && !isStreaming && (
              <div className="h-[60vh] flex flex-col items-center justify-center text-center space-y-6">
                <div className="relative">
                   <div className="absolute inset-0 bg-primary/20 blur-[60px] rounded-full animate-pulse" />
                   <Cpu className="w-16 h-16 text-primary relative z-10" />
                </div>
                <div>
                   <h2 className="text-2xl font-bold text-[#e2e2e2] mb-2 tracking-tight">System Virtualized</h2>
                   <p className="text-on-surface-variant text-sm max-w-sm mx-auto leading-relaxed uppercase tracking-widest text-[10px] font-bold opacity-60">
                      Knowledge matrix loaded. Input query to begin neural extraction.
                   </p>
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Streaming placeholder */}
            {isStreaming && streamingContent && (
              <MessageBubble 
                message={{
                  id: "streaming",
                  role: "assistant",
                  content: streamingContent,
                  citations: [],
                  createdAt: new Date().toISOString(),
                  tokenUsage: streamingTokenUsage || null
                }} 
              />
            )}

            {error && (
              <div className="glass-panel border-red-500/20 bg-red-500/5 p-4 rounded-xl text-center flex items-center justify-center gap-3 text-red-400 text-xs font-bold uppercase tracking-widest">
                <Activity className="w-4 h-4" />
                {error}
              </div>
            )}

            <div ref={bottomRef} className="h-24" />
           </div>
        </div>

        {/* Fixed Input Area */}
        <div className="p-8 bg-gradient-to-t from-black via-black/80 to-transparent absolute bottom-0 left-0 right-0 z-20">
           <div className="max-w-4xl mx-auto relative group">
              <div className="absolute -inset-1 bg-primary/20 rounded-2xl blur opacity-0 group-focus-within:opacity-100 transition-opacity" />
              <div className="relative glass-panel rounded-2xl border-white/10 p-2 flex items-end gap-2 bg-[#121212]/80 backdrop-blur-xl">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Input neural query..."
                  rows={1}
                  className="flex-1 bg-transparent border-none focus:ring-0 text-[#e2e2e2] text-sm py-3 px-4 resize-none placeholder:text-on-surface-variant/40"
                  style={{ maxHeight: "200px" }}
                />
                <button
                  onClick={handleSend}
                  disabled={isStreaming || !input.trim()}
                  className="p-3 rounded-xl bg-primary text-black hover:bg-[#adc6ff] disabled:opacity-20 disabled:cursor-not-allowed transition-all mb-1 mr-1 shadow-lg shadow-primary/20 hover:scale-105"
                >
                  <Send className="w-5 h-5 fill-current" />
                </button>
              </div>
              <div className="mt-3 flex justify-between items-center px-2">
                 <div className="flex gap-4">
                    <span className="text-[9px] font-bold text-on-surface-variant/40 uppercase tracking-widest flex items-center gap-1">
                       <ChevronRight className="w-3 h-3" /> Global Search
                    </span>
                    <span className="text-[9px] font-bold text-on-surface-variant/40 uppercase tracking-widest flex items-center gap-1">
                       <ChevronRight className="w-3 h-3" /> Citations Enabled
                    </span>
                 </div>
                 <span className="text-[9px] font-bold text-on-surface-variant/40 uppercase tracking-widest">
                    Press <span className="text-on-surface-variant">Enter</span> to transmit
                 </span>
              </div>
           </div>
        </div>
      </main>

      {/* Decorative Atmosphere */}
      <div className="absolute top-0 right-0 w-[30%] h-[30%] bg-primary/5 blur-[120px] rounded-full pointer-events-none -z-10 animate-pulse" />
      <div className="absolute bottom-0 left-0 w-[40%] h-[40%] bg-secondary/5 blur-[150px] rounded-full pointer-events-none -z-10" />

    </div>
  );
}
