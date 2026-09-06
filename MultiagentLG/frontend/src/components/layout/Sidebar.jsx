import React, { useEffect, useState, useRef, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { 
  Plus, 
  History, 
  Globe, 
  ChevronRight, 
  RotateCw, 
  X,
  LogOut,
  ChevronUp,
  Trash2,
  Loader2,
  CircleUser,
} from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { getResearchHistory, deleteResearch, clearAllResearch } from "../../services/api";

export const Sidebar = ({ isOpen, onClose, onNewResearch }) => {
  const { getIdToken, currentUser, logout } = useAuth();
  const { id: activeId } = useParams();
  const navigate = useNavigate();

  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef(null);

  // Close user popup on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

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
  const userInitials = displayName.charAt(0).toUpperCase() || "U";

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      const token = await getIdToken();
      if (!token) return;
      const list = await getResearchHistory(token);
      setHistory(list || []);
    } catch (err) {
      console.warn("Could not load research history:", err);
    } finally {
      setLoading(false);
    }
  }, [getIdToken]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const [deletingId, setDeletingId] = useState(null);

  const handleItemClick = (researchId) => {
    navigate(`/research/${researchId}`);
    if (window.innerWidth < 1024 && onClose) {
      onClose();
    }
  };

  const handleNew = () => {
    if (onNewResearch) onNewResearch();
    navigate("/");
    if (window.innerWidth < 1024 && onClose) {
      onClose();
    }
  };

  const handleDeleteResearch = async (e, researchId) => {
    e.stopPropagation();
    if (!window.confirm("Delete this research inquiry?")) return;

    try {
      setDeletingId(researchId);
      const token = await getIdToken();
      if (!token) return;

      await deleteResearch(researchId, token);
      setHistory((prev) => prev.filter((item) => item.research_id !== researchId));

      if (activeId === researchId) {
        if (onNewResearch) onNewResearch();
        navigate("/");
      }
    } catch (err) {
      console.error("Failed to delete research:", err);
      alert("Failed to delete research inquiry. Please try again.");
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAllHistory = async () => {
    if (history.length === 0) return;
    if (!window.confirm("Are you sure you want to delete ALL research inquiries? This cannot be undone.")) return;

    try {
      setLoading(true);
      const token = await getIdToken();
      if (!token) return;

      await clearAllResearch(token);
      setHistory([]);

      if (activeId) {
        if (onNewResearch) onNewResearch();
        navigate("/");
      }
    } catch (err) {
      console.error("Failed to clear research history:", err);
      alert("Failed to clear research history. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
        />
      )}

      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 z-45 w-72 glass-surface flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0 lg:w-0 lg:overflow-hidden lg:border-r-0"
        }`}
      >
        {/* Top Header — Clean, no logo */}
        <div className="p-3 pb-2.5 flex items-center justify-between border-b border-white/[0.06]">
          <span className="font-semibold text-sm text-white tracking-tight pl-1 select-none">
            Research Hub
          </span>

          <div className="flex items-center gap-0.5">
            {/* Reload button */}
            <button
              onClick={fetchHistory}
              disabled={loading}
              className="p-1.5 rounded-lg text-neutral-400 hover:text-white hover:bg-white/[0.06] transition-colors disabled:opacity-40"
              title="Refresh history"
            >
              <RotateCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            </button>

            {/* Close sidebar button */}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-neutral-400 hover:text-white hover:bg-white/[0.06] transition-colors"
              title="Close sidebar"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* New Research Button */}
        <div className="p-3 border-b border-white/[0.06]">
          <button
            onClick={handleNew}
            className="w-full flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-xl bg-white hover:bg-neutral-200 text-black font-semibold text-xs transition-all shadow-md shadow-white/10 active:scale-[0.98]"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>New Research</span>
          </button>
        </div>

        {/* History List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <div className="px-2 py-1.5 flex items-center justify-between text-[11px] font-mono uppercase tracking-wider text-neutral-500 font-semibold">
            <span className="flex items-center gap-1.5">
              <History className="w-3.5 h-3.5" />
              Past Inquiries
            </span>
            <span>{history.length}</span>
          </div>

          {loading && history.length === 0 ? (
            <div className="p-4 space-y-2.5">
              <div className="h-4 rounded w-4/5 shimmer" />
              <div className="h-4 rounded w-2/3 shimmer" />
              <div className="h-4 rounded w-3/4 shimmer" />
            </div>
          ) : history.length === 0 ? (
            <div className="py-10 px-3 text-center">
              <p className="text-xs text-neutral-500">No past research runs yet.</p>
              <p className="text-[11px] text-neutral-600 mt-1">Submit a question to get started.</p>
            </div>
          ) : (
            history.map((item) => {
              const isSelected = activeId === item.research_id;
              const isDeleting = deletingId === item.research_id;
              const dateStr = item.created_at
                ? new Date(item.created_at).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                  })
                : "";

              return (
                <div
                  key={item.research_id}
                  className="relative group/item"
                >
                  <button
                    onClick={() => handleItemClick(item.research_id)}
                    className={`w-full text-left p-2.5 pr-8 rounded-xl border transition-all duration-150 group flex flex-col gap-1 ${
                      isSelected
                        ? "glass-strong text-white shadow-sm ring-1 ring-white/10"
                        : "bg-transparent border-transparent hover:bg-white/[0.03] hover:border-white/[0.06] text-neutral-300"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-1.5 w-full">
                      <span className="text-xs font-medium line-clamp-2 leading-snug group-hover:text-white pr-2">
                        {item.question}
                      </span>
                      <ChevronRight className={`w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-neutral-600 transition-transform ${isSelected ? "text-white rotate-90" : "group-hover:translate-x-0.5"}`} />
                    </div>

                    <div className="flex items-center gap-2 text-[10px] text-neutral-500 font-mono mt-0.5">
                      {dateStr && <span>{dateStr}</span>}
                      {item.web_search_performed && (
                        <span className="inline-flex items-center gap-1 text-neutral-300">
                          <Globe className="w-2.5 h-2.5" />
                          Web
                        </span>
                      )}
                    </div>
                  </button>

                  {/* Delete Item Button */}
                  <button
                    onClick={(e) => handleDeleteResearch(e, item.research_id)}
                    disabled={isDeleting}
                    className="absolute right-2 top-2 p-1.5 rounded-lg text-neutral-500 hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover/item:opacity-100 transition-all active:scale-90"
                    title="Delete inquiry"
                  >
                    {isDeleting ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-red-400" />
                    ) : (
                      <Trash2 className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* User Profile — ChatGPT-style bottom */}
        <div className="relative border-t border-white/[0.06]" ref={userMenuRef}>
          {/* Popup menu */}
          {userMenuOpen && (
            <div className="absolute bottom-full left-2 right-2 mb-1 rounded-xl glass-strong shadow-2xl py-1.5 z-50 animate-in fade-in zoom-in-95">
              <div className="px-3.5 py-2.5 border-b border-white/[0.06]">
                <p className="text-xs font-medium text-white truncate">
                  {displayName}
                </p>
                <p className="text-[11px] text-neutral-500 font-mono truncate">
                  {currentUser?.email}
                </p>
              </div>

              <div className="px-1.5 py-1">
                <div className="px-2.5 py-1.5 flex items-center gap-2 text-[10px] text-neutral-500 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_6px_rgba(255,255,255,0.6)]" />
                  LangGraph + Gemini + Groq
                </div>
              </div>

              <div className="border-t border-white/[0.06] px-1.5 py-1 space-y-0.5">
                {history.length > 0 && (
                  <button
                    onClick={() => {
                      setUserMenuOpen(false);
                      handleClearAllHistory();
                    }}
                    disabled={loading}
                    className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium text-neutral-400 hover:text-red-400 hover:bg-red-500/10 transition-colors text-left"
                    title="Delete all research inquiries"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Clear all inquiries ({history.length})</span>
                  </button>
                )}

                <button
                  onClick={() => {
                    setUserMenuOpen(false);
                    logout();
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors text-left"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Sign out
                </button>
              </div>
            </div>
          )}

          {/* User profile button */}
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="w-full p-3 flex items-center gap-2.5 hover:bg-white/[0.04] transition-colors text-left"
          >
            {currentUser?.photoURL ? (
              <img
                src={currentUser.photoURL}
                alt={displayName}
                className="w-8 h-8 rounded-full object-cover border border-white/10 ring-1 ring-white/10 flex-shrink-0"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-white/[0.08] border border-white/10 text-white flex items-center justify-center flex-shrink-0">
                <CircleUser className="w-4 h-4 text-neutral-300" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-neutral-200 truncate">
                {displayName}
              </p>
              <p className="text-[10px] text-neutral-500 font-mono truncate">
                Free plan
              </p>
            </div>
            <ChevronUp className={`w-4 h-4 text-neutral-500 transition-transform ${userMenuOpen ? "" : "rotate-180"}`} />
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
