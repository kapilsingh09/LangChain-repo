// Generate a unique session ID for the backend conversation
function generateSessionId() {
    return 'sess_' + Math.random().toString(36).substring(2, 15);
}

// State
let currentVideoInfo = null;
let sessionId = generateSessionId(); 

// DOM Elements
const videoTitleEl = document.getElementById('video-title');
const chatHistoryEl = document.getElementById('chat-history');
const questionInput = document.getElementById('question-input');
const askBtn = document.getElementById('ask-btn');
const resetBtn = document.getElementById('reset-btn');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // 1. Get the current active tab
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const tab = tabs[0];
    
    if (tab && tab.url && tab.url.includes('youtube.com/watch')) {
        // We are on a YouTube video page
        const urlParams = new URL(tab.url).searchParams;
        const videoId = urlParams.get('v');
        
        if (videoId) {
            currentVideoInfo = {
                url: tab.url,
                videoId: videoId,
                title: tab.title.replace(/^\(\d+\)\s*/, '').replace(' - YouTube', '') // Remove notification count and suffix
            };
            
            videoTitleEl.textContent = `Current Video: ${currentVideoInfo.title}`;
            videoTitleEl.title = currentVideoInfo.title; // For tooltip on hover
            
            const thumbnailEl = document.getElementById('video-thumbnail');
            if (thumbnailEl) {
                thumbnailEl.src = `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
                thumbnailEl.style.display = 'block';
            }
            questionInput.disabled = false;
            askBtn.disabled = false;
            
            addMessage("bot", "Hello! I'm ready to answer questions about this video. What would you like to know?");
        } else {
            videoTitleEl.textContent = "Status: Invalid YouTube URL";
            showError("Could not detect video ID from URL.");
        }
    } else {
        // Not on a YouTube video
        videoTitleEl.textContent = "Status: Not on a YouTube video";
        showError("Please open a YouTube video first to use YouTube RAG.");
    }
});

// Event Listeners
askBtn.addEventListener('click', handleAskQuestion);
questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleAskQuestion();
    }
});
resetBtn.addEventListener('click', () => {
    sessionId = generateSessionId(); // New session
    chatHistoryEl.innerHTML = '';
    
    if (currentVideoInfo) {
        addMessage("bot", "Conversation reset. What would you like to know?");
    }
});

// Functions
async function handleAskQuestion() {
    const question = questionInput.value.trim();
    
    if (!question || !currentVideoInfo) return;
    
    // 1. Add user message to UI
    addMessage("user", question);
    questionInput.value = '';
    
    // 2. Disable inputs & show loading
    setLoadingState(true);
    const loadingId = addLoadingIndicator();
    
    try {
        // 3. Send message to background script to fetch from FastAPI
        const response = await chrome.runtime.sendMessage({
            type: "ASK_QUESTION",
            payload: {
                youtube_url: currentVideoInfo.url,
                question: question,
                session_id: sessionId
            }
        });
        
        // 4. Remove loading indicator
        removeElement(loadingId);
        
        if (!response) {
            showError("No response received from the extension background script.");
        } else if (response.error) {
            showError(response.error + (response.details ? `: ${response.details}` : ""));
        } else if (response.answer) {
            addMessage("bot", response.answer);
        } else {
            showError("Received an unexpected response from the server.");
        }
    } catch (err) {
        removeElement(loadingId);
        showError("Unable to connect to the RAG server. Make sure the FastAPI backend is running.");
        console.error("Popup Error:", err);
    } finally {
        // 5. Restore inputs
        setLoadingState(false);
    }
}

function addMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
    msgDiv.textContent = text;
    chatHistoryEl.appendChild(msgDiv);
    scrollToBottom();
}

function showError(text) {
    const errDiv = document.createElement('div');
    errDiv.classList.add('message', 'error-message');
    errDiv.textContent = text;
    chatHistoryEl.appendChild(errDiv);
    scrollToBottom();
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
