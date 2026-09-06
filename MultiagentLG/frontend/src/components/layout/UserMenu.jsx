import React, { useState, useRef, useEffect } from "react";
import { LogOut, CircleUser } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";

export const UserMenu = () => {
  const { currentUser, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!currentUser) return null;

  const getUserFirstName = () => {
    if (!currentUser) return "User";
    if (currentUser.displayName && currentUser.displayName.trim()) {
      const first = currentUser.displayName.trim().split(/[\s._-]+/)[0];
      if (first) return first.charAt(0).toUpperCase() + first.slice(1).toLowerCase();
    }
    if (currentUser.email && currentUser.email.trim()) {
      const prefix = currentUser.email.split("@")[0].trim();
      const firstPart = prefix.split(/[._\d-]+/)[0] || prefix;
      if (firstPart) return firstPart.charAt(0).toUpperCase() + firstPart.slice(1).toLowerCase();
    }
    return "User";
  };
  const displayName = getUserFirstName();
  const userInitial = displayName.charAt(0).toUpperCase() || "U";

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2.5 p-1.5 rounded-full hover:bg-neutral-800/80 transition-colors focus:outline-none focus:ring-2 focus:ring-white/30"
      >
        {currentUser.photoURL ? (
          <img
            src={currentUser.photoURL}
            alt={displayName}
            className="w-8 h-8 rounded-full object-cover border border-white/10 ring-1 ring-white/20"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-neutral-800 border border-white/20 text-white flex items-center justify-center">
            <CircleUser className="w-4 h-4 text-neutral-300" />
          </div>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-64 rounded-xl bg-neutral-900 border border-neutral-800 shadow-2xl py-2 z-50 animate-in fade-in zoom-in-95">
          <div className="px-4 py-2.5 border-b border-neutral-800">
            <p className="text-xs font-medium text-white truncate">
              {displayName}
            </p>
            <p className="text-[11px] text-neutral-400 font-mono truncate">
              {currentUser.email}
            </p>
          </div>

          <div className="px-2 py-1.5">
            <div className="px-2.5 py-1.5 flex items-center gap-2 text-xs text-neutral-400 font-mono">
              <span className="w-2 h-2 rounded-full bg-white shadow-[0_0_6px_rgba(255,255,255,0.7)] animate-pulse" />
              <span>Multi-Agent Engine v1.0</span>
            </div>
          </div>

          <div className="border-t border-neutral-800 pt-1 px-1">
            <button
              onClick={() => {
                setOpen(false);
                logout();
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors text-left"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserMenu;
