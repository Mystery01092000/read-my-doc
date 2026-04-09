import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { chatApi } from "@/api/chat";
import { documentsApi } from "@/api/documents";
import { useAuth } from "@/hooks/useAuth";
import type { ChatSession, Document } from "@/types";
import { 
  Plus, 
  MessageSquare, 
  LogOut, 
  Database, 
  ChevronRight, 
  Cpu,
  Layers,
  Search,
  Check
} from "lucide-react";
import { cn } from "@/lib/utils";

export function SessionSidebar() {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [showNewModal, setShowNewModal] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<Set<string>>(new Set());
  const [isCreating, setIsCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const loadSessions = async () => {
    try {
      const result = await chatApi.listSessions();
      setSessions(result.items);
    } catch {
      // silently ignore
    }
  };

  useEffect(() => {
    loadSessions();
  }, [sessionId]);

  const openNewModal = async () => {
    try {
      const result = await documentsApi.list(1, 100);
      setDocuments(result.items.filter((d) => d.status === "ready"));
    } catch {
      setDocuments([]);
    }
    setSelectedDocIds(new Set());
    setShowNewModal(true);
  };

  const createSession = async () => {
    if (selectedDocIds.size === 0) return;
    setIsCreating(true);
    try {
      const session = await chatApi.createSession([...selectedDocIds]);
      setShowNewModal(false);
      await loadSessions();
      navigate(`/chat/${session.id}`);
    } catch {
      // error handling
    } finally {
      setIsCreating(false);
    }
  };

  const toggleDoc = (id: string) => {
    setSelectedDocIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const filteredSessions = sessions.filter(s => 
    s.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      <aside className="w-72 border-r border-white/5 bg-[#080808] flex flex-col h-screen relative z-30 font-body">
        {/* TOP HUD: Branding & Actions */}
        <div className="p-6 border-b border-white/5 space-y-6">
           <div className="flex items-center justify-between">
              <Link to="/documents" className="flex flex-col gap-0.5 group">
                 <span className="text-[10px] font-bold text-primary uppercase tracking-[0.4em] transition-all group-hover:tracking-[0.5em]">Neural Link</span>
                 <h1 className="text-xl font-bold tracking-tighter text-[#e2e2e2]">ReadMyDoc</h1>
              </Link>
              <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)] animate-pulse" />
           </div>

           <button
            onClick={openNewModal}
            className="w-full relative group"
           >
              <div className="absolute -inset-0.5 bg-primary/20 rounded-xl blur-lg opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative flex items-center justify-center gap-3 py-3 rounded-xl bg-primary text-black font-bold text-[11px] uppercase tracking-widest hover:bg-[#adc6ff] transition-all">
                 <Plus className="w-4 h-4" /> Initialize Chat
              </div>
           </button>
        </div>

        {/* SEARCH & FILTERS */}
        <div className="px-6 py-4">
           <div className="relative group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-on-surface-variant group-focus-within:text-primary transition-colors" />
              <input 
                type="text" 
                placeholder="Locate session..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-white/5 border-white/5 rounded-lg pl-9 pr-4 py-2 text-[11px] text-on-surface placeholder:text-on-surface-variant/40 focus:ring-1 focus:ring-primary/40 focus:border-primary/40 transition-all font-mono"
              />
           </div>
        </div>

        {/* SESSION LIST: "Neural Streams" */}
        <div className="flex-1 overflow-y-auto px-4 py-2 space-y-1 scrollbar-hide">
           <div className="px-2 pb-2">
              <span className="text-[9px] font-bold text-on-surface-variant/40 uppercase tracking-widest">Active Streams</span>
           </div>

           {filteredSessions.length === 0 ? (
             <div className="py-12 flex flex-col items-center justify-center gap-4 text-center opacity-40">
                <Layers className="w-8 h-8 text-on-surface-variant" />
                <p className="text-[10px] font-bold uppercase tracking-widest max-w-[120px]">Matrix Empty</p>
             </div>
           ) : (
             filteredSessions.map((s) => (
              <Link
                key={s.id}
                to={`/chat/${s.id}`}
                className={cn(
                  "flex items-center justify-between group px-4 py-3 rounded-xl transition-all relative overflow-hidden",
                  s.id === sessionId 
                    ? "bg-white/5 border border-white/10" 
                    : "hover:bg-white/5 border border-transparent"
                )}
              >
                {s.id === sessionId && (
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary shadow-[0_0_12px_rgba(173,198,255,0.4)]" />
                )}
                <div className="flex items-center gap-3 truncate">
                   <MessageSquare className={cn("w-4 h-4", s.id === sessionId ? "text-primary" : "text-on-surface-variant")} />
                   <span className={cn(
                     "text-xs truncate font-medium",
                     s.id === sessionId ? "text-[#e2e2e2]" : "text-on-surface-variant group-hover:text-on-surface"
                   )}>
                      {s.title}
                   </span>
                </div>
                <ChevronRight className={cn(
                  "w-3 h-3 transition-all",
                  s.id === sessionId ? "text-primary translate-x-0" : "text-on-surface-variant opacity-0 translate-x-2 group-hover:opacity-100 group-hover:translate-x-0"
                )} />
              </Link>
             ))
           )}
        </div>

        {/* BOTTOM HUD: Meta & Actions */}
        <div className="p-6 border-t border-white/5 bg-black/20 space-y-4">
           <div className="flex items-center justify-between px-2">
              <div className="flex items-center gap-2">
                 <Cpu className="w-3.5 h-3.5 text-primary" />
                 <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">System Atlas</span>
              </div>
              <button 
                onClick={logout}
                className="p-2 rounded-lg hover:bg-red-500/10 text-on-surface-variant hover:text-red-500 transition-all"
              >
                 <LogOut className="w-4 h-4" />
              </button>
           </div>
           
           <div className="glass-panel p-3 rounded-xl border-white/5 bg-white/[0.02]">
              <div className="flex justify-between items-center mb-1">
                 <span className="text-[8px] font-bold text-on-surface-variant uppercase tracking-widest opacity-40">Uptime</span>
                 <span className="text-[8px] font-mono text-emerald-500 font-bold tracking-widest">STABLE</span>
              </div>
              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                 <div className="h-full bg-primary/40 w-[85%]" />
              </div>
           </div>
        </div>
      </aside>

      {/* NEW CHAT MODAL: Bento Style */}
      {showNewModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
           <div 
             className="w-full max-w-2xl glass-panel rounded-3xl border-white/10 shadow-[0_32px_128px_-16px_rgba(0,0,0,0.8)] overflow-hidden flex flex-col max-h-[80vh]"
             onClick={(e) => e.stopPropagation()}
           >
              {/* Modal Atmosphere Decor */}
              <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 blur-[100px] pointer-events-none" />
              <div className="absolute bottom-0 left-0 w-64 h-64 bg-secondary/5 blur-[120px] pointer-events-none" />

              <div className="p-8 border-b border-white/5 relative z-10 flex justify-between items-center">
                 <div className="space-y-1">
                    <div className="flex items-center gap-2 text-primary">
                       <Database className="w-4 h-4" />
                       <span className="text-[10px] font-bold uppercase tracking-[0.4em]">Resource Selector</span>
                    </div>
                    <h2 className="text-2xl font-bold tracking-tight text-[#e2e2e2]">Synchronize Shards</h2>
                    <p className="text-on-surface-variant text-sm font-medium">Select document matrices to merge into neural context.</p>
                 </div>
                 <button 
                  onClick={() => setShowNewModal(false)}
                  className="p-3 rounded-full hover:bg-white/5 transition-colors text-on-surface-variant"
                 >
                    <Plus className="w-6 h-6 rotate-45" />
                 </button>
              </div>

              <div className="flex-1 overflow-y-auto p-8 relative z-10 space-y-6">
                {documents.length === 0 ? (
                  <div className="py-20 flex flex-col items-center gap-4 text-center">
                     <div className="w-16 h-16 rounded-3xl bg-white/5 flex items-center justify-center">
                        <Database className="w-8 h-8 text-on-surface-variant opacity-40" />
                     </div>
                     <div>
                        <p className="text-on-surface-variant font-bold text-[10px] uppercase tracking-widest leading-relaxed"> No Valid Matrices Detected.<br/>Perform Data Ingestion first. </p>
                     </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-4">
                     {documents.map((doc) => (
                       <div 
                         key={doc.id}
                         onClick={() => toggleDoc(doc.id)}
                         className={cn(
                           "p-4 rounded-2xl border transition-all cursor-pointer group flex flex-col gap-4",
                           selectedDocIds.has(doc.id) 
                             ? "bg-primary/5 border-primary shadow-[0_0_32px_-8px_rgba(173,198,255,0.2)]" 
                             : "bg-white/[0.02] border-white/5 hover:border-white/20"
                         )}
                       >
                          <div className="flex justify-between items-start">
                             <div className={cn(
                               "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
                               selectedDocIds.has(doc.id) ? "bg-primary text-black" : "bg-white/5 text-on-surface-variant"
                             )}>
                                <Database className="w-5 h-5" />
                             </div>
                             {selectedDocIds.has(doc.id) && (
                               <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                                  <Check className="w-4 h-4 text-black" />
                               </div>
                             )}
                          </div>
                          <div>
                             <h4 className={cn(
                               "text-[10px] font-bold uppercase tracking-widest truncate",
                               selectedDocIds.has(doc.id) ? "text-primary" : "text-on-surface-variant"
                             )}>{doc.filename}</h4>
                             <p className="text-xs font-medium text-on-surface-variant/60 mt-1">Ready for Neural Link</p>
                          </div>
                       </div>
                     ))}
                  </div>
                )}
              </div>

              <div className="p-8 border-t border-white/5 bg-black/40 relative z-10 flex justify-between items-center">
                 <div className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                    {selectedDocIds.size} Matrices Selected
                 </div>
                 <div className="flex gap-4">
                    <button
                      onClick={() => setShowNewModal(false)}
                      className="px-6 py-2 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant hover:text-on-surface transition-colors"
                    >
                      Abort
                    </button>
                    <button
                      onClick={createSession}
                      disabled={selectedDocIds.size === 0 || isCreating}
                      className="px-8 py-3 rounded-xl bg-primary text-black font-bold text-[11px] uppercase tracking-widest hover:bg-[#adc6ff] disabled:opacity-20 transition-all shadow-lg shadow-primary/10"
                    >
                      {isCreating ? "Initializing..." : "Transmit Session"}
                    </button>
                 </div>
              </div>
           </div>
        </div>
      )}
    </>
  );
}
