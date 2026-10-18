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
      item.className = `video-library-item flex items-center justify-between gap-2 p-1.5 rounded-lg hover:bg-chatgpt-surface cursor-pointer text-xs transition-colors group ${window.state.currentVideo && window.state.currentVideo.id === v.id ? 'bg-chatgpt-surface text-white' : 'text-chatgpt-textSecondary'}`;
      item.innerHTML = `
        <div class="flex items-center gap-2 overflow-hidden flex-1 select-none">
          <img src="${v.thumbnail_url}" class="w-9 h-6 object-cover rounded shrink-0 bg-black" alt="" />
          <span class="truncate font-medium text-chatgpt-textPrimary" title="${v.title}">${v.title}</span>
        </div>
        <button class="video-delete-btn p-1 rounded hover:bg-rose-500/20 text-chatgpt-textMuted hover:text-rose-400 transition-all shrink-0" title="Delete video from library">
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
          </svg>
        </button>
      `;

      // Select Video
      item.addEventListener('click', async (e) => {
        if (e.target.closest('.video-delete-btn')) return;
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

      // Delete Video
      const delBtn = item.querySelector('.video-delete-btn');
      if (delBtn) {
        delBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          openVideoDeleteModal(v.id, v.title);
        });
      }

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

  if (window.timelineController && segments.length > 0) {
    const lastSeg = segments[segments.length - 1];
    const totalSecs = Math.ceil((lastSeg.start || 0) + (lastSeg.duration || 0));
    if (totalSecs > 0) {
      window.timelineController.setDuration(totalSecs);
    }
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
    item.querySelector('button').addEventListener('click', (e) => {
      e.stopPropagation();
      openDeleteModal(chat.id, chat.title);
    });

    container.appendChild(item);
  });
}

// ── Custom Delete Confirmation Modals ─────────────────────────────────────────
let pendingDeleteChatId = null;
let pendingDeleteVideoId = null;

function openDeleteModal(chatId, chatTitle) {
  pendingDeleteChatId = chatId;
  const modal = document.getElementById('delete-modal');
  const nameEl = document.getElementById('delete-chat-name');
  if (nameEl) nameEl.textContent = `"${chatTitle}"`;
  if (modal) modal.classList.remove('hidden');
}

function closeDeleteModal() {
  pendingDeleteChatId = null;
  const modal = document.getElementById('delete-modal');
  if (modal) modal.classList.add('hidden');
}

function openVideoDeleteModal(videoId, videoTitle) {
  pendingDeleteVideoId = videoId;
  const modal = document.getElementById('video-delete-modal');
  const titleEl = document.getElementById('delete-video-title');
  if (titleEl) titleEl.textContent = `"${videoTitle}"`;
  if (modal) modal.classList.remove('hidden');
}

function closeVideoDeleteModal() {
  pendingDeleteVideoId = null;
  const modal = document.getElementById('video-delete-modal');
  if (modal) modal.classList.add('hidden');
}

