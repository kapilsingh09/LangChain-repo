// Generate a unique session ID for the backend conversation
function generateSessionId() {
    return 'sess_' + Math.random().toString(36).substring(2, 15);
}

// Robust storage wrapper to prevent crashes if extension isn't reloaded yet
const storage = {
    get: (keys, callback) => {
        try {
            if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
                chrome.storage.local.get(keys, callback);
                return;
            }
        } catch (e) {
            console.warn("chrome.storage.local not available, falling back to localStorage:", e);
        }
        
        // Fallback to localStorage
        const result = {};
        keys.forEach(key => {
            const val = localStorage.getItem(key);
            try {
                result[key] = val ? JSON.parse(val) : null;
            } catch {
                result[key] = val;
            }
        });
        callback(result);
    },
    set: (data) => {
        try {
            if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
                chrome.storage.local.set(data);
                return;
            }
        } catch (e) {
            console.warn("chrome.storage.local not available, falling back to localStorage:", e);
        }
        
        // Fallback to localStorage
        Object.keys(data).forEach(key => {
            localStorage.setItem(key, JSON.stringify(data[key]));
        });
    }
};

// Configuration
const API_BASE_URL = "http://localhost:8000";

// State
let currentVideoInfo = null;
let sessionId = null;
let chatHistory = [];
let savedApiKey = '';

// DOM Elements
const videoTitleEl = document.getElementById('video-title');
const chatHistoryEl = document.getElementById('chat-history');
const questionInput = document.getElementById('question-input');
const askBtn = document.getElementById('ask-btn');
const resetBtn = document.getElementById('reset-btn');

const modelSelect = document.getElementById('model-select');
const apiKeyContainer = document.getElementById('api-key-container');
const apiKeyInput = document.getElementById('api-key-input');
const saveSetupBtn = document.getElementById('save-setup-btn');

