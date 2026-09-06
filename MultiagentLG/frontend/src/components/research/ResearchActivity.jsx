import React from "react";
import { 
  CheckCircle2, 
  Circle, 
  Loader2, 
  Globe, 
  Compass, 
  Search, 
  Layers, 
  ShieldCheck, 
  PenTool, 
  Image as ImageIcon,
  Save
} from "lucide-react";

const STAGE_CONFIG = [
  { id: "planning", name: "Strategic Planning", icon: Compass },
  { id: "researching", name: "Parallel Deep Investigation", icon: Search },
  { id: "web_search", name: "Live Web Intel", icon: Globe },
  { id: "collecting", name: "Evidence Synthesis", icon: Layers },
  { id: "critique", name: "Quality & Rigor Check", icon: ShieldCheck },
  { id: "writing", name: "Comprehensive Reporting", icon: PenTool },
  { id: "finalizing", name: "Illustrations & Visuals", icon: ImageIcon },
  { id: "saving", name: "Persistent Archiving", icon: Save },
];

export const ResearchActivity = ({ stages, currentStage, isStreaming, question }) => {
  // Calculate completed count
  const completedCount = Object.values(stages).filter((s) => s.status === "completed").length;
  const totalStages = STAGE_CONFIG.length;
  const progressPercent = Math.min(100, Math.round((completedCount / totalStages) * 100));

  return (
    <div className="w-full max-w-3xl mx-auto rounded-2xl glass-surface p-5 shadow-2xl">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/5">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium bg-white/10 text-white border border-white/20">
              {isStreaming ? (
                <>
                  <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
                  Investigation in Progress
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-3 h-3 text-white" />
                  Synthesis Concluded
                </>
              )}
            </span>
            <span className="text-xs text-neutral-400 font-mono">
              {completedCount} of {totalStages} milestones
            </span>
          </div>
          {question && (
            <h3 className="text-sm font-medium text-neutral-100 mt-1.5 line-clamp-1">
              "{question}"
            </h3>
          )}
        </div>

        {/* Progress percent badge */}
        <div className="flex items-center gap-3">
          <div className="w-28 sm:w-36 h-2 bg-neutral-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-white via-neutral-200 to-neutral-400 transition-all duration-500 ease-out shadow-[0_0_8px_rgba(255,255,255,0.4)]"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <span className="text-xs font-mono font-semibold text-white">
            {progressPercent}%
          </span>
        </div>
      </div>

      {/* Stage Flow List */}
      <div className="pt-4 grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {STAGE_CONFIG.map((config) => {
          const stageState = stages[config.id] || { status: "idle", message: "" };
          const Icon = config.icon;
          const isCurrent = currentStage === config.id;
          const isCompleted = stageState.status === "completed";
          const isRunning = stageState.status === "running" || isCurrent;

          return (
            <div
              key={config.id}
              className={`p-3 rounded-xl border transition-all duration-200 flex items-start gap-3 ${
                isRunning && !isCompleted
                  ? "bg-neutral-800/80 border-white/30 shadow-sm shadow-white/5 ring-1 ring-white/10"
                  : isCompleted
                  ? "bg-neutral-900/40 border-white/5 opacity-90"
                  : "bg-neutral-900/20 border-white/5 opacity-40"
              }`}
            >
              <div className="mt-0.5 flex-shrink-0">
                {isCompleted ? (
                  <div className="w-5 h-5 rounded-full bg-white/20 text-white flex items-center justify-center">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  </div>
                ) : isRunning ? (
                  <div className="w-5 h-5 rounded-full bg-white/20 text-white flex items-center justify-center animate-spin">
                    <Loader2 className="w-3.5 h-3.5" />
                  </div>
                ) : (
                  <div className="w-5 h-5 rounded-full bg-neutral-800 text-neutral-600 flex items-center justify-center">
                    <Circle className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-1">
                  <div className="flex items-center gap-1.5">
                    <Icon className={`w-3.5 h-3.5 ${isRunning ? "text-white" : isCompleted ? "text-neutral-400" : "text-neutral-600"}`} />
                    <span className={`text-xs font-medium truncate ${isRunning ? "text-white" : isCompleted ? "text-neutral-300" : "text-neutral-500"}`}>
                      {config.name}
                    </span>
                  </div>

                  {stageState.score && (
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/15 text-white border border-white/20 font-semibold">
                      Score: {stageState.score}
                    </span>
                  )}
                </div>

                <p className="text-[11px] text-neutral-400 line-clamp-1 mt-0.5 leading-snug">
                  {stageState.message || "Awaiting pipeline trigger"}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ResearchActivity;
