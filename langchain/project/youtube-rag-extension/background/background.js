// Configuration
const API_BASE_URL = "http://localhost:8000";

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    
    if (message.type === "ASK_QUESTION") {
        
        // Handle the async fetch request
        // We must return true from the listener to indicate we will sendResponse asynchronously
        handleAskQuestion(message.payload)
            .then(data => sendResponse(data))
            .catch(err => {
                console.error("Background Fetch Error:", err);
                sendResponse({ 
                    error: "Network error or backend unavailable", 
                    details: err.message 
                });
            });
            
        return true; 
    }
});

async function handleAskQuestion(payload) {
    try {
        const response = await fetch(`${API_BASE_URL}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || "Server returned an error");
        }
        
        return data;
        
    } catch (error) {
        // Propagate error to be caught by the .catch() in the message listener
        throw error;
    }
}