const setupContainer = document.getElementById('setup-container');
const activeModelContainer = document.getElementById('active-model-container');
const activeModelText = document.getElementById('active-model-text');
const changeModelBtn = document.getElementById('change-model-btn');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // 1. Get the current active tab
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const tab = tabs[0];
    
    if (tab && tab.url && tab.url.includes('youtube.com/watch')) {
        const urlParams = new URL(tab.url).searchParams;
        const videoId = urlParams.get('v');
        
        if (videoId) {
            currentVideoInfo = {
                url: tab.url,
                videoId: videoId,
                title: tab.title.replace(/^\(\d+\)\s*/, '').replace(' - YouTube', '')
            };
            
            videoTitleEl.textContent = `Current Video: ${currentVideoInfo.title}`;
            videoTitleEl.title = currentVideoInfo.title;
            
            const thumbnailEl = document.getElementById('video-thumbnail');
            if (thumbnailEl) {
                thumbnailEl.src = `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
                thumbnailEl.style.display = 'block';
            }
            questionInput.disabled = false;
            askBtn.disabled = false;

            // Load state from chrome.storage
            loadState(videoId);

        } else {
            videoTitleEl.textContent = "Status: Invalid YouTube URL";
            showError("Could not detect video ID from URL.");
        }
    } else {
        videoTitleEl.textContent = "Status: Not on a YouTube video";
        showError("Please open a YouTube video first to use YouTube RAG.");
    }
});

// Load state from storage
function loadState(videoId) {
    storage.get(['apiKey', 'selectedModel', 'videoId', 'sessionId', 'chatHistory'], (result) => {
        // Restore API Key and Model
        if (result.selectedModel) {
            modelSelect.value = result.selectedModel;
        }
        if (result.apiKey) {
            savedApiKey = result.apiKey;
            apiKeyInput.value = savedApiKey;
        }
        
        // Show active container if we have a complete setup
        if (result.selectedModel && (result.selectedModel === 'free' || result.apiKey)) {
            showActiveModelView();
        } else {
            showSetupView();
        }

        // Restore chat history if video matches
        if (result.videoId === videoId && result.sessionId && result.chatHistory) {
            sessionId = result.sessionId;
            chatHistory = result.chatHistory;
            renderChatHistory();
        } else {
            // New video or no history, start fresh
            sessionId = generateSessionId();
            chatHistory = [];
            storage.set({ videoId: videoId, sessionId: sessionId, chatHistory: [] });
            addMessage("bot", "Hello! I'm ready to answer questions about this video. What would you like to know?");
        }
    });
}

function showSetupView() {
    setupContainer.style.display = 'flex';
    activeModelContainer.style.display = 'none';
    
    // Toggle API input based on selected model
    if (modelSelect.value === 'free') {
        apiKeyContainer.style.display = 'none';
    } else {
        apiKeyContainer.style.display = 'flex';
    }
}

function showActiveModelView() {
    setupContainer.style.display = 'none';
    activeModelContainer.style.display = 'flex';
    
    let modelName = "Free Model";
    if (modelSelect.value === 'gemini') modelName = "Gemini";
    if (modelSelect.value === 'grok') modelName = "Grok";
    activeModelText.textContent = `Active: ${modelName}`;
}


// Event Listeners
askBtn.addEventListener('click', handleAskQuestion);
questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleAskQuestion();
});

resetBtn.addEventListener('click', () => {
    sessionId = generateSessionId();
    chatHistory = [];
    chatHistoryEl.innerHTML = '';
    
    if (currentVideoInfo) {
        storage.set({ sessionId: sessionId, chatHistory: chatHistory });
        addMessage("bot", "Conversation reset. What would you like to know?");
    }
});

modelSelect.addEventListener('change', (e) => {
    if (e.target.value === 'free') {
        apiKeyContainer.style.display = 'none';
    } else {
        apiKeyContainer.style.display = 'flex';
    }
});

saveSetupBtn.addEventListener('click', () => {
    const model = modelSelect.value;
    let key = '';
    
    if (model !== 'free') {
        key = apiKeyInput.value.trim();
        if (!key) {
            showError(`Please enter a valid API key for ${model}.`);
            return;
        }
    }
    
    savedApiKey = key;
    storage.set({ 
        selectedModel: model,
        apiKey: savedApiKey 
    });
    
    showActiveModelView();
});

changeModelBtn.addEventListener('click', () => {
    showSetupView();
});

// Functions
async function handleAskQuestion() {
    // If in setup mode and asking a question, try saving first
    if (setupContainer.style.display === 'flex') {
        saveSetupBtn.click();
        if (setupContainer.style.display === 'flex') {
             // Validation failed
             return; 
        }
    }

    const question = questionInput.value.trim();
    const model = modelSelect.value;
    const apiKey = savedApiKey;
    
    if (!question || !currentVideoInfo) return;

    if (model !== 'free' && !apiKey) {
        showError(`Please enter a valid API key for the ${model} model.`);
        return;
    }
    
    addMessage("user", question);
    questionInput.value = '';
    
    setLoadingState(true);
    const loadingId = addLoadingIndicator();
    
    try {
        const response = await fetch(`${API_BASE_URL}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                youtube_url: currentVideoInfo.url,
                question: question,
                session_id: sessionId,
                model: model,
                api_key: apiKey
            })
        });
        
        removeElement(loadingId);

        const contentType = response.headers.get('content-type') || '';

        // JSON response means an error from the backend
        if (contentType.includes('application/json')) {
            const data = await response.json();
            if (data.error) {
                showError(data.error + (data.details ? `: ${data.details}` : ""));
            } else {
                showError("Received an unexpected response from the server.");
            }
            return;
        }

        // Handle unexpected non-OK responses
        if (!response.ok) {
            showError(`Server error: ${response.status} ${response.statusText}`);
            return;
        }

        // Streaming text/plain response — read progressively
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        // Create a bot message bubble for progressive token updates
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', 'bot-message');
        chatHistoryEl.appendChild(msgDiv);

        let fullAnswer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value, { stream: true });
            fullAnswer += text;
            msgDiv.textContent = fullAnswer;
            scrollToBottom();
        }

        // Save the complete streamed message to chat history
        if (fullAnswer) {
            chatHistory.push({ sender: 'bot', text: fullAnswer });
            storage.set({ chatHistory: chatHistory });
        }

    } catch (err) {
        removeElement(loadingId);
        showError("Unable to connect to the RAG server. Make sure the FastAPI backend is running.");
        console.error("Popup Error:", err);
    } finally {
        setLoadingState(false);
    }
}

function addMessage(sender, text, isError = false) {
    if (!isError) {
        chatHistory.push({ sender, text });
        storage.set({ chatHistory: chatHistory });
    }
    renderMessage(sender, text, isError);
}

function renderMessage(sender, text, isError = false) {
    const msgDiv = document.createElement('div');
    if (isError) {
        msgDiv.classList.add('message', 'error-message');
    } else {
        msgDiv.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
    }
    msgDiv.textContent = text;
    chatHistoryEl.appendChild(msgDiv);
    scrollToBottom();
}

function renderChatHistory() {
    chatHistoryEl.innerHTML = '';
    chatHistory.forEach(msg => {
        renderMessage(msg.sender, msg.text);
    });
}

function showError(text) {
    addMessage("bot", text, true);
}

function addLoadingIndicator() {
    const id = 'loading-' + Date.now();
    const loadingDiv = document.createElement('div');
    loadingDiv.id = id;
    loadingDiv.classList.add('loading');
    
    const spinner = document.createElement('div');
    spinner.classList.add('spinner');
    
    const text = document.createElement('span');
    text.textContent = "Thinking...";
    
    loadingDiv.appendChild(spinner);
    loadingDiv.appendChild(text);
    
    chatHistoryEl.appendChild(loadingDiv);
    scrollToBottom();
    return id;
}

function removeElement(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function setLoadingState(isLoading) {
    questionInput.disabled = isLoading;
    askBtn.disabled = isLoading;
    if (!isLoading) {
        questionInput.focus();
    }
}

function scrollToBottom() {
    chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
}
