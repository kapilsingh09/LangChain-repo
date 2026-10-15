/**
 * YouTube Researcher — Main Orchestrator
 * Coordinates:
 * - window.ytController (player.js)
 * - window.chatController (chat.js)
 * - window.sidebarController (sidebar.js)
 * - window.compareController (compare.js)
 */

// ── Application State ────────────────────────────────────────────────────────
window.state = {
  currentVideo: null,
  currentChat: null,
  chats: [],
  allChats: [],
  allVideos: [],
  citations: [],
};

// ── Global Toast Notification ───────────────────────────────────────────────
window.showToast = function(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon font-bold">${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
    <span>${message}</span>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 250);
  }, 3000);
};

// ── Video Operations ────────────────────────────────────────────────────────
async function loadVideo(url) {
  if (!url || !url.trim()) {
    window.showToast('Please enter a YouTube video URL', 'error');
    return;
  }

  const loadBtn = document.getElementById('load-video-btn');
  const btnText = loadBtn ? loadBtn.querySelector('.btn-text') : null;
  if (btnText) btnText.textContent = 'Indexing...';
  if (loadBtn) loadBtn.disabled = true;

  try {
    const res = await fetch('/api/videos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url.trim() }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to load video');
    }

    const video = await res.json();
    window.state.currentVideo = video;
    window.showToast(`Loaded: ${video.title}`, 'success');

    // Load video in YouTube player
    if (window.ytController) {
      window.ytController.loadVideo(video.video_id);
    }

    renderCurrentVideoCard(video);
    renderTranscriptTimeline(video.transcript_segments || []);

    await fetchIndexedVideos();
    await fetchChatsForVideo(video.id);

    if (window.state.chats.length === 0) {
      await createNewChat(video.id, 'Research Session');
    } else {
      await selectChat(window.state.chats[0].id);
    }
  } catch (error) {
    console.error(error);
    window.showToast(error.message, 'error');
  } finally {
    if (btnText) btnText.textContent = 'Index Video';
    if (loadBtn) loadBtn.disabled = false;
  }
}

function renderCurrentVideoCard(video) {
  const card = document.getElementById('current-video-card');
  const thumb = document.getElementById('current-video-thumb');
  const title = document.getElementById('current-video-title');
  const link = document.getElementById('current-video-link');

  if (card) card.classList.remove('hidden');
  if (thumb) thumb.src = video.thumbnail_url;
  if (title) title.textContent = video.title;
  if (link) link.href = video.url;
}

async function fetchIndexedVideos() {
  try {
    const res = await fetch('/api/videos');
    if (!res.ok) return;
    const videos = await res.json();
    window.state.allVideos = videos;

    const countBadge = document.getElementById('video-count-badge');
    if (countBadge) countBadge.textContent = videos.length;

    const list = document.getElementById('video-library-list');
    if (!list) return;

    list.innerHTML = '';
    videos.forEach((v) => {
      const item = document.createElement('div');
      item.className = `flex items-center gap-2 p-1.5 rounded-lg hover:bg-chatgpt-surface cursor-pointer text-xs transition-colors ${window.state.currentVideo && window.state.currentVideo.id === v.id ? 'bg-chatgpt-surface text-white' : 'text-chatgpt-textSecondary'}`;
      item.innerHTML = `
        <img src="${v.thumbnail_url}" class="w-9 h-6 object-cover rounded shrink-0 bg-black" alt="" />
        <span class="truncate" title="${v.title}">${v.title}</span>
      `;
      item.addEventListener('click', async () => {
        const detailRes = await fetch(`/api/videos/${v.id}`);
        if (detailRes.ok) {
          const fullVideo = await detailRes.json();
          window.state.currentVideo = fullVideo;
          if (window.ytController) window.ytController.loadVideo(fullVideo.video_id);
          renderCurrentVideoCard(fullVideo);
          renderTranscriptTimeline(fullVideo.transcript_segments || []);
          await fetchChatsForVideo(fullVideo.id);
          if (window.state.chats.length > 0) {
            await selectChat(window.state.chats[0].id);
          } else {
            await createNewChat(fullVideo.id, 'Research Session');
          }
          fetchIndexedVideos();
        }
      });
      list.appendChild(item);
    });
  } catch (e) {
    console.error('Error fetching video library:', e);
  }
}

