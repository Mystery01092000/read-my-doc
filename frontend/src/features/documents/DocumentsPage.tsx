import { useCallback, useEffect, useRef, useState } from "react";
import { useDropzone } from "react-dropzone";
import { documentsApi } from "@/api/documents";
import type { Document } from "@/types";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  processing: "bg-blue-100 text-blue-800",
  ready: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
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
      setError("Failed to load documents");
    }
  }, []);

  useEffect(() => {
    loadDocuments();
    // Poll every 5s to update processing statuses
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
        setError("Upload failed. Please check the file type and size.");
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
      setError("Failed to delete document");
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleDrop,
    accept: ACCEPTED_EXTENSIONS,
    multiple: true,
  });

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="max-w-4xl mx-auto p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-50 mb-6">My Documents</h1>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 dark:bg-red-950 px-4 py-3 text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Upload zone */}
        <div
          {...getRootProps()}
          className={`mb-6 rounded-xl border-2 border-dashed p-10 text-center cursor-pointer transition-colors
            ${isDragActive ? "border-brand-500 bg-brand-50 dark:bg-brand-950" : "border-gray-300 dark:border-gray-700 hover:border-brand-400"}`}
        >
          <input {...getInputProps()} />
          {isUploading ? (
            <p className="text-sm text-gray-500">Uploading…</p>
          ) : isDragActive ? (
            <p className="text-sm text-brand-600">Drop files here</p>
          ) : (
            <>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Drag & drop files here, or click to browse
              </p>
              <p className="mt-1 text-xs text-gray-400">
                PDF, TXT, MD, CSV, XLSX, PPTX — up to 50 MB each
              </p>
            </>
          )}
        </div>

        {/* Document list */}
        {documents.length === 0 ? (
          <p className="text-center text-sm text-gray-400 py-12">
            No documents yet. Upload one above.
          </p>
        ) : (
          <ul className="space-y-3">
            {documents.map((doc) => (
              <li
                key={doc.id}
                className="flex items-center justify-between rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 px-5 py-4"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="text-xs font-mono uppercase text-gray-400 w-8">{doc.fileType}</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {doc.filename}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[doc.status] ?? ""}`}
                  >
                    {doc.status}
                  </span>
                </div>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="ml-4 text-xs text-red-500 hover:text-red-700 shrink-0"
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
