import { useState } from "react";
import type { Citation } from "@/types";
import { Link2, X, FileText } from "lucide-react";

interface Props {
  citation: Citation;
  index: number;
}

export function CitationChip({ citation, index }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-tighter bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 transition-all group"
        title={`${citation.filename}${citation.page ? `, p.${citation.page}` : ""}`}
      >
        <Link2 className="w-3 h-3 group-hover:rotate-45 transition-transform" />
        Link [{index + 1}]
      </button>

      {open && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
          onClick={() => setOpen(false)}
        >
          <div
            className="glass-panel w-full max-w-lg rounded-xl shadow-2xl p-8 relative animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setOpen(false)}
              className="absolute top-4 right-4 p-2 text-on-surface-variant hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-4 mb-6">
              <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
                <FileText className="w-6 h-6 text-primary" />
              </div>
              <div>
                <p className="font-headline font-bold text-lg text-[#e2e2e2] tracking-tight truncate max-w-[300px]">
                  {citation.filename}
                </p>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-primary uppercase tracking-widest">Source Fragment</span>
                  {citation.page && (
                    <>
                      <span className="text-[10px] text-on-surface-variant">•</span>
                      <span className="text-[10px] text-on-surface-variant uppercase font-bold tracking-widest">Page {citation.page}</span>
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="relative">
              <div className="absolute -left-4 top-0 bottom-0 w-1 bg-primary/40 rounded-full" />
              <blockquote className="text-sm text-on-surface-variant leading-relaxed italic">
                "{citation.snippet}"
              </blockquote>
            </div>

            <div className="mt-8 pt-6 border-t border-white/5 flex justify-between items-center">
               <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-[0.2em]">Neural Verification Active</span>
               <button className="text-[10px] font-bold text-primary uppercase tracking-widest hover:text-white transition-colors">
                  Open Original Archive
               </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
