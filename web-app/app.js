const STORAGE_KEY = 'youtube-copilot-web-v1';
const DEFAULT_API_URL = 'http://localhost:8000';

function createSessionId() {
  return globalThis.crypto?.randomUUID?.() ?? `session-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function readSavedState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    return {
      apiUrl: typeof saved.apiUrl === 'string' ? saved.apiUrl : DEFAULT_API_URL,
      model: ['groq', 'gemini'].includes(saved.model) ? saved.model : 'groq',
      youtubeUrl: typeof saved.youtubeUrl === 'string' ? saved.youtubeUrl : '',
      videoId: typeof saved.videoId === 'string' ? saved.videoId : '',
      sessionId: typeof saved.sessionId === 'string' ? saved.sessionId : createSessionId(),
      messages: Array.isArray(saved.messages) ? saved.messages.filter((message) =>
        message && ['user', 'assistant', 'error'].includes(message.role) && typeof message.text === 'string'
      ) : [],
    };
  } catch {
    return { apiUrl: DEFAULT_API_URL, model: 'groq', youtubeUrl: '', videoId: '', sessionId: createSessionId(), messages: [] };
  }
}

const state = readSavedState();
const videoForm = document.getElementById('video-form');
const youtubeUrlInput = document.getElementById('youtube-url');
const videoThumbnail = document.getElementById('video-thumbnail');
const thumbnailPlaceholder = document.getElementById('thumbnail-placeholder');
const videoTitle = document.getElementById('video-title');
const videoState = document.getElementById('video-state');
const openVideoLink = document.getElementById('open-video');
const modelSelect = document.getElementById('model-select');
const apiUrlInput = document.getElementById('api-url');
const backendIndicator = document.getElementById('backend-indicator');
const backendStatus = document.getElementById('backend-status');
const chatHistory = document.getElementById('chat-history');
const questionForm = document.getElementById('question-form');
const questionInput = document.getElementById('question-input');
const sendButton = document.getElementById('send-button');
const sendLabel = document.getElementById('send-label');
const promptButtons = document.querySelectorAll('[data-prompt]');

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (error) {
    console.warn('Could not save chat state:', error);
  }
}

function parseVideoUrl(value) {
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new Error('Enter a valid YouTube video URL.');
  }

  const host = url.hostname.toLowerCase().replace(/^www\./, '');
  let videoId = '';
  if (host === 'youtu.be') {
    videoId = url.pathname.split('/').filter(Boolean)[0] || '';
  } else if (host === 'youtube.com' || host === 'm.youtube.com' || host === 'youtube-nocookie.com') {
    if (url.pathname === '/watch') videoId = url.searchParams.get('v') || '';
    else videoId = url.pathname.split('/').filter(Boolean)[1] || '';
  } else {
    throw new Error('Use a link from youtube.com or youtu.be.');
  }

  if (!/^[A-Za-z0-9_-]{11}$/.test(videoId)) {
    throw new Error('That link does not contain a valid YouTube video ID.');
  }
  return videoId;
}

function renderVideo() {
  youtubeUrlInput.value = state.youtubeUrl;
  if (!state.videoId) {
    videoThumbnail.hidden = true;
    thumbnailPlaceholder.hidden = false;
    videoTitle.textContent = 'Add a YouTube link to begin';
    videoState.textContent = 'NO VIDEO';
    videoState.classList.remove('loaded');
    openVideoLink.hidden = true;
    questionInput.disabled = true;
    sendButton.disabled = true;
    return;
  }

  videoThumbnail.src = `https://img.youtube.com/vi/${encodeURIComponent(state.videoId)}/mqdefault.jpg`;
  videoThumbnail.hidden = false;
  thumbnailPlaceholder.hidden = true;
  videoTitle.textContent = `YouTube video · ${state.videoId}`;
  videoState.textContent = 'READY';
  videoState.classList.add('loaded');
  openVideoLink.href = state.youtubeUrl;
  openVideoLink.hidden = false;
  questionInput.disabled = false;
  sendButton.disabled = false;
}

function createMessageElement(role, text) {
  const element = document.createElement('div');
  element.className = `message ${role}`;
  element.textContent = text;
  return element;
}

