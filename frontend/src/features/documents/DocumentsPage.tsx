import { useCallback, useEffect, useRef, useState } from "react";
import { useDropzone } from "react-dropzone";
import { documentsApi } from "@/api/documents";
import type { Document } from "@/types";
import { 
  LayoutDashboard, 
  Upload, 
  Database, 
  FileText, 
  Activity,
  ShieldCheck,
  Zap,
  Plus
} from "lucide-react";
import { Link } from "react-router-dom";
import { BentoGrid, type BentoItem } from "@/components/ui/bento-grid";
import { cn } from "@/lib/utils";

const STATUS_CONFIG: Record<string, { color: string; label: string }> = {
  pending: { color: "text-amber-400 bg-amber-400/10", label: "Queueing" },
  processing: { color: "text-blue-400 bg-blue-400/10 animate-pulse", label: "Indexing" },
  ready: { color: "text-emerald-400 bg-emerald-400/10", label: "Neural Link Active" },
  failed: { color: "text-red-400 bg-red-400/10", label: "System Fault" },
};

const ACCEPTED_EXTENSIONS = {
  "application/pdf": [".pdf"],
  "text/plain": [".txt"],
  "text/markdown": [".md"],
  "text/csv": [".csv"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
  "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
};

export function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadDocuments = useCallback(async () => {
    try {
      const result = await documentsApi.list();
      setDocuments(result.items);
    } catch {
      setError("Failed to synchronize repository atlas.");
    }
  }, []);

  useEffect(() => {
    loadDocuments();
    pollingRef.current = setInterval(loadDocuments, 5000);
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [loadDocuments]);

  const handleDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;
      setIsUploading(true);
      setError(null);
      try {
        await Promise.all(acceptedFiles.map((f) => documentsApi.upload(f)));
        await loadDocuments();
      } catch {
        setError("Uplink failed. Data stream rejected.");
      } finally {
        setIsUploading(false);
      }
    },
    [loadDocuments]
  );

  const handleDelete = async (id: string) => {
    try {
      await documentsApi.delete(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch {
      setError("Purge protocols failed. Matrix persistent.");
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleDrop,
    accept: ACCEPTED_EXTENSIONS,
    multiple: true,
  });

  const stats = {
    total: documents.length,
    active: documents.filter(d => d.status === 'ready').length,
    processing: documents.filter(d => d.status === 'processing').length,
  };

  const documentItems: BentoItem[] = documents.map((doc) => {
    const config = STATUS_CONFIG[doc.status] || { color: "text-gray-400", label: doc.status };
    return {
      title: doc.filename,
      description: `${doc.tokensEmbedded?.toLocaleString() || 0} Neural Intelligence Units initialized.`,
      icon: <FileText className="w-5 h-5" />,
      status: config.label,
      meta: doc.fileType.toUpperCase(),
      cta: "Purge Shard",
      onClick: () => handleDelete(doc.id),
      className: "hover:border-primary/20",
    };
  });

  return (
    <div className="p-8 md:p-16 max-w-[1400px] mx-auto space-y-12">
      
      {/* Header HUD: Architectural Layout */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 relative">
        <div className="space-y-2">
           <div className="flex items-center gap-3 text-primary">
              <Database className="w-5 h-5" />
              <span className="text-[10px] font-bold uppercase tracking-[0.5em] opacity-80 font-body">Data Repository</span>
           </div>
           <h1 className="text-4xl md:text-5xl font-bold tracking-tighter text-[#e2e2e2]">Document Atlas</h1>
           <p className="text-on-surface-variant text-sm font-medium opacity-60">System Version 2.8.4 | Matrix Status: Synchronized</p>
        </div>
        
        <div className="flex gap-4">
           <Link to="/chat" className="glass-panel px-6 py-3 rounded-xl flex items-center gap-3 group bg-white/5 border-white/5 hover:bg-white/10 transition-all">
              <Plus className="w-4 h-4 text-primary group-hover:rotate-90 transition-all duration-300" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface">Neural Session</span>
           </Link>
           <div className="glass-panel px-6 py-3 rounded-xl flex items-center gap-3 bg-[#adc6ff] text-black shadow-[0_0_24px_rgba(173,198,255,0.2)]">
              <ShieldCheck className="w-4 h-4" />
              <span className="text-[10px] font-bold uppercase tracking-widest">Secure Uplink</span>
           </div>
        </div>
      </div>

      {error && (
        <div className="glass-panel border-red-500/20 bg-red-500/5 p-4 rounded-xl text-[11px] font-bold uppercase tracking-widest text-red-400 flex items-center gap-3 animate-pulse">
           <Activity className="w-4 h-4" />
           {error}
        </div>
      )}

      {/* Main Grid Ecosystem */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        
        {/* Analytics Module (8 cols) */}
        <div className="md:col-span-8 glass-panel rounded-3xl p-10 flex flex-col justify-between border-white/[0.03] bg-gradient-to-br from-[#121212] to-black relative group overflow-hidden">
           <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 blur-[100px] pointer-events-none -z-10" />
           
           <div className="flex justify-between items-start">
              <div className="space-y-2">
                 <div className="flex items-center gap-2 text-primary">
                    <LayoutDashboard className="w-5 h-5 font-bold" />
                    <span className="text-[10px] font-bold uppercase tracking-[0.4em]">Intelligence Matrix</span>
                 </div>
                 <h2 className="text-3xl font-bold tracking-tight text-[#e2e2e2]">System Telemetry</h2>
              </div>
              <div className="p-3 bg-white/5 rounded-2xl border border-white/10 group-hover:bg-primary/10 transition-all">
                 <Zap className="w-5 h-5 text-primary" />
              </div>
           </div>

           <div className="grid grid-cols-3 gap-12 mt-12">
              <div className="space-y-2">
                 <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest opacity-40">Total Shards</span>
                 <div className="text-5xl font-bold text-[#e2e2e2] tracking-tighter tabular-nums">{stats.total}</div>
              </div>
              <div className="space-y-2 border-l border-white/5 pl-12">
                 <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest opacity-40">Direct Access</span>
                 <div className="text-5xl font-bold text-emerald-400 tracking-tighter tabular-nums">{stats.active}</div>
              </div>
              <div className="space-y-2 border-l border-white/5 pl-12">
                 <span className="text-[10px] font-bold text-blue-500 uppercase tracking-widest opacity-40">Contextualizing</span>
                 <div className="text-5xl font-bold text-blue-400 tracking-tighter tabular-nums">{stats.processing}</div>
              </div>
           </div>
        </div>

        {/* Ingestion Portal (4 cols) */}
        <div 
          {...getRootProps()}
          className={cn(
            "md:col-span-4 rounded-3xl p-10 flex flex-col items-center justify-center text-center cursor-pointer group transition-all relative overflow-hidden border border-white/5",
            isDragActive ? "bg-primary/20 border-primary" : "bg-surface-container-low hover:bg-white/[0.04]"
          )}
        >
           <input {...getInputProps()} />
           <div className="relative z-10 space-y-6">
              <div className="w-20 h-20 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mx-auto group-hover:scale-110 group-hover:border-primary/40 transition-all duration-500">
                 <Upload className={cn("w-10 h-10 transition-all duration-300", isUploading ? "animate-bounce text-primary" : "text-on-surface-variant group-hover:text-primary")} />
              </div>
              <div>
                 <h3 className="text-xl font-bold text-[#e2e2e2] tracking-tight">Data Ingestion</h3>
                 <p className="text-xs font-medium text-on-surface-variant mt-2 leading-relaxed opacity-60">
                    {isUploading ? "Streaming to Neural core..." : "Drop matrices here to initialize context streams."}
                 </p>
              </div>
           </div>
           <Database className="absolute -bottom-8 -right-8 w-40 h-40 opacity-[0.02] rotate-12 group-hover:opacity-[0.05] transition-all duration-700" />
        </div>

        {/* Global Registry Section */}
        <div className="md:col-span-12 space-y-8">
           <div className="flex justify-between items-center px-4">
              <div className="flex items-center gap-3">
                 <Database className="w-5 h-5 text-primary" />
                 <h3 className="text-xl font-bold tracking-tight text-[#e2e2e2]">Synchronized Shards</h3>
              </div>
              <div className="flex items-center gap-2">
                 <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                 <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest mt-0.5">Live Feed</span>
              </div>
           </div>

           {documents.length === 0 ? (
             <div className="py-32 glass-panel rounded-3xl flex flex-col items-center gap-6 text-center border-dashed border-white/10">
                <FileText className="w-16 h-16 text-on-surface-variant/10" />
                <p className="text-[10px] font-bold text-on-surface-variant uppercase tracking-[0.4em] opacity-40">No Matrices Found in Repository</p>
             </div>
           ) : (
             <BentoGrid items={documentItems} className="md:grid-cols-4" />
           )}
        </div>

      </div>
    </div>
  );
}