// ── Transcript & Highlights Hub ─────────────────────────────────────────────
function renderTranscriptTimeline(segments) {
  const container = document.getElementById('transcript-timeline');
  const countLabel = document.getElementById('transcript-segment-count');
  if (!container) return;

  container.innerHTML = '';
  if (countLabel) countLabel.textContent = `${segments.length} segments`;

  if (!segments || segments.length === 0) {
    container.innerHTML = '<div class="p-3 text-center text-xs text-chatgpt-textMuted">No transcript segments available.</div>';
    return;
  }

  segments.forEach((seg) => {
    const startSec = Math.floor(seg.start || 0);
    const row = document.createElement('div');
    row.className = 'flex items-start gap-2 p-1.5 rounded-lg hover:bg-chatgpt-surface/80 cursor-pointer text-xs transition-colors group';
    row.dataset.text = (seg.text || '').toLowerCase();
    row.innerHTML = `
      <button class="timestamp-jump-btn shrink-0 px-1.5 py-0.5 rounded font-mono text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 group-hover:bg-chatgpt-accent group-hover:text-white border border-emerald-500/20 transition-all flex items-center gap-1" data-seconds="${startSec}">
        <span>▶</span>
        <span>${formatSeconds(startSec)}</span>
      </button>
      <div class="text-chatgpt-textSecondary text-[11px] leading-relaxed">${seg.text}</div>
    `;

    row.querySelector('.timestamp-jump-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      seekToTimestamp(startSec);
    });

    row.addEventListener('click', () => seekToTimestamp(startSec));
    container.appendChild(row);
  });
}

function formatSeconds(totalSecs) {
  const mins = Math.floor(totalSecs / 60);
  const secs = Math.floor(totalSecs % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function seekToTimestamp(seconds) {
  if (window.sidebarController && window.sidebarController.isVideoDockCollapsed) {
    window.sidebarController.toggleVideoDock(false);
  }
  if (window.ytController) {
    window.ytController.seekTo(seconds);
  }
}

function updateCitationsTab() {
  const container = document.getElementById('citations-list');
  if (!container) return;
  container.innerHTML = '';

  if (window.state.citations.length === 0) {
    container.innerHTML = '<div class="p-4 text-center text-xs text-chatgpt-textMuted">No citations generated yet. Ask questions in the chat!</div>';
    return;
  }

  const seen = new Set();
  window.state.citations.forEach((c) => {
    if (seen.has(c.timestamp)) return;
    seen.add(c.timestamp);

    const card = document.createElement('div');
    card.className = 'p-2.5 rounded-lg bg-chatgpt-surface border border-chatgpt-border flex items-center justify-between gap-2';
    card.innerHTML = `
      <div class="flex items-center gap-2">
        <button class="timestamp-pill" data-seconds="${c.seconds}">${c.timestamp}</button>
        <span class="text-xs text-chatgpt-textSecondary">Video Reference Point</span>
      </div>
      <button class="px-2 py-0.5 rounded text-[11px] font-medium text-emerald-400 hover:bg-chatgpt-surfaceHover border border-emerald-500/20" onclick="seekToTimestamp(${c.seconds})">Play</button>
    `;
    card.querySelector('.timestamp-pill').addEventListener('click', () => seekToTimestamp(c.seconds));
    container.appendChild(card);
  });
}

// ── Chat Operations ─────────────────────────────────────────────────────────
async function fetchChatsForVideo(videoId) {
  try {
    const res = await fetch(`/api/chats?video_id=${videoId}`);
    if (!res.ok) return;
    const chats = await res.json();
    window.state.chats = chats;
    const badge = document.getElementById('chat-count-badge');
    if (badge) badge.textContent = chats.length;
    renderChatList(chats);
  } catch (e) {
    console.error('Error fetching chats:', e);
  }
}

function renderChatList(chats) {
  const container = document.getElementById('chat-list');
  if (!container) return;
  container.innerHTML = '';

  if (!chats || chats.length === 0) {
    container.innerHTML = '<div class="p-3 text-center text-chatgpt-textMuted text-xs">No chats yet for this video</div>';
    return;
  }

  chats.forEach((chat) => {
    const item = document.createElement('div');
    item.className = `sidebar-chat-item group ${window.state.currentChat && window.state.currentChat.id === chat.id ? 'active' : ''}`;
    item.innerHTML = `
      <div class="flex items-center gap-2 overflow-hidden flex-1">
        <svg class="w-3.5 h-3.5 shrink-0 text-chatgpt-textMuted group-hover:text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span class="truncate" title="${chat.title}">${chat.title}</span>
      </div>
      <button class="opacity-0 group-hover:opacity-100 p-1 text-chatgpt-textMuted hover:text-rose-400 transition-all" title="Delete chat">
        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"/>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
        </svg>
      </button>
    `;

    item.addEventListener('click', () => selectChat(chat.id));
    item.querySelector('button').addEventListener('click', async (e) => {
      e.stopPropagation();
      if (confirm(`Delete chat "${chat.title}"?`)) {
        await deleteChat(chat.id);
      }
    });

    container.appendChild(item);
  });
}

window.createNewChat = async function(videoId, title = 'New Research Chat') {
  try {
    const res = await fetch('/api/chats', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_id: videoId, title }),
    });

    if (!res.ok) throw new Error('Failed to create chat');
    const newChat = await res.json();
    await fetchChatsForVideo(videoId);
    await selectChat(newChat.id);
    window.showToast('New research session ready', 'success');
  } catch (err) {
    console.error(err);
    window.showToast(err.message, 'error');
  }
};

