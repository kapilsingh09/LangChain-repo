import { Brain, FileSearch, Search, ShieldCheck, FileText, Download, Check, RefreshCw } from 'lucide-react';
import { cn } from '../layout/Sidebar';

const PIPELINE_STAGES = [
  { id: 'planner', label: 'Planner', icon: Brain },
  { id: 'researcher', label: 'Researchers', icon: Search },
  { id: 'collector', label: 'Collector', icon: FileSearch },
  { id: 'critic', label: 'Critic', icon: ShieldCheck },
  { id: 'report_writer', label: 'Writer', icon: FileText },
  { id: 'image_subgraph', label: 'Diagrams', icon: RefreshCw },
  { id: 'file_saver', label: 'Complete', icon: Download },
];

export function ResearchPipeline({ nodes }) {
  
  const getStageStatus = (stageId) => {
    // nodes contains { planner: { status: 'pending|active|completed' }, ... }
    return nodes[stageId]?.status || 'pending';
  };

  return (
    <div className="w-full overflow-x-auto py-6 hide-scrollbar">
      <div className="flex items-center min-w-max px-4">
        {PIPELINE_STAGES.map((stage, index) => {
          const status = getStageStatus(stage.id);
          const isLast = index === PIPELINE_STAGES.length - 1;
          const isCompleted = status === 'completed';
          const isActive = status === 'active';
          
          return (
            <div key={stage.id} className="flex items-center">
              {/* Node */}
              <div className="flex flex-col items-center gap-3 relative">
                <div 
                  className={cn(
                    "w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-500 relative z-10",
                    isCompleted ? "bg-primary/20 text-primary border border-primary/50 shadow-[0_0_15px_rgba(79,70,229,0.2)]" :
                    isActive ? "bg-primary text-white shadow-[0_0_20px_rgba(79,70,229,0.5)] scale-110 border border-primary-light" :
                    "bg-surface border border-border text-text-muted"
                  )}
                >
                  {isActive && (
                    <div className="absolute inset-0 rounded-2xl border border-primary animate-ping opacity-75"></div>
                  )}
                  {isCompleted && stage.id !== 'file_saver' ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <stage.icon className={cn("w-5 h-5", isActive && "animate-pulse")} />
                  )}
                </div>
                <span className={cn(
                  "text-xs font-medium transition-colors duration-300 absolute -bottom-6 whitespace-nowrap",
                  isActive ? "text-text-main" : "text-text-muted"
                )}>
                  {stage.label}
                </span>
              </div>

              {/* Edge/Line */}
              {!isLast && (
                <div className="w-12 md:w-20 h-[2px] mx-2 relative">
                  <div className="absolute inset-0 bg-border"></div>
                  <div 
                    className="absolute inset-0 bg-primary transition-all duration-700 ease-in-out origin-left"
                    style={{ transform: `scaleX(${isCompleted ? 1 : 0})` }}
                  ></div>
                  {isActive && (
                    <div className="absolute inset-0 bg-primary/50 animate-pulse"></div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
