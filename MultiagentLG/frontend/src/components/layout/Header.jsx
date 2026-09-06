import React, { useEffect, useState } from "react";
import { Menu } from "lucide-react";
import { checkHealth } from "../../services/api";

export const Header = ({ onToggleSidebar, sidebarOpen = false }) => {
  const [backendOnline, setBackendOnline] = useState(true);

  useEffect(() => {
    checkHealth()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));

    const interval = setInterval(() => {
      checkHealth()
        .then(() => setBackendOnline(true))
        .catch(() => setBackendOnline(false));
    }, 45000);

    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-14 border-b border-white/[0.06] glass-surface px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-2">
        {/* Sidebar toggle — only visible when sidebar is closed */}
        {!sidebarOpen && (
          <button
            onClick={onToggleSidebar}
            className="p-1.5 rounded-lg text-neutral-400 hover:text-white hover:bg-white/[0.06] transition-colors"
            title="Open Sidebar"
            aria-label="Open Sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        {/* App name — only visible when sidebar is closed */}
        {!sidebarOpen && (
          <span className="font-semibold text-sm tracking-tight text-white hidden sm:inline select-none">
            Deep Researcher
          </span>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Backend health status badge */}
        <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-full glass text-[11px] font-mono">
          <span
            className={`w-2 h-2 rounded-full ${
              backendOnline
                ? "bg-white shadow-[0_0_8px_rgba(255,255,255,0.7)]"
                : "bg-neutral-500"
            }`}
          />
          <span className="text-neutral-300">
            {backendOnline ? "LangGraph Active" : "Connecting..."}
          </span>
        </div>
      </div>
    </header>
  );
};

export default Header;
