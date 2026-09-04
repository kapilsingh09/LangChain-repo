import { Menu } from 'lucide-react';

export function TopNavigation({ setMobileOpen }) {
  return (
    <div className="md:hidden sticky top-0 z-30 bg-surface/80 backdrop-blur-md border-b border-border p-4 flex items-center gap-3">
      <button onClick={() => setMobileOpen(true)} className="text-text-muted hover:text-text-main">
        <Menu className="w-6 h-6" />
      </button>
      <div className="font-semibold text-text-main text-sm">Deep Research</div>
    </div>
  );
}
