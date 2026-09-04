import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Clock, ExternalLink, Loader2, RefreshCcw } from 'lucide-react';
import { useResearchStream } from '../hooks/useResearchStream';
import { ResearchPipeline } from '../components/research/ResearchPipeline';
import { LiveActivityFeed } from '../components/activity/LiveActivityFeed';
import { ResearchReport } from '../components/report/ResearchReport';

export function ResearchPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { state, startResearch, clearResearch } = useResearchStream();
  const [elapsedTime, setElapsedTime] = useState(0);

  const initialQuestion = location.state?.question;

  useEffect(() => {
    if (!initialQuestion && state.status === 'idle') {
      navigate('/');
    } else if (initialQuestion && state.status === 'idle') {
      startResearch(initialQuestion);
    }
  }, [initialQuestion, state.status, navigate, startResearch]);

  // Timer logic
  useEffect(() => {
    let interval;
    if (state.status === 'researching') {
      interval = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [state.status]);

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleNewResearch = () => {
    clearResearch();
    navigate('/');
  };

  return (
    <div className="flex h-full w-full flex-col md:flex-row overflow-hidden">
      
      {/* Center Workspace */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-background">
        {/* Header */}
        <div className="p-6 border-b border-border bg-surface/30">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
            <div className="flex-1">
               <div className="flex items-center gap-2 mb-2">
                 <span className="text-xs font-semibold uppercase tracking-wider text-primary">Researching</span>
                 {state.status === 'researching' && <Loader2 className="w-3 h-3 text-primary animate-spin" />}
               </div>
               <h2 className="text-xl md:text-2xl font-bold text-text-main line-clamp-2">
                 "{state.question || initialQuestion}"
               </h2>
            </div>
            
            <div className="flex flex-row md:flex-col items-center md:items-end gap-4 md:gap-2 shrink-0">
               <div className="flex items-center gap-2 text-text-muted text-sm glass-card px-3 py-1.5 rounded-full">
                 <Clock className="w-4 h-4" />
                 <span className="font-mono">{formatTime(elapsedTime)} elapsed</span>
               </div>
               <div className="flex gap-4 text-xs text-text-muted">
                 <span>{state.tasks.length} tasks</span>
                 <span>•</span>
                 <span>{state.evidence.length} sources</span>
               </div>
            </div>
          </div>
        </div>

        {/* Pipeline & Main Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-8">
          
          {/* Pipeline */}
          <section>
            <h3 className="text-sm font-semibold text-text-muted mb-4 uppercase tracking-wider">Pipeline Status</h3>
            <div className="glass-panel p-2">
               <ResearchPipeline nodes={state.nodes} />
            </div>
          </section>

          {/* Error State */}
          {state.status === 'error' && (
            <div className="p-4 bg-status-error/10 border border-status-error/20 rounded-xl text-status-error flex items-center justify-between">
              <div>
                <h4 className="font-semibold mb-1">Research Failed</h4>
                <p className="text-sm opacity-90">{state.error}</p>
              </div>
              <button onClick={() => startResearch(state.question)} className="flex items-center gap-2 px-3 py-2 bg-status-error/20 rounded-lg hover:bg-status-error/30 transition-colors">
                <RefreshCcw className="w-4 h-4" />
                Retry
              </button>
            </div>
          )}

          {/* Research Results / Report View */}
          {state.final_report && (
             <section className="animate-in fade-in slide-in-from-bottom-4 duration-700">
               <div className="flex items-center justify-between mb-4">
                 <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider">Final Research Report</h3>
                 <button onClick={handleNewResearch} className="text-xs text-primary hover:underline">Start New Research</button>
               </div>
               <div className="glass-panel p-6 md:p-8 shadow-2xl">
                 <ResearchReport markdown={state.final_report} />
               </div>
             </section>
          )}

          {/* Tasks & Evidence Preview (shown while researching or if no report yet) */}
          {!state.final_report && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
               <section>
                 <h3 className="text-sm font-semibold text-text-muted mb-4 uppercase tracking-wider">Planned Tasks</h3>
                 <div className="space-y-3">
                   {state.tasks.length === 0 ? (
                     <div className="text-sm text-text-muted italic p-4 glass-card text-center">Waiting for planner...</div>
                   ) : (
                     state.tasks.map((task, i) => (
                       <div key={i} className="glass-card p-4">
                         <div className="text-xs text-primary font-medium mb-1">Task {String(i+1).padStart(2, '0')}</div>
                         <div className="text-sm text-text-main">{task}</div>
                       </div>
                     ))
                   )}
                 </div>
               </section>

               <section>
                 <h3 className="text-sm font-semibold text-text-muted mb-4 uppercase tracking-wider">Evidence Gathered</h3>
                 <div className="space-y-3">
                   {state.evidence.length === 0 ? (
                     <div className="text-sm text-text-muted italic p-4 glass-card text-center">Waiting for researchers...</div>
                   ) : (
                     state.evidence.slice(0, 5).map((ev, i) => (
                       <div key={i} className="glass-card p-4">
                         <div className="text-sm text-text-main line-clamp-3 mb-2">{ev.finding || (typeof ev === 'string' ? ev : JSON.stringify(ev))}</div>
                         {ev.source && (
                           <a href={ev.source} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[11px] text-text-muted hover:text-primary transition-colors">
                             <ExternalLink className="w-3 h-3" />
                             {ev.source}
                           </a>
                         )}
                       </div>
                     ))
                   )}
                   {state.evidence.length > 5 && (
                     <div className="text-center text-xs text-text-muted pt-2">+ {state.evidence.length - 5} more sources collected</div>
                   )}
                 </div>
               </section>
            </div>
          )}
        </div>
      </div>

      {/* Right Sidebar - Live Activity */}
      <LiveActivityFeed events={state.events} />
      
    </div>
  );
}