async function confirmVideoDelete() {
  if (!pendingDeleteVideoId) return;
  const vid = pendingDeleteVideoId;
  closeVideoDeleteModal();

  try {
    const res = await fetch(`/api/videos/${vid}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete video');
    window.showToast('Video removed from library', 'info');

    if (window.state.currentVideo && window.state.currentVideo.id === vid) {
      window.state.currentVideo = null;
      window.state.currentChat = null;
      window.state.chats = [];
      const card = document.getElementById('current-video-card');
      if (card) card.classList.add('hidden');
      const placeholder = document.getElementById('video-placeholder');
      const wrapper = document.getElementById('player-frame-wrapper');
      if (placeholder) placeholder.classList.remove('hidden');
      if (wrapper) wrapper.classList.add('hidden');
      const messagesContainer = document.getElementById('messages-container');
      const welcome = document.getElementById('chat-welcome-state');
      if (messagesContainer) {
        messagesContainer.querySelectorAll('.message-row').forEach(el => el.remove());
      }
      if (welcome) welcome.classList.remove('hidden');
      const chatList = document.getElementById('chat-list');
      if (chatList) chatList.innerHTML = '<div class="p-3 text-center text-chatgpt-textMuted text-xs">No video selected</div>';
    }

    await fetchIndexedVideos();
  } catch (err) {
    console.error(err);
    window.showToast(err.message, 'error');
  }
}

window.createNewChat = async function(videoId, title = 'New Research Chat') {
  if (!videoId) {
    window.showToast('Please load or select a video first', 'info');
    return;
  }

  // Prevent duplicate empty chats: If already in an empty chat session, reuse it!
  if (
    window.state.currentChat &&
    window.state.currentChat.video_id === videoId &&
    (!window.state.currentChat.messages || window.state.currentChat.messages.length === 0)
  ) {
    const msgInput = document.getElementById('user-message-input');
    if (msgInput) msgInput.focus();
    window.showToast('Already on a fresh research session', 'info');
    return;
  }

  // If there is an existing empty chat in the list for this video, switch to it!
  if (Array.isArray(window.state.chats)) {
    const existingEmpty = window.state.chats.find(
      (c) => c.video_id === videoId && (!c.messages || c.messages.length === 0)
    );
    if (existingEmpty) {
      await selectChat(existingEmpty.id);
      const msgInput = document.getElementById('user-message-input');
      if (msgInput) msgInput.focus();
      return;
    }
  }

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
    const msgInput = document.getElementById('user-message-input');
    if (msgInput) msgInput.focus();
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

  if (window.timelineController) {
    window.timelineController.renderMarkers(messages);
  }
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
    const res = await fetch(`/api/chats/${window.state.currentChat.id}/messages/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: text }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to connect stream' }));
      throw new Error(err.detail || 'Failed to get response');
    }

    if (loading) loading.classList.add('hidden');

    const streamingBubble = window.chatController && container
      ? window.chatController.createStreamingBubble(container, 'rag')
      : null;

    if (container) container.scrollTop = container.scrollHeight;

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let accumulatedContent = '';
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep partial line in buffer

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data:')) continue;
        const jsonStr = trimmed.replace(/^data:\s*/, '');
        try {
          const event = JSON.parse(jsonStr);

          if (event.type === 'user_message') {
            const tempUserEl = container ? container.querySelector('[data-msg-id="temp-user"]') : null;
            if (tempUserEl) tempUserEl.remove();
            if (window.chatController && container && streamingBubble) {
              const userRow = document.createElement('div');
              userRow.className = 'message-row user';
              userRow.dataset.msgId = event.message.id;
              userRow.innerHTML = `<div class="user-bubble">${window.chatController.escapeHtml(event.message.content)}</div>`;
              container.insertBefore(userRow, streamingBubble.element);
            }
          } else if (event.type === 'route') {
            if (streamingBubble) streamingBubble.setRoute(event.route);
          } else if (event.type === 'delta') {
            accumulatedContent += event.content;
            if (streamingBubble) streamingBubble.updateContent(accumulatedContent);
            if (container) container.scrollTop = container.scrollHeight;
          } else if (event.type === 'done') {
            const aiMsg = event.ai_message;
            if (streamingBubble) {
              streamingBubble.finalize(aiMsg);
            }
            if (aiMsg.timestamps_json) {
              window.state.citations.push(...aiMsg.timestamps_json);
              updateCitationsTab();
            }
            if (window.timelineController && window.state.currentChat) {
              if (!window.state.currentChat.messages) window.state.currentChat.messages = [];
              window.state.currentChat.messages.push(aiMsg);
              window.timelineController.renderMarkers(window.state.currentChat.messages);
            }
            if (window.state.currentVideo) {
              fetchChatsForVideo(window.state.currentVideo.id);
            }
          } else if (event.type === 'error') {
            throw new Error(event.message);
          }
        } catch (parseErr) {
          console.warn('SSE Parse warning:', parseErr);
        }
      }
    }
  } catch (err) {
    console.error(err);
    window.showToast(err.message, 'error');
  } finally {
    if (loading) loading.classList.add('hidden');
    if (container) container.scrollTop = container.scrollHeight;
  }
}

// ── Draggable Panel Resizers (High-Performance Pointer Capture) ─────────────
function initWorkspaceResizer() {
  const resizer = document.getElementById('workspace-resizer');
  const dock = document.getElementById('video-dock-panel');
  const workspace = document.getElementById('view-workspace');
  if (!resizer || !dock || !workspace) return;

  // Restore saved width
  const savedWidth = localStorage.getItem('yt_video_dock_width');
  if (savedWidth) {
    const parsed = parseInt(savedWidth, 10);
    if (parsed >= 280 && parsed <= window.innerWidth * 0.75) {
      dock.style.width = parsed + 'px';
      dock.style.maxWidth = 'none';
    }
  }

  let isDragging = false;

  resizer.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    isDragging = true;
    resizer.setPointerCapture(e.pointerId);
    resizer.classList.add('dragging');
    document.body.classList.add('is-resizing');
  });

  resizer.addEventListener('pointermove', (e) => {
    if (!isDragging) return;
    const workspaceRect = workspace.getBoundingClientRect();
    const newWidth = e.clientX - workspaceRect.left;
    const minWidth = 280;
    const maxWidth = Math.max(minWidth, workspaceRect.width - 320);

    if (newWidth >= minWidth && newWidth <= maxWidth) {
      dock.style.width = `${Math.round(newWidth)}px`;
      dock.style.maxWidth = 'none';
    }
  });

  const stopDrag = (e) => {
    if (isDragging) {
      isDragging = false;
      try { resizer.releasePointerCapture(e.pointerId); } catch (err) {}
      resizer.classList.remove('dragging');
      document.body.classList.remove('is-resizing');
      if (dock.style.width) {
        localStorage.setItem('yt_video_dock_width', parseInt(dock.style.width, 10));
      }
    }
  };

  resizer.addEventListener('pointerup', stopDrag);
  resizer.addEventListener('pointercancel', stopDrag);
}

function initSidebarResizer() {
  const resizer = document.getElementById('sidebar-vertical-resizer');
  const videoLibSection = document.getElementById('video-library-section');
  const sidebar = document.getElementById('sidebar');
  if (!resizer || !videoLibSection || !sidebar) return;

  // Restore saved height
  const savedHeight = localStorage.getItem('yt_sidebar_videolib_height');
  if (savedHeight) {
    const parsed = parseInt(savedHeight, 10);
    if (parsed >= 100 && parsed <= 450) {
      videoLibSection.style.height = parsed + 'px';
    }
  }

  let isDragging = false;

  resizer.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    isDragging = true;
    resizer.setPointerCapture(e.pointerId);
    resizer.classList.add('dragging');
    document.body.classList.add('is-resizing');
  });

  resizer.addEventListener('pointermove', (e) => {
    if (!isDragging) return;
    const sidebarRect = sidebar.getBoundingClientRect();
    const newHeight = sidebarRect.bottom - e.clientY;
    const minHeight = 90;
    const maxHeight = Math.max(minHeight, sidebarRect.height - 160);

    if (newHeight >= minHeight && newHeight <= maxHeight) {
      videoLibSection.style.height = `${Math.round(newHeight)}px`;
    }
  });

  const stopSidebarDrag = (e) => {
    if (isDragging) {
      isDragging = false;
      try { resizer.releasePointerCapture(e.pointerId); } catch (err) {}
      resizer.classList.remove('dragging');
      document.body.classList.remove('is-resizing');
      if (videoLibSection.style.height) {
        localStorage.setItem('yt_sidebar_videolib_height', parseInt(videoLibSection.style.height, 10));
      }
    }
  };

  resizer.addEventListener('pointerup', stopSidebarDrag);
  resizer.addEventListener('pointercancel', stopSidebarDrag);
}

// ── Master Initialization ───────────────────────────────────────────────────
async function initApp() {
  // 1. Initialize sidebar controller
  if (window.sidebarController) {
    window.sidebarController.init();
  }

  // 2. Bind Header & Video Loading events
  const loadBtn = document.getElementById('load-video-btn');
  const urlInput = document.getElementById('video-url-input');
  if (loadBtn) loadBtn.addEventListener('click', () => loadVideo(urlInput ? urlInput.value : ''));
  if (urlInput) {
    urlInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        loadVideo(urlInput.value);
      }
    });
  }

  // Header quick load button
  const headerLoadBtn = document.getElementById('header-load-video-modal-btn');
  if (headerLoadBtn) {
    headerLoadBtn.addEventListener('click', () => {
      const sidebar = document.getElementById('sidebar');
      if (sidebar && sidebar.classList.contains('collapsed') && window.sidebarController) {
        window.sidebarController.toggleSidebar();
      }
      if (urlInput) {
        urlInput.focus();
        urlInput.select();
      }
    });
  }

  // Video placeholder inputs
  const pLoadBtn = document.getElementById('placeholder-load-btn');
  const pUrlInput = document.getElementById('placeholder-video-url-input');
  if (pLoadBtn && pUrlInput) {
    pLoadBtn.addEventListener('click', () => loadVideo(pUrlInput.value));
    pUrlInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        loadVideo(pUrlInput.value);
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
        if (window.state.allVideos && window.state.allVideos.length > 0) {
          const first = window.state.allVideos[0];
          window.createNewChat(first.id, 'New Research Chat');
          return;
        }
        window.showToast('Please load a video first to start researching', 'info');
        return;
      }
      window.createNewChat(window.state.currentVideo.id, 'New Research Chat');
    });
  }

  // Delete Confirmation Modal Event Listeners
  const cancelDelBtn = document.getElementById('cancel-delete-btn');
  const confirmDelBtn = document.getElementById('confirm-delete-btn');
  const delModal = document.getElementById('delete-modal');

  if (cancelDelBtn) cancelDelBtn.addEventListener('click', closeDeleteModal);
  if (confirmDelBtn) {
    confirmDelBtn.addEventListener('click', async () => {
      if (pendingDeleteChatId) {
        const idToDelete = pendingDeleteChatId;
        closeDeleteModal();
        await deleteChat(idToDelete);
      }
    });
  }
  if (delModal) {
    delModal.addEventListener('click', (e) => {
      if (e.target === delModal) closeDeleteModal();
    });
  }
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeDeleteModal();
  });

  // Video Delete Confirmation Modal Event Listeners
  const cancelVidDelBtn = document.getElementById('cancel-video-delete-btn');
  const confirmVidDelBtn = document.getElementById('confirm-video-delete-btn');
  const vidDelModal = document.getElementById('video-delete-modal');

  if (cancelVidDelBtn) cancelVidDelBtn.addEventListener('click', closeVideoDeleteModal);
  if (confirmVidDelBtn) confirmVidDelBtn.addEventListener('click', confirmVideoDelete);
  if (vidDelModal) {
    vidDelModal.addEventListener('click', (e) => {
      if (e.target === vidDelModal) closeVideoDeleteModal();
    });
  }

  // Initialize Draggable Panel Resizers
  initWorkspaceResizer();
  initSidebarResizer();

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
