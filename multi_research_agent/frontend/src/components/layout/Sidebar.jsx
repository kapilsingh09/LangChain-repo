import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Brain, FileSearch, History, Bookmark, Library, Settings, Plus, Menu, X, CheckCircle, Loader, XCircle } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Helper for tailwind class merging
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const NAV_ITEMS = [
  { label: 'New Research', icon: Plus, path: '/', primary: true },
  { label: 'Research History', icon: History, path: '/history' },
  { label: 'Saved Reports', icon: Bookmark, path: '/saved' },
  { label: 'Sources', icon: Library, path: '/sources' },
  { label: 'Settings', icon: Settings, path: '/settings' },
];

const RECENT_SESSIONS = [
  { id: '1', title: 'Current state of Generative AI', date: '2 hours ago', status: 'completed' },
  { id: '2', title: 'RAG vs Fine-tuning', date: 'Yesterday', status: 'completed' },
  { id: '3', title: 'Future of AI Agents', date: '3 days ago', status: 'failed' },
];

export function Sidebar({ mobileOpen, setMobileOpen }) {
  
  const getStatusIcon = (status) => {
    switch(status) {
      case 'completed': return <CheckCircle className="w-3 h-3 text-status-success" />;
      case 'researching': return <Loader className="w-3 h-3 text-status-pending animate-spin" />;
      case 'failed': return <XCircle className="w-3 h-3 text-status-error" />;
      default: return null;
    }
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div 
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 md:hidden" 
          onClick={() => setMobileOpen(false)} 
        />
      )}
      
      <aside className={cn(
        "fixed md:sticky top-0 left-0 h-screen w-64 bg-surface border-r border-border flex flex-col transition-transform duration-300 ease-in-out z-50",
        mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      )}>
        {/* Header */}
        <div className="p-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center border border-primary/50 text-primary">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-semibold text-text-main text-sm">Deep Research</h1>
              <p className="text-[10px] text-text-muted uppercase tracking-wider">Intelligence Engine</p>
            </div>
          </div>
          <button className="md:hidden text-text-muted hover:text-text-main" onClick={() => setMobileOpen(false)}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 flex flex-col gap-1 flex-1 overflow-y-auto">
          <div className="mb-6 space-y-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                  isActive 
                    ? "bg-primary/10 text-primary font-medium" 
                    : item.primary 
                      ? "text-text-main hover:bg-surface-hover" 
                      : "text-text-muted hover:text-text-main hover:bg-surface-hover"
                )}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </NavLink>
            ))}
          </div>

          <div>
            <h3 className="px-3 text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">Recent Research</h3>
            <div className="space-y-1">
              {RECENT_SESSIONS.map((session) => (
                <div key={session.id} className="group flex flex-col px-3 py-2 rounded-lg hover:bg-surface-hover cursor-pointer transition-colors">
                  <div className="text-sm text-text-main truncate group-hover:text-primary transition-colors">
                    {session.title}
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-[11px] text-text-muted">{session.date}</span>
                    <div className="flex items-center gap-1">
                       {getStatusIcon(session.status)}
                       <span className="text-[10px] text-text-muted capitalize">{session.status}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-hover cursor-pointer transition-colors">
            <div className="w-8 h-8 rounded-full bg-border flex items-center justify-center text-xs font-medium">
              U
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-medium text-text-main">User</span>
              <span className="text-xs text-text-muted">Pro Plan</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
