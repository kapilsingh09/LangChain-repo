// Generate a unique session ID for the backend conversation
function generateSessionId() {
    return 'sess_' + Math.random().toString(36).substring(2, 15);
}

// Robust storage wrapper
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
let isBannerVisible = true;
let isModelPillVisible = true;

// DOM Elements
const videoTitleEl = document.getElementById('video-title');
const videoThumbnailEl = document.getElementById('video-thumbnail');
const chatHistoryEl = document.getElementById('chat-history');
const questionInput = document.getElementById('question-input');
const askBtn = document.getElementById('ask-btn');
const resetBtn = document.getElementById('reset-btn');
const settingsBtn = document.getElementById('settings-btn');
const closeSettingsBtn = document.getElementById('close-settings-btn');

const modelSelect = document.getElementById('model-select');
const apiKeyContainer = document.getElementById('api-key-container');
const apiKeyInput = document.getElementById('api-key-input');
const saveSetupBtn = document.getElementById('save-setup-btn');

const setupContainer = document.getElementById('setup-container');
const activeModelText = document.getElementById('active-model-text');
const modelPillContainer = document.getElementById('model-pill-container');
const modelPill = document.getElementById('model-pill');

// Toggle Elements
const toggleBannerBtn = document.getElementById('toggle-banner-btn');
const toggleBannerIcon = document.getElementById('toggle-banner-icon');
const videoBanner = document.getElementById('video-banner');

const toggleModelBtn = document.getElementById('toggle-model-btn');
const toggleModelIcon = document.getElementById('toggle-model-icon');

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
            
            videoTitleEl.textContent = currentVideoInfo.title;
            videoTitleEl.title = currentVideoInfo.title;
            
            videoThumbnailEl.src = `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
            videoThumbnailEl.style.display = 'block';
            
            questionInput.disabled = false;
            askBtn.disabled = false;

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
    storage.get(['apiKey', 'selectedModel', 'videoId', 'sessionId', 'chatHistory', 'isBannerVisible', 'isModelPillVisible'], (result) => {
        
        // Restore Toggles
        if (result.isBannerVisible !== undefined) {
            isBannerVisible = result.isBannerVisible;
            updateBannerVisibility();
        }
        if (result.isModelPillVisible !== undefined) {
            isModelPillVisible = result.isModelPillVisible;
            updateModelPillVisibility();
        }

        // Restore API Key and Model
        if (result.selectedModel) {
            modelSelect.value = result.selectedModel;
            updateActiveModelText();
        }
        if (result.apiKey) {
            savedApiKey = result.apiKey;
            apiKeyInput.value = savedApiKey;
        }
        
        // Show/Hide API key input based on model
        updateSettingsUI();

        // Check if settings are missing (if gemini/grok selected but no key)
        if (result.selectedModel !== 'free' && !result.apiKey) {
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

function updateActiveModelText() {
    let modelName = "Free Model";
    if (modelSelect.value === 'gemini') modelName = "Gemini";
    if (modelSelect.value === 'grok') modelName = "Grok";
    activeModelText.textContent = modelName;
}

function updateSettingsUI() {
    if (modelSelect.value === 'free') {
        apiKeyContainer.classList.add('hidden');
    } else {
        apiKeyContainer.classList.remove('hidden');
    }
}

function showSetupView() {
    setupContainer.classList.remove('hidden');
    setupContainer.classList.add('flex');
}

function hideSetupView() {
    setupContainer.classList.add('hidden');
    setupContainer.classList.remove('flex');
}

// --- Toggle Logic ---

function updateBannerVisibility() {
    if (isBannerVisible) {
        videoBanner.classList.remove('hidden-banner');
        toggleBannerIcon.classList.remove('fa-chevron-down');
        toggleBannerIcon.classList.add('fa-chevron-up');
    } else {
        videoBanner.classList.add('hidden-banner');
        toggleBannerIcon.classList.remove('fa-chevron-up');
        toggleBannerIcon.classList.add('fa-chevron-down');
    }
}

toggleBannerBtn.addEventListener('click', () => {
    isBannerVisible = !isBannerVisible;
    storage.set({ isBannerVisible });
    updateBannerVisibility();
});

function updateModelPillVisibility() {
    if (isModelPillVisible) {
        modelPill.classList.remove('opacity-0', 'scale-90', 'absolute');
        modelPill.classList.add('opacity-100', 'scale-100');
        setTimeout(() => { if (isModelPillVisible) modelPill.style.visibility = 'visible'; }, 300);
        toggleModelIcon.classList.remove('fa-eye');
        toggleModelIcon.classList.add('fa-eye-slash');
    } else {
        modelPill.classList.remove('opacity-100', 'scale-100');
        modelPill.classList.add('opacity-0', 'scale-90', 'absolute');
        setTimeout(() => { if (!isModelPillVisible) modelPill.style.visibility = 'hidden'; }, 300);
        toggleModelIcon.classList.remove('fa-eye-slash');
        toggleModelIcon.classList.add('fa-eye');
    }
}

toggleModelBtn.addEventListener('click', () => {
    isModelPillVisible = !isModelPillVisible;
    storage.set({ isModelPillVisible });
    updateModelPillVisibility();
});

// --- Event Listeners ---

settingsBtn.addEventListener('click', () => showSetupView());
closeSettingsBtn.addEventListener('click', () => hideSetupView());

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

modelSelect.addEventListener('change', updateSettingsUI);

saveSetupBtn.addEventListener('click', () => {
    const model = modelSelect.value;
    let key = '';
    
    if (model !== 'free') {
        key = apiKeyInput.value.trim();
        if (!key) {
            // Can add a temporary red border or toast here if needed
            apiKeyInput.classList.add('border-red-500');
            setTimeout(() => apiKeyInput.classList.remove('border-red-500'), 2000);
            return;
        }
    }
    
    savedApiKey = key;
    storage.set({ 
        selectedModel: model,
        apiKey: savedApiKey 
    });
    
    updateActiveModelText();
    hideSetupView();
});

// --- Functions ---

async function handleAskQuestion() {
    const question = questionInput.value.trim();
    const model = modelSelect.value;
    const apiKey = savedApiKey;
    
    if (!question || !currentVideoInfo) return;

    if (model !== 'free' && !apiKey) {
        showError(`Please configure your API key for ${model} in settings.`);
        showSetupView();
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

        // Streaming text/plain response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        // Create a bot message bubble
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

        if (fullAnswer) {
            chatHistory.push({ sender: 'bot', text: fullAnswer });
            storage.set({ chatHistory: chatHistory });
        }

    } catch (err) {
        removeElement(loadingId);
        showError("Unable to connect to the server. Make sure FastAPI is running.");
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