async function selectChat(chatId) {
  try {
    const res = await fetch(`/api/chats/${chatId}`);
    if (!res.ok) throw new Error('Failed to load chat');
    const chat = await res.json();
    window.state.currentChat = chat;
    window.state.citations = [];

    const titleEl = document.getElementById('active-chat-title');
    const subEl = document.getElementById('active-chat-sub');
    if (titleEl) titleEl.textContent = chat.title;
    if (subEl) subEl.textContent = `• #${chat.id} (${chat.messages.length} messages)`;

    renderChatMessages(chat.messages);
    renderChatList(window.state.chats);
    updateCitationsTab();
  } catch (err) {
    console.error(err);
  }
}

async function deleteChat(chatId) {
  try {
    const res = await fetch(`/api/chats/${chatId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete chat');
    window.showToast('Chat deleted', 'info');
    if (window.state.currentVideo) {
      await fetchChatsForVideo(window.state.currentVideo.id);
      if (window.state.currentChat && window.state.currentChat.id === chatId) {
        if (window.state.chats.length > 0) {
          await selectChat(window.state.chats[0].id);
        } else {
          await window.createNewChat(window.state.currentVideo.id, 'New Research Chat');
        }
      }
    }
  } catch (err) {
    window.showToast(err.message, 'error');
  }
}

function renderChatMessages(messages) {
  const container = document.getElementById('messages-container');
  const welcome = document.getElementById('chat-welcome-state');
  if (!container) return;

  container.querySelectorAll('.message-row').forEach((el) => el.remove());

  if (!messages || messages.length === 0) {
    if (welcome) welcome.classList.remove('hidden');
    return;
  }

  if (welcome) welcome.classList.add('hidden');

  messages.forEach((msg) => {
    if (window.chatController) {
      window.chatController.appendMessageBubble(msg, container);
    }
    if (msg.timestamps_json && msg.timestamps_json.length > 0) {
      window.state.citations.push(...msg.timestamps_json);
    }
  });

  container.scrollTop = container.scrollHeight;
  updateCitationsTab();
}

// ── Send Message ────────────────────────────────────────────────────────────
async function handleSendMessage(content) {
  if (!content || !content.trim()) return;
  if (!window.state.currentChat) {
    window.showToast('Please select or create a research chat first', 'error');
    return;
  }

  const text = content.trim();
  const input = document.getElementById('user-message-input');
  const container = document.getElementById('messages-container');
  const loading = document.getElementById('chat-loading-indicator');

  if (input) {
    input.value = '';
    input.style.height = 'auto';
  }

  // Optimistic message
  if (window.chatController && container) {
    window.chatController.appendMessageBubble({
      id: 'temp-user',
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }, container);
  }

  if (loading) loading.classList.remove('hidden');
  if (container) container.scrollTop = container.scrollHeight;

  try {
    const res = await fetch(`/api/chats/${window.state.currentChat.id}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: text }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to get response');
    }

    const data = await res.json();

    const tempUserEl = container ? container.querySelector('[data-msg-id="temp-user"]') : null;
    if (tempUserEl) tempUserEl.remove();

    if (window.chatController && container) {
      window.chatController.appendMessageBubble(data.user_message, container);
      window.chatController.appendMessageBubble(data.ai_message, container);
    }

    if (data.ai_message.timestamps_json) {
      window.state.citations.push(...data.ai_message.timestamps_json);
      updateCitationsTab();
    }

    if (window.state.currentVideo) {
      fetchChatsForVideo(window.state.currentVideo.id);
    }
  } catch (err) {
    console.error(err);
    window.showToast(err.message, 'error');
  } finally {
    if (loading) loading.classList.add('hidden');
    if (container) container.scrollTop = container.scrollHeight;
  }
}

