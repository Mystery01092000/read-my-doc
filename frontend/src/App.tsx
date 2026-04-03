import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { RequireAuth } from "@/features/auth/RequireAuth";
import { AppShell } from "@/components/AppShell";
import { DocumentsPage } from "@/features/documents/DocumentsPage";
import { ChatPage } from "@/features/chat/ChatPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected — inside AppShell with sidebar */}
        <Route element={<RequireAuth />}>
          <Route element={<AppShell />}>
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/chat/:sessionId" element={<ChatPage />} />
          </Route>
        </Route>

        <Route path="/" element={<Navigate to="/documents" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
