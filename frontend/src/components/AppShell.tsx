import { Outlet } from "react-router-dom";
import { SessionSidebar } from "@/features/history/SessionSidebar";

export function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950">
      <SessionSidebar />
      <main className="flex-1 overflow-hidden flex flex-col">
        <Outlet />
      </main>
    </div>
  );
}
