import React, { useState } from "react";
import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";
import { ResearchInput } from "../components/research/ResearchInput";
import { ResearchActivity } from "../components/research/ResearchActivity";
import { ResearchReport } from "../components/research/ResearchReport";
import { EmptyState } from "../components/common/EmptyState";
import { useResearch } from "../hooks/useResearch";
import { AlertCircle, RotateCcw, Home as HomeIcon, LayoutGrid, X } from "lucide-react";

export const Home = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showTopics, setShowTopics] = useState(false);
  const {
    isStreaming,
    stages,
    currentStage,
    activeQuestion,
    finalReport,
    reportData,
    error,
    startResearch,
    stopResearch,
    resetResearch,
  } = useResearch();

  const handlePromptSelect = (prompt) => {
    startResearch(prompt);
  };

  const handleNewResearch = () => {
    resetResearch();
  };

  const hasActiveContent = isStreaming || Boolean(finalReport) || currentStage !== null;

  // Detect cancelled state: not streaming, no final report, but has a stage active
  const isCancelled = !isStreaming && !finalReport && currentStage !== null && currentStage !== "complete";

  return (
    <div className="flex h-screen bg-[#0a0a0a] text-[#f5f5f5] overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewResearch={handleNewResearch}
      />

      {/* Main Workspace Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        <Header 
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} 
          sidebarOpen={sidebarOpen} 
        />

        <main className="flex-1 overflow-y-auto px-4 sm:px-8 py-6 flex flex-col justify-between">
          <div className={`max-w-4xl w-full mx-auto ${!hasActiveContent && !error && !showTopics ? "flex-1 flex flex-col justify-center my-auto" : "space-y-6"}`}>
            {/* Error Message if any */}
            {error && (
              <div className="p-4 rounded-xl glass border-red-500/20 text-red-300 text-sm flex items-start justify-between gap-3 animate-in fade-in">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-400" />
                  <span>{error}</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleNewResearch}
                    className="px-2.5 py-1 rounded-md bg-white/[0.06] hover:bg-white/[0.1] text-neutral-200 text-xs font-medium transition-colors flex items-center gap-1"
                  >
                    <HomeIcon className="w-3 h-3" />
                    Home
                  </button>
                  <button
                    onClick={() => startResearch(activeQuestion)}
                    className="px-2.5 py-1 rounded-md bg-red-500/20 hover:bg-red-500/30 text-red-200 text-xs font-medium transition-colors flex items-center gap-1"
                  >
                    <RotateCcw className="w-3 h-3" />
                    Retry
                  </button>
                </div>
              </div>
            )}

            {/* If no query has been run yet */}
            {!hasActiveContent && !error && (
              <EmptyState 
                onSelectPrompt={handlePromptSelect} 
                showTopics={showTopics}
                onCloseTopics={() => setShowTopics(false)}
              />
            )}

            {/* Cancelled state — show "Start Over" banner */}
            {isCancelled && (
              <div className="p-4 rounded-xl glass text-sm flex items-center justify-between gap-3 animate-in fade-in">
                <div className="flex items-center gap-2 text-neutral-300">
                  <AlertCircle className="w-4 h-4 text-neutral-400" />
                  <span>Research was stopped. You can start a new one or retry.</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleNewResearch}
                    className="px-3 py-1.5 rounded-lg bg-white hover:bg-neutral-200 text-black text-xs font-semibold transition-colors flex items-center gap-1.5 active:scale-95"
                  >
                    <HomeIcon className="w-3.5 h-3.5" />
                    Start Over
                  </button>
                  <button
                    onClick={() => startResearch(activeQuestion)}
                    className="px-3 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] border border-white/[0.08] text-neutral-200 text-xs font-medium transition-colors flex items-center gap-1.5"
                  >
                    <RotateCcw className="w-3 h-3" />
                    Retry
                  </button>
                </div>
              </div>
            )}

            {/* Active Research Progress */}
            {hasActiveContent && (
              <ResearchActivity
                stages={stages}
                currentStage={currentStage}
                isStreaming={isStreaming}
                question={activeQuestion}
              />
            )}

            {/* Generated Report */}
            {finalReport && (
              <ResearchReport
                report={finalReport}
                question={activeQuestion}
                webSearchPerformed={reportData?.web_search_performed}
                critique={reportData?.critique}
                createdAt={new Date().toISOString()}
              />
            )}
          </div>

          {/* Sticky Research Input Bar */}
          <div className="pt-4 pb-2 sticky bottom-0 bg-gradient-to-t from-[#0a0a0a] via-[#0a0a0a]/90 to-transparent">
            {/* Ultra-compact Topics toggle pill right above input */}
            {!hasActiveContent && !error && (
              <div className="flex justify-center mb-1.5 animate-in fade-in duration-200">
                <button
                  onClick={() => setShowTopics(!showTopics)}
                  className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full border transition-all active:scale-95 group text-[10px] font-mono ${
                    showTopics
                      ? "bg-white/[0.06] hover:bg-red-500/10 border-white/[0.12] hover:border-red-500/30 text-neutral-300 hover:text-red-300"
                      : "bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.06] hover:border-white/[0.12] text-neutral-400 hover:text-neutral-200"
                  }`}
                  title={showTopics ? "Hide topic cards" : "Browse topic cards and prompts"}
                >
                  {showTopics ? (
                    <>
                      <X className="w-2.5 h-2.5 text-neutral-400 group-hover:text-red-400 transition-colors" />
                      <span>Hide Topics</span>
                    </>
                  ) : (
                    <>
                      <LayoutGrid className="w-2.5 h-2.5 text-neutral-500 group-hover:text-neutral-300 transition-colors" />
                      <span>Topics (24)</span>
                    </>
                  )}
                </button>
              </div>
            )}

            <ResearchInput
              onSubmit={startResearch}
              onStop={stopResearch}
              isStreaming={isStreaming}
              initialValue=""
              showGlow={!hasActiveContent && !error}
            />
          </div>
        </main>
      </div>
    </div>
  );
};

export default Home;
