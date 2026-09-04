import { useEffect, useRef, useState } from 'react';
import { Activity, ArrowDown } from 'lucide-react';
import { cn } from '../layout/Sidebar';

export function LiveActivityFeed({ events }) {
  const scrollRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Handle scroll events to detect if user scrolled up
  const handleScroll = () => {
    if (!scrollRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    
    setAutoScroll(isAtBottom);
  };

  // Auto-scroll to bottom when new events arrive, if autoScroll is true
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events, autoScroll]);

  return (
    <div className="flex flex-col h-full bg-surface border-l border-border md:w-80 lg:w-96">
      <div className="p-4 border-b border-border flex items-center justify-between bg-surface/95 backdrop-blur-sm z-10 sticky top-0">
        <div className="flex items-center gap-2 text-text-main font-medium text-sm">
          <Activity className="w-4 h-4 text-primary animate-pulse" />
          Live Research Activity
        </div>
      </div>
      
      <div 
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 space-y-4 hide-scrollbar relative"
      >
        {events.length === 0 ? (
          <div className="text-center text-text-muted text-sm mt-10">
            Waiting for research to begin...
          </div>
        ) : (
          events.map((event, i) => (
            <ActivityEvent key={event.id || i} event={event} isLatest={i === events.length - 1} />
          ))
        )}
      </div>

      {!autoScroll && events.length > 0 && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20">
          <button 
            onClick={() => setAutoScroll(true)}
            className="flex items-center gap-1 bg-primary text-white text-xs px-3 py-1.5 rounded-full shadow-lg hover:bg-primary/90 transition-colors"
          >
            <ArrowDown className="w-3 h-3" />
            New activity
          </button>
        </div>
      )}
    </div>
  );
}

function ActivityEvent({ event, isLatest }) {
  const time = new Date(event.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' });
  
  let content = "Processing...";
  if (event.event === 'started') content = "Research session started";
  else if (event.event === 'node_update') {
    content = `${event.node} stage active`;
  } else if (event.event === 'completed') {
    content = "Research completed successfully";
  } else if (event.event === 'error') {
    content = `Error: ${event.error}`;
  }

  return (
    <div className={cn(
      "flex gap-3 text-sm animate-in fade-in slide-in-from-bottom-2 duration-300",
      isLatest ? "opacity-100" : "opacity-60 hover:opacity-100 transition-opacity"
    )}>
      <div className="text-[10px] text-text-muted font-mono mt-1 w-14 shrink-0">{time}</div>
      <div className="flex-1">
        <div className={cn(
          "px-3 py-2 rounded-lg border",
          event.event === 'error' ? "bg-status-error/10 border-status-error/20 text-status-error" :
          isLatest ? "bg-primary/10 border-primary/20 text-text-main shadow-[0_0_10px_rgba(79,70,229,0.1)]" : "bg-surface-hover border-border text-text-main/80"
        )}>
          {content}
          
          {/* Detailed payload preview for debug/interest */}
          {event.event === 'node_update' && event.data && (
            <div className="mt-2 text-[10px] text-text-muted font-mono overflow-hidden text-ellipsis whitespace-nowrap max-w-[200px]">
               {Object.keys(event.data).join(', ')} updated
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
