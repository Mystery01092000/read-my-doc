import ReactMarkdown from "react-markdown";
import type { Message } from "@/types";
import { CitationChip } from "./CitationChip";
import { User, Cpu, Info } from "lucide-react";

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-6 group`}>
      <div className={`flex gap-4 max-w-[85%] ${isUser ? "flex-row-reverse" : "flex-row"}`}>
        
        {/* Avatar / Icon Container */}
        <div className={`mt-1 shrink-0 w-8 h-8 rounded-lg flex items-center justify-center border transition-all
          ${isUser 
            ? "bg-primary/10 border-primary/20 text-primary group-hover:bg-primary/20" 
            : "bg-surface-container-highest border-white/5 text-on-surface-variant group-hover:border-primary/20"}`}>
          {isUser ? <User className="w-4 h-4" /> : <Cpu className="w-4 h-4" />}
        </div>

        {/* Message Content */}
        <div className="flex flex-col gap-2">
          <div
            className={`rounded-2xl px-5 py-3.5 text-sm leading-relaxed relative overflow-hidden
              ${isUser
                ? "bg-surface-container-highest text-[#e2e2e2] border border-white/5"
                : "glass-panel text-[#e2e2e2] border-white/5"
            }`}
          >
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <div className="prose prose-sm prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-black/40 prose-pre:border prose-pre:border-white/5">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            )}
            
            {/* Background Atmosphere for Assistant Messages */}
            {!isUser && (
              <div className="absolute -top-12 -right-12 w-24 h-24 bg-primary/5 blur-[40px] rounded-full pointer-events-none"></div>
            )}
          </div>

          {/* Citations & Meta */}
          {!isUser && (
            <div className="flex flex-wrap items-center gap-3 ml-1">
              {message.citations.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {message.citations.map((cit, i) => (
                    <CitationChip key={cit.chunkId} citation={cit} index={i} />
                  ))}
                </div>
              )}
              
              {message.tokenUsage && (
                <div className="group/meta relative inline-flex items-center gap-1 cursor-default">
                  <Info className="w-3 h-3 text-on-surface-variant/40" />
                  <span className="text-[9px] font-bold text-on-surface-variant/40 uppercase tracking-widest">
                    {message.tokenUsage.total_tokens} Intelligence Units
                  </span>
                  
                  {/* Tooltip for usage details */}
                  <div className="absolute bottom-full left-0 mb-2 invisible group-hover/meta:visible opacity-0 group-hover/meta:opacity-100 transition-all z-20">
                     <div className="glass-panel p-3 rounded-lg border-white/5 text-[9px] whitespace-nowrap space-y-1 shadow-2xl">
                        <div className="flex justify-between gap-4">
                           <span className="text-on-surface-variant uppercase tracking-widest">LLM Compute</span>
                           <span className="text-primary font-bold">{message.tokenUsage.llm_tokens}</span>
                        </div>
                        <div className="flex justify-between gap-4">
                           <span className="text-on-surface-variant uppercase tracking-widest">Neural Embed</span>
                           <span className="text-primary font-bold">{message.tokenUsage.embedding_tokens}</span>
                        </div>
                        <div className="flex justify-between gap-4">
                           <span className="text-on-surface-variant uppercase tracking-widest">Link Rerank</span>
                           <span className="text-primary font-bold">{message.tokenUsage.rerank_tokens}</span>
                        </div>
                     </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
