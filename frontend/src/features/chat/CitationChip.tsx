import { useState } from "react";
import type { Citation } from "@/types";

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
        className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
        title={`${citation.filename}${citation.page ? `, p.${citation.page}` : ""}`}
      >
        [{index + 1}]
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/40"
          onClick={() => setOpen(false)}
        >
          <div
            className="w-full max-w-lg rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-xl p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  {citation.filename}
                </p>
                {citation.page && (
                  <p className="text-xs text-gray-500 mt-0.5">Page {citation.page}</p>
                )}
              </div>
              <button
                onClick={() => setOpen(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-lg leading-none"
              >
                ✕
              </button>
            </div>
            <blockquote className="border-l-2 border-blue-400 pl-4 text-sm text-gray-700 dark:text-gray-300 italic">
              {citation.snippet}
            </blockquote>
          </div>
        </div>
      )}
    </>
  );
}