function renderMessages() {
  chatHistory.replaceChildren();
  if (state.messages.length === 0) {
    const emptyState = document.createElement('div');
    emptyState.className = 'empty-state';
    emptyState.innerHTML = '<div class="empty-glyph" aria-hidden="true">✳</div><p class="empty-title">A better way to follow along.</p><p class="empty-copy">Load a video, then ask about its ideas, examples, or key takeaways.</p><div class="prompt-list" aria-label="Example questions"><button type="button" class="prompt-button" data-prompt="Summarize the main ideas in this video">Summarize the main ideas <span>↗</span></button><button type="button" class="prompt-button" data-prompt="What are the most important examples?">Find the important examples <span>↗</span></button><button type="button" class="prompt-button" data-prompt="Explain the hardest concept in simple terms">Explain a difficult concept <span>↗</span></button></div>';
    chatHistory.append(emptyState);
    emptyState.querySelectorAll('[data-prompt]').forEach((button) => {
      button.addEventListener('click', () => setPrompt(button.dataset.prompt));
    });
    return;
  }

  for (const message of state.messages) {
    chatHistory.append(createMessageElement(message.role, message.text));
  }
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

function setPrompt(prompt) {
  if (!state.videoId) {
    youtubeUrlInput.focus();
    return;
  }
  questionInput.value = prompt;
  questionInput.focus();
  resizeQuestionInput();
}

function normalizeApiUrl() {
  let url;
  try {
    url = new URL(apiUrlInput.value.trim());
  } catch {
    throw new Error('Enter a valid backend address, such as http://localhost:8000.');
  }
  if (!['http:', 'https:'].includes(url.protocol)) {
    throw new Error('Backend address must use HTTP or HTTPS.');
  }
  return url.href.replace(/\/$/, '');
}

async function checkBackend() {
  backendStatus.textContent = 'Checking backend';
  backendIndicator.className = 'status-dot';
  try {
    const baseUrl = normalizeApiUrl();
    state.apiUrl = baseUrl;
    saveState();
    const response = await fetch(`${baseUrl}/health`, { signal: AbortSignal.timeout(5000) });
    if (!response.ok) throw new Error(`Backend returned ${response.status}.`);
    backendIndicator.className = 'status-dot online';
    backendStatus.textContent = 'Backend connected';
  } catch (error) {
    backendIndicator.className = 'status-dot offline';
    backendStatus.textContent = error.name === 'TimeoutError' ? 'Backend timed out' : 'Backend unavailable';
  }
}

function updateVideoError(message) {
  videoTitle.textContent = message;
  videoTitle.classList.add('error-text');
}

videoForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const nextUrl = youtubeUrlInput.value.trim();
  try {
    const nextVideoId = parseVideoUrl(nextUrl);
    videoTitle.classList.remove('error-text');
    if (nextVideoId !== state.videoId) {
      state.sessionId = createSessionId();
      state.messages = [];
    }
    state.youtubeUrl = nextUrl;
    state.videoId = nextVideoId;
    saveState();
    renderVideo();
    renderMessages();
    questionInput.focus();
  } catch (error) {
    updateVideoError(error.message);
  }
});

questionForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question || !state.videoId || sendButton.disabled) return;

  state.messages.push({ role: 'user', text: question });
  saveState();
  chatHistory.querySelector('#empty-state')?.remove();
  const userMessage = createMessageElement('user', question);
  const assistantMessage = createMessageElement('assistant', '');
  assistantMessage.classList.add('streaming');
  chatHistory.append(userMessage, assistantMessage);
  chatHistory.scrollTop = chatHistory.scrollHeight;

  questionInput.value = '';
  resizeQuestionInput();
  questionInput.disabled = true;
  sendButton.disabled = true;
  sendLabel.textContent = 'Wait';

  let answer = '';
  try {
    const baseUrl = normalizeApiUrl();
    state.apiUrl = baseUrl;
    state.model = modelSelect.value;
    saveState();
    const response = await fetch(`${baseUrl}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'text/plain' },
      body: JSON.stringify({
        youtube_url: state.youtubeUrl,
        question,
        session_id: state.sessionId,
        model: state.model,
      }),
    });

    if (!response.ok) {
      const contentType = response.headers.get('content-type') || '';
      const detail = contentType.includes('application/json')
        ? (await response.json()).detail
        : await response.text();
      throw new Error(detail || `Request failed (${response.status}).`);
    }
    if (!response.body) throw new Error('The backend did not return a response stream.');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      answer += decoder.decode(value, { stream: true });
      assistantMessage.textContent = answer;
      chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    answer += decoder.decode();
    assistantMessage.textContent = answer || 'The model returned an empty response.';
    assistantMessage.classList.remove('streaming');
    state.messages.push({ role: 'assistant', text: assistantMessage.textContent });
    saveState();

    if (answer.startsWith('\n\n[ERROR]:')) {
      assistantMessage.classList.add('error');
    }
  } catch (error) {
    assistantMessage.classList.remove('streaming');
    if (answer) {
      assistantMessage.textContent = `${answer}\n\nConnection interrupted: ${error.message}`;
      state.messages.push({ role: 'assistant', text: assistantMessage.textContent });
    } else {
      assistantMessage.remove();
      const errorMessage = createMessageElement('error', error.message || 'Could not reach the backend.');
      chatHistory.append(errorMessage);
      state.messages.push({ role: 'error', text: errorMessage.textContent });
    }
    saveState();
  } finally {
    questionInput.disabled = !state.videoId;
    sendButton.disabled = !state.videoId;
    sendLabel.textContent = 'Send';
    questionInput.focus();
  }
});

function resizeQuestionInput() {
  questionInput.style.height = 'auto';
  questionInput.style.height = `${Math.min(questionInput.scrollHeight, 130)}px`;
}

questionInput.addEventListener('input', resizeQuestionInput);
modelSelect.addEventListener('change', () => {
  state.model = modelSelect.value;
  saveState();
});
apiUrlInput.addEventListener('change', () => {
  state.apiUrl = apiUrlInput.value.trim();
  saveState();
});
document.getElementById('check-backend').addEventListener('click', checkBackend);
document.getElementById('reset-chat').addEventListener('click', () => {
  state.sessionId = createSessionId();
  state.messages = [];
  saveState();
  renderMessages();
  questionInput.focus();
});
promptButtons.forEach((button) => button.addEventListener('click', () => setPrompt(button.dataset.prompt)));

apiUrlInput.value = state.apiUrl;
modelSelect.value = state.model;
renderVideo();
renderMessages();
checkBackend();