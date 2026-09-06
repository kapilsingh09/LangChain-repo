import React, { useState, useRef, useEffect } from "react";
import { ArrowUp, Square } from "lucide-react";

const PLACEHOLDER_HINTS = [
  "What are the latest breakthroughs in quantum computing?",
  "Compare the economics of solar vs nuclear energy...",
  "How is CRISPR being used in cancer treatment?",
  "Analyze the impact of AI agents on software engineering...",
  "What's the current state of solid-state batteries?",
  "Explain the latest developments in nuclear fusion...",
  "How are LLMs changing scientific research?",
  "What are the biggest cybersecurity threats in 2025?",
];

export const ResearchInput = ({ onSubmit, onStop, isStreaming, initialValue = "", showGlow = false }) => {
  const [question, setQuestion] = useState(initialValue);
  const [placeholderIdx, setPlaceholderIdx] = useState(0);
  const [placeholderVisible, setPlaceholderVisible] = useState(true);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (initialValue) {
      setQuestion(initialValue);
    }
  }, [initialValue]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [question]);

  // Rotate placeholder text
  useEffect(() => {
    if (question.length > 0 || isStreaming) return;

    const interval = setInterval(() => {
      setPlaceholderVisible(false);
      setTimeout(() => {
        setPlaceholderIdx((prev) => (prev + 1) % PLACEHOLDER_HINTS.length);
        setPlaceholderVisible(true);
      }, 300);
    }, 4000);

    return () => clearInterval(interval);
  }, [question, isStreaming]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!question.trim() || isStreaming) return;
    onSubmit(question.trim());
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form
        onSubmit={handleSubmit}
        className={`relative rounded-2xl glass-surface hover:border-white/[0.12] focus-within:border-white/30 focus-within:ring-1 focus-within:ring-white/10 shadow-2xl shadow-black/50 transition-all p-3 ${
          showGlow && !question.trim() ? "input-glow" : ""
        }`}
      >
        <textarea
          ref={textareaRef}
          rows={1}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={PLACEHOLDER_HINTS[placeholderIdx]}
          disabled={isStreaming}
          className={`w-full bg-transparent text-sm text-neutral-100 placeholder-neutral-500 resize-none outline-none max-h-44 pr-12 pl-2 py-1 leading-relaxed font-sans disabled:opacity-50 transition-opacity duration-300 ${
            placeholderVisible ? "placeholder:opacity-100" : "placeholder:opacity-0"
          }`}
        />

        <div className="flex items-center justify-between pt-2 px-1 border-t border-white/[0.05] mt-1">
          <div className="flex items-center gap-2 text-[11px] text-neutral-500 font-mono">
            <span><b className="text-neutral-400">Deep Researcher</b> can make mistakes. Check important info.</span>
          </div>

          <div className="flex items-center gap-2">
            {isStreaming ? (
              <button
                type="button"
                onClick={onStop}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 text-xs font-mono font-medium transition-colors"
              >
                <Square className="w-3 h-3 fill-red-400" />
                <span>Stop</span>
              </button>
            ) : (
              <button
                type="submit"
                disabled={!question.trim()}
                className="w-8 h-8 rounded-lg bg-white hover:bg-neutral-200 disabled:bg-neutral-800 text-black disabled:text-neutral-600 flex items-center justify-center transition-all shadow-md shadow-white/10 disabled:shadow-none active:scale-95"
                title="Run Research"
              >
                <ArrowUp className="w-4 h-4 stroke-[2.5]" />
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
};

export default ResearchInput;
