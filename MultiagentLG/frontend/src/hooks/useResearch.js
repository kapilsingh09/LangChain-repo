import { useState, useRef, useCallback } from "react";
import { streamResearch } from "../services/api";
import { useAuth } from "./useAuth";

const INITIAL_STAGES = {
  planning: { id: "planning", label: "Research Planning", status: "idle", message: "Deconstructing problem & creating subtasks" },
  researching: { id: "researching", label: "Parallel Investigators", status: "idle", message: "Multi-agent deep domain exploration", count: 0 },
  web_search: { id: "web_search", label: "Live Web Intelligence", status: "idle", message: "Searching external web sources & validating citations", active: false },
  collecting: { id: "collecting", label: "Evidence Synthesis", status: "idle", message: "Aggregating and deduplicating findings" },
  critique: { id: "critique", label: "Critic & Verification", status: "idle", message: "Fact verification and rigor scoring", score: "" },
  writing: { id: "writing", label: "Report Formulation", status: "idle", message: "Synthesizing comprehensive analytical report" },
  finalizing: { id: "finalizing", label: "Visuals & Diagrams", status: "idle", message: "Generating technical illustrations & charts" },
  saving: { id: "saving", label: "Persistence", status: "idle", message: "Archiving report to persistent storage" },
};

export const useResearch = () => {
  const { getIdToken } = useAuth();
  const [isStreaming, setIsStreaming] = useState(false);
  const [stages, setStages] = useState(INITIAL_STAGES);
  const [currentStage, setCurrentStage] = useState(null);
  const [activeQuestion, setActiveQuestion] = useState("");
  const [finalReport, setFinalReport] = useState("");
  const [reportData, setReportData] = useState(null);
  const [error, setError] = useState(null);

  const abortControllerRef = useRef(null);

  const resetResearch = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setStages(INITIAL_STAGES);
    setCurrentStage(null);
    setActiveQuestion("");
    setFinalReport("");
    setReportData(null);
    setError(null);
  }, []);

  const stopResearch = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const handleStageEvent = useCallback((event) => {
    if (event.type === "stage_update") {
      const stageName = event.stage;
      setCurrentStage(stageName);

      setStages((prev) => {
        const next = { ...prev };

        // Mark previous stages as completed if needed
        const stageKeys = Object.keys(next);
        const currentIndex = stageKeys.indexOf(stageName);
        if (currentIndex > 0) {
          for (let i = 0; i < currentIndex; i++) {
            const k = stageKeys[i];
            if (k !== "web_search" && next[k].status !== "completed") {
              next[k] = { ...next[k], status: "completed" };
            }
          }
        }

        if (next[stageName]) {
          next[stageName] = {
            ...next[stageName],
            status: event.status || "running",
            message: event.message || next[stageName].message,
            count: event.researcher_count || next[stageName].count,
            score: event.message?.includes("Score:") ? event.message.split("Score:")[1]?.trim() : next[stageName].score,
          };
        }

        if (event.web_search_detected || stageName === "web_search") {
          next.web_search = {
            ...next.web_search,
            status: "completed",
            active: true,
            message: event.message || "Live web data retrieved",
          };
        }

        return next;
      });
    } else if (event.type === "complete") {
      setIsStreaming(false);
      setCurrentStage("complete");
      setStages((prev) => {
        const completed = {};
        for (const [k, v] of Object.entries(prev)) {
          completed[k] = { ...v, status: "completed" };
        }
        return completed;
      });

      if (event.data) {
        setReportData(event.data);
        setFinalReport(event.data.final_report || "");
      }
    } else if (event.type === "error") {
      setError(event.message || "Research encountered an unexpected error");
      setIsStreaming(false);
    }
  }, []);

  const startResearch = useCallback(async (question) => {
    if (!question || !question.trim()) return;

    resetResearch();
    setIsStreaming(true);
    setActiveQuestion(question.trim());
    setError(null);

    // Initial stage active
    setStages((prev) => ({
      ...prev,
      planning: { ...prev.planning, status: "running", message: "Structuring research goals and subtopics..." },
    }));
    setCurrentStage("planning");

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const token = await getIdToken();
      if (!token) {
        throw new Error("Authentication required. Please sign in.");
      }

      await streamResearch(
        question.trim(),
        token,
        {
          onEvent: (evt) => handleStageEvent(evt),
          onError: (err) => {
            setError(err.message || "Failed during research stream");
            setIsStreaming(false);
          },
          onComplete: (data) => {
            handleStageEvent(data);
          },
        },
        controller.signal
      );
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(err.message || "Failed to start research");
      }
      setIsStreaming(false);
    }
  }, [getIdToken, handleStageEvent, resetResearch]);

  return {
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
  };
};

export default useResearch;
