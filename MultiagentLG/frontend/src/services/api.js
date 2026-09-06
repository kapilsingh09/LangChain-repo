import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Check backend health status
 */
export const checkHealth = async () => {
  try {
    const res = await apiClient.get("/health");
    return res.data;
  } catch (err) {
    console.error("Health check error:", err);
    throw err;
  }
};

/**
 * Fetch authenticated user's research history
 */
export const getResearchHistory = async (token) => {
  try {
    const res = await apiClient.get("/research/history", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return res.data?.researches || [];
  } catch (err) {
    console.error("Fetch history error:", err);
    throw err;
  }
};

/**
 * Fetch a specific research run by ID
 */
export const getResearchById = async (id, token) => {
  try {
    const res = await apiClient.get(`/research/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return res.data;
  } catch (err) {
    console.error(`Fetch research ${id} error:`, err);
    throw err;
  }
};

/**
 * Run synchronous research (fallback)
 */
export const runResearchSync = async (question, token) => {
  try {
    const res = await apiClient.post(
      "/research",
      { question },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return res.data;
  } catch (err) {
    console.error("Sync research error:", err);
    throw err;
  }
};

/**
 * Stream research via SSE over HTTP POST
 * 
 * @param {string} question - The query to research
 * @param {string} token - Firebase ID token
 * @param {Object} callbacks
 * @param {Function} callbacks.onEvent - (eventData) => void
 * @param {Function} callbacks.onError - (error) => void
 * @param {Function} callbacks.onComplete - (finalData) => void
 * @param {AbortSignal} [signal] - Optional AbortSignal to cancel
 */
export const streamResearch = async (question, token, { onEvent, onError, onComplete }, signal) => {
  try {
    const response = await fetch(`${API_BASE_URL}/research/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({ question }),
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorJson;
      try {
        errorJson = JSON.parse(errorText);
      } catch {
        errorJson = { detail: errorText || `HTTP error ${response.status}` };
      }
      throw new Error(errorJson.detail || errorJson.message || "Failed to initiate research stream");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() || ""; // Keep incomplete line in buffer

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith("data:")) continue;

        const dataStr = trimmed.slice(5).trim();
        if (!dataStr) continue;

        try {
          const parsed = JSON.parse(dataStr);
          if (onEvent) {
            onEvent(parsed);
          }

          if (parsed.type === "complete") {
            if (onComplete) onComplete(parsed);
          } else if (parsed.type === "error") {
            if (onError) onError(new Error(parsed.message || "Research pipeline error"));
          }
        } catch (e) {
          console.warn("Failed to parse SSE line:", trimmed, e);
        }
      }
    }
  } catch (err) {
    if (err.name === "AbortError") {
      console.log("Research stream aborted by user");
      return;
    }
    console.error("Stream research error:", err);
    if (onError) onError(err);
    throw err;
  }
};