// ── Master Initialization ───────────────────────────────────────────────────
async function initApp() {
  // 1. Initialize sidebar controller
  if (window.sidebarController) {
    window.sidebarController.init();
  }

  // 2. Bind Header & Chat events
  const loadBtn = document.getElementById('load-video-btn');
  const urlInput = document.getElementById('video-url-input');
  if (loadBtn) loadBtn.addEventListener('click', () => loadVideo(urlInput.value));
  if (urlInput) {
    urlInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        loadVideo(urlInput.value);
      }
    });
  }

  // Sample Chips
  document.querySelectorAll('.sample-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      const url = chip.dataset.url;
      if (urlInput) urlInput.value = url;
      loadVideo(url);
    });
  });

  // Prompt Chips
  document.querySelectorAll('.prompt-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      handleSendMessage(chip.dataset.prompt);
    });
  });

  // Chat Form & Input
  const chatForm = document.getElementById('chat-form');
  const msgInput = document.getElementById('user-message-input');
  if (chatForm) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      if (msgInput) handleSendMessage(msgInput.value);
    });
  }
  if (msgInput) {
    msgInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage(msgInput.value);
      }
    });
    msgInput.addEventListener('input', () => {
      msgInput.style.height = 'auto';
      msgInput.style.height = Math.min(msgInput.scrollHeight, 150) + 'px';
    });
  }

  // New Chat Button
  const newChatBtn = document.getElementById('new-chat-btn');
  if (newChatBtn) {
    newChatBtn.addEventListener('click', () => {
      if (!window.state.currentVideo) {
        window.showToast('Please load a video first', 'info');
        return;
      }
      window.createNewChat(window.state.currentVideo.id, 'New Research Chat');
    });
  }

  // Export Full Chat
  const exportFullBtn = document.getElementById('export-full-chat-btn');
  if (exportFullBtn) {
    exportFullBtn.addEventListener('click', () => {
      if (window.chatController) window.chatController.exportFullChat();
    });
  }

  // View Switcher (Workspace vs Compare)
  const tabWs = document.getElementById('tab-btn-workspace');
  const tabCmp = document.getElementById('tab-btn-compare');
  const viewWs = document.getElementById('view-workspace');
  const viewCmp = document.getElementById('view-compare');

  if (tabWs && tabCmp) {
    tabWs.addEventListener('click', () => {
      tabWs.classList.add('bg-chatgpt-surface', 'text-white');
      tabWs.classList.remove('text-chatgpt-textSecondary');
      tabCmp.classList.remove('bg-chatgpt-surface', 'text-white');
      tabCmp.classList.add('text-chatgpt-textSecondary');
      if (viewWs) viewWs.classList.remove('hidden');
      if (viewCmp) viewCmp.classList.add('hidden');
    });

    tabCmp.addEventListener('click', () => {
      tabCmp.classList.add('bg-chatgpt-surface', 'text-white');
      tabCmp.classList.remove('text-chatgpt-textSecondary');
      tabWs.classList.remove('bg-chatgpt-surface', 'text-white');
      tabWs.classList.add('text-chatgpt-textSecondary');
      if (viewWs) viewWs.classList.add('hidden');
      if (viewCmp) viewCmp.classList.remove('hidden');
      if (window.compareController) window.compareController.loadAllChatsForComparison();
    });
  }

  const runCompareBtn = document.getElementById('run-compare-btn');
  if (runCompareBtn && window.compareController) {
    runCompareBtn.addEventListener('click', () => window.compareController.runComparison());
  }

  // Media Tabs (Transcript vs Citations)
  const tabTrans = document.getElementById('tab-btn-transcript');
  const tabCits = document.getElementById('tab-btn-citations');
  const contentTrans = document.getElementById('tab-content-transcript');
  const contentCits = document.getElementById('tab-content-citations');

  if (tabTrans && tabCits) {
    tabTrans.addEventListener('click', () => {
      tabTrans.classList.add('text-chatgpt-accent', 'border-chatgpt-accent');
      tabTrans.classList.remove('text-chatgpt-textSecondary', 'border-transparent');
      tabCits.classList.remove('text-chatgpt-accent', 'border-chatgpt-accent');
      tabCits.classList.add('text-chatgpt-textSecondary', 'border-transparent');
      if (contentTrans) contentTrans.classList.remove('hidden');
      if (contentCits) contentCits.classList.add('hidden');
    });

    tabCits.addEventListener('click', () => {
      tabCits.classList.add('text-chatgpt-accent', 'border-chatgpt-accent');
      tabCits.classList.remove('text-chatgpt-textSecondary', 'border-transparent');
      tabTrans.classList.remove('text-chatgpt-accent', 'border-chatgpt-accent');
      tabTrans.classList.add('text-chatgpt-textSecondary', 'border-transparent');
      if (contentCits) contentCits.classList.remove('hidden');
      if (contentTrans) contentTrans.classList.add('hidden');
      updateCitationsTab();
    });
  }

  // Transcript live filter
  const transFilter = document.getElementById('transcript-filter');
  if (transFilter) {
    transFilter.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      const rows = document.querySelectorAll('#transcript-timeline div[data-text]');
      let visibleCount = 0;
      rows.forEach((row) => {
        const text = row.dataset.text || '';
        if (!query || text.includes(query)) {
          row.style.display = 'flex';
          visibleCount++;
        } else {
          row.style.display = 'none';
        }
      });
      const countEl = document.getElementById('transcript-segment-count');
      if (countEl) countEl.textContent = `${visibleCount} segments`;
    });
  }

  // 3. Auto-load latest indexed video from SQLite
  await fetchIndexedVideos();
  if (window.state.allVideos && window.state.allVideos.length > 0) {
    const latest = window.state.allVideos[0];
    const res = await fetch(`/api/videos/${latest.id}`);
    if (res.ok) {
      const fullVideo = await res.json();
      window.state.currentVideo = fullVideo;
      if (urlInput) urlInput.value = fullVideo.url;
      if (window.ytController) window.ytController.loadVideo(fullVideo.video_id);
      renderCurrentVideoCard(fullVideo);
      renderTranscriptTimeline(fullVideo.transcript_segments || []);
      await fetchChatsForVideo(fullVideo.id);
      if (window.state.chats.length > 0) {
        await selectChat(window.state.chats[0].id);
      }
    }
  }
}

document.addEventListener('DOMContentLoaded', initApp);
