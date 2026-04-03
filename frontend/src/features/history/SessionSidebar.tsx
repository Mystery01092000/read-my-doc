import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { chatApi } from "@/api/chat";
import { documentsApi } from "@/api/documents";
import { useAuth } from "@/hooks/useAuth";
import type { ChatSession, Document } from "@/types";

export function SessionSidebar() {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [showNewModal, setShowNewModal] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<Set<string>>(new Set());
  const [isCreating, setIsCreating] = useState(false);

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
  }, [sessionId]); // reload when active session changes

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

  return (
    <>
      <aside className="flex flex-col w-64 shrink-0 h-full border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200 dark:border-gray-800">
          <Link to="/documents" className="text-sm font-bold text-gray-900 dark:text-gray-50 hover:text-brand-600">
            Ask My Docs
          </Link>
          <button
            onClick={openNewModal}
            className="text-xs px-2 py-1 rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors"
          >
            + New Chat
          </button>
        </div>

        {/* Session list */}
        <nav className="flex-1 overflow-y-auto py-2">
          {sessions.length === 0 ? (
            <p className="text-xs text-gray-400 text-center mt-8 px-4">
              No chats yet. Start a new one.
            </p>
          ) : (
            sessions.map((s) => (
              <Link
                key={s.id}
                to={`/chat/${s.id}`}
                className={`block px-4 py-2.5 text-sm truncate transition-colors ${
                  s.id === sessionId
                    ? "bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300 font-medium"
                    : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                }`}
              >
                {s.title}
              </Link>
            ))
          )}
        </nav>

        {/* Bottom actions */}
        <div className="border-t border-gray-200 dark:border-gray-800 px-4 py-3 space-y-1">
          <Link
            to="/documents"
            className="block text-xs text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 py-1"
          >
            Documents
          </Link>
          <button
            onClick={logout}
            className="block text-xs text-gray-500 hover:text-red-600 py-1"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* New chat modal */}
      {showNewModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40"
          onClick={() => setShowNewModal(false)}
        >
          <div
            className="w-full max-w-md rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-xl p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-base font-semibold text-gray-900 dark:text-gray-50 mb-4">
              Select documents to chat with
            </h2>

            {documents.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-6">
                No ready documents. Upload and process some first.
              </p>
            ) : (
              <ul className="space-y-2 max-h-64 overflow-y-auto mb-4">
                {documents.map((doc) => (
                  <li key={doc.id}>
                    <label className="flex items-center gap-3 cursor-pointer rounded-lg px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800">
                      <input
                        type="checkbox"
                        checked={selectedDocIds.has(doc.id)}
                        onChange={() => toggleDoc(doc.id)}
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm text-gray-800 dark:text-gray-200 truncate">
                        {doc.filename}
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            )}

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowNewModal(false)}
                className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 dark:hover:text-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={createSession}
                disabled={selectedDocIds.size === 0 || isCreating}
                className="px-4 py-1.5 text-sm rounded-lg bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isCreating ? "Creating…" : "Start Chat"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
