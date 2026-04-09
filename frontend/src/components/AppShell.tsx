import { Outlet } from "react-router-dom";
import { SessionSidebar } from "@/features/history/SessionSidebar";

export function AppShell() {
  return (
    <div className="flex h-screen bg-black text-on-surface font-body overflow-hidden relative">
      
      {/* 1. Global Navigation HUD */}
      <SessionSidebar />

      {/* 2. Main content area */}
      <main className="flex-1 overflow-y-auto relative z-10 flex flex-col">
        {/* Atmosphere Decor */}
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-primary/5 blur-[140px] rounded-full pointer-events-none -z-10" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-secondary/5 blur-[120px] rounded-full pointer-events-none -z-10" />
        
        <Outlet />
      </main>
      
    </div>
  );
}
