// Configuration
const API_BASE_URL = "http://localhost:8000";
const WEB_SEARCH_MARKER = '\u001eWEB_SEARCH_USED\u001e';
const RAG_MARKER = '\u001eRAG_USED\u001e';
let activeRequest = null;

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "ASK_QUESTION") {
        // Start streaming process asynchronously
        handleStreamingRequest(message.payload);
        // Respond immediately so popup knows it started
        sendResponse({ status: "started" });
    } else if (message.type === "CANCEL_GENERATION") {
        if (activeRequest && activeRequest.requestId === message.requestId) {
            activeRequest.controller.abort();
        }
        sendResponse({ status: "cancelling" });
    }
});

async function handleStreamingRequest(payload) {
    const controller = new AbortController();
    const request = { requestId: payload.requestId, controller };
    activeRequest = request;
    let fullAnswer = '';
    let pendingStreamText = '';
    let webSearchUsed = false;
    let ragUsed = false;
    let history = [];

    async function consumeStreamText(text, flush = false) {
        pendingStreamText += text;
        
        let markerIndex = pendingStreamText.indexOf(WEB_SEARCH_MARKER);
        while (markerIndex !== -1) {
            fullAnswer += pendingStreamText.slice(0, markerIndex);
            pendingStreamText = pendingStreamText.slice(markerIndex + WEB_SEARCH_MARKER.length);
            webSearchUsed = true;
            markerIndex = pendingStreamText.indexOf(WEB_SEARCH_MARKER);
        }

        let ragMarkerIndex = pendingStreamText.indexOf(RAG_MARKER);
        while (ragMarkerIndex !== -1) {
            fullAnswer += pendingStreamText.slice(0, ragMarkerIndex);
            pendingStreamText = pendingStreamText.slice(ragMarkerIndex + RAG_MARKER.length);
            ragUsed = true;
            ragMarkerIndex = pendingStreamText.indexOf(RAG_MARKER);
        }

        if (flush) {
            fullAnswer += pendingStreamText;
            pendingStreamText = '';
        } else {
            let partialMarkerLength = 0;
            const markers = [WEB_SEARCH_MARKER, RAG_MARKER];
            for (const marker of markers) {
                const maxLength = Math.min(pendingStreamText.length, marker.length - 1);
                for (let length = maxLength; length > 0; length--) {
                    if (marker.startsWith(pendingStreamText.slice(-length))) {
                        partialMarkerLength = Math.max(partialMarkerLength, length);
                        break;
                    }
                }
            }
            
            const visibleLength = pendingStreamText.length - partialMarkerLength;
            fullAnswer += pendingStreamText.slice(0, visibleLength);
            pendingStreamText = pendingStreamText.slice(visibleLength);
        }

        await chrome.storage.local.set({
            currentStream: fullAnswer,
            currentWebSearchUsed: webSearchUsed,
            currentRagUsed: ragUsed
        });
    }

    try {
        // 1. Initialize state first so popup can show the loader immediately
        await chrome.storage.local.set({
            isGenerating: true,
            currentStream: "",
            currentWebSearchUsed: false,
            currentRagUsed: false,
            currentError: null,
            currentRequestId: payload.requestId
        });

        // 2. Add user question to history immediately
        const storageData = await chrome.storage.local.get(['chatHistory']);
        history = storageData.chatHistory || [];
        history.push({ sender: 'user', text: payload.question });
        await chrome.storage.local.set({ chatHistory: history });

        // 3. Initiate fetch
        const response = await fetch(`${API_BASE_URL}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            signal: controller.signal
        });

        const contentType = response.headers.get('content-type') || '';

        // 4. Handle JSON Error Responses
        if (contentType.includes('application/json')) {
            const data = await response.json();
            throw new Error((data.error || 'Request failed') + (data.details ? `: ${data.details}` : ""));
        }

        if (!response.ok) {
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }

        // 5. Read Stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value, { stream: true });
            await consumeStreamText(text);
        }

        await consumeStreamText(decoder.decode(), true);

        // 6. Complete Stream: move to history, clear stream
        history.push({ sender: 'bot', text: fullAnswer, webSearchUsed, ragUsed });
        await chrome.storage.local.set({
            chatHistory: history,
            currentStream: "",
            currentWebSearchUsed: false,
            currentRagUsed: false,
            isGenerating: false,
            currentRequestId: null
        });

    } catch (error) {
        if (controller.signal.aborted || error.name === 'AbortError') {
            await consumeStreamText('', true);
            if (fullAnswer) {
                const latest = await chrome.storage.local.get(['chatHistory']);
                history = latest.chatHistory || history;
                history.push({ sender: 'bot', text: fullAnswer, webSearchUsed, ragUsed });
            }
            await chrome.storage.local.set({
                chatHistory: history,
                currentStream: "",
                currentWebSearchUsed: false,
                currentRagUsed: false,
                isGenerating: false,
                currentRequestId: null,
                currentError: null
            });
            return;
        }

        console.error("Background Fetch Error:", error);
        await chrome.storage.local.set({
            isGenerating: false,
            currentStream: "",
            currentWebSearchUsed: false,
            currentRagUsed: false,
            currentRequestId: null,
            currentError: error.message || "Network error or backend unavailable"
        });
    } finally {
        if (activeRequest === request) activeRequest = null;
    }
}
