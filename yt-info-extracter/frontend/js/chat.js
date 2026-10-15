/**
 * Chat & Markdown Controller (ChatGPT Stream, Timestamp Seeking, and Markdown Export)
 */

const chatController = {
  /**
   * Parse timestamp or range to seconds (e.g. 6:38, [6:38-7:06], [6:38‑7:06])
   */
  parseTimestampToSeconds(tsStr) {
    if (!tsStr) return 0;
    const clean = tsStr.replace(/[\[\]\(\)]/g, '').trim();
    const startPart = clean.split(/[\s\-‑–—\u2010\u2011\u2012\u2013\u2014to]+/)[0];
    const parts = startPart.split(':').map(Number);
    if (parts.length === 2) {
      return (parts[0] || 0) * 60 + (parts[1] || 0);
    } else if (parts.length === 3) {
      return (parts[0] || 0) * 3600 + (parts[1] || 0) * 60 + (parts[2] || 0);
    }
    return 0;
  },

  /**
   * Render Markdown and convert timestamp ranges e.g. [6:38‑7:06] into clickable pills
   */
  renderMarkdownWithTimestamps(rawText) {
    if (!rawText) return '';
    let html = window.marked ? window.marked.parse(rawText) : rawText;

    // Handles [6:38-7:06], [6:38‑7:06], [6:38], etc.
    const timestampRegex = /(?:\[|\()(\d{1,2}:\d{2}(?::\d{2})?)(?:\s*(?:[-‑–—\u2010\u2011\u2012\u2013\u2014]|to|&ndash;|&mdash;)\s*(\d{1,2}:\d{2}(?::\d{2})?))?(?:\]|\))/gi;

    html = html.replace(timestampRegex, (match, startTime, endTime) => {
      const startSecs = this.parseTimestampToSeconds(startTime);
      const label = endTime ? `${startTime} – ${endTime}` : startTime;
      const titleText = endTime 
        ? `Click to jump to ${startTime} (segment to ${endTime})` 
        : `Click to jump to ${startTime}`;
      return `<button class="timestamp-pill" data-seconds="${startSecs}" title="${titleText}">${label}</button>`;
    });

    return html;
  },

  /**
   * Escape HTML for user bubbles
   */
  escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, (m) => map[m]);
  },

  /**
   * Append a single message bubble into container
   */
  appendMessageBubble(msg, container) {
    const row = document.createElement('div');
    row.className = `message-row ${msg.role}`;
    row.dataset.msgId = msg.id;

    if (msg.role === 'user') {
      row.innerHTML = `
        <div class="user-bubble">
          ${this.escapeHtml(msg.content)}
        </div>
      `;
    } else {
      const routeClass = msg.route ? msg.route.toLowerCase() : 'rag';
      const routeLabel = msg.route === 'rag' ? 'Vector RAG' : msg.route === 'direct' ? 'Direct Context' : 'LangGraph';
      const formattedHtml = this.renderMarkdownWithTimestamps(msg.content);

      row.innerHTML = `
        <div class="assistant-container">
          <div class="assistant-avatar">
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 14.5v-9l6 4.5-6 4.5z"/>
            </svg>
          </div>

          <div class="assistant-content-wrap">
            <div class="flex items-center gap-2 mb-2">
              <span class="font-semibold text-xs text-white">YouTube Researcher</span>
              <span class="route-badge ${routeClass}">${routeLabel}</span>
              <span class="text-[11px] text-chatgpt-textMuted">${new Date(msg.created_at || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>

            <div class="markdown-body">
              ${formattedHtml}
            </div>

            <div class="flex items-center gap-2 mt-3 pt-2 border-t border-chatgpt-borderSubtle">
              <button class="btn-export-md flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 transition-all" data-msg-id="${msg.id}" title="Generate and download formatted study notes as a .md file">
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                <span>Export MD (.md)</span>
              </button>

              <button class="btn-copy-msg flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-chatgpt-textMuted hover:text-white hover:bg-chatgpt-surface transition-all" title="Copy raw answer">
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>
                  <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
                </svg>
                <span>Copy</span>
              </button>
            </div>
          </div>
        </div>
      `;

      // Export MD Handler
      const exportBtn = row.querySelector('.btn-export-md');
      exportBtn.addEventListener('click', () => this.handleExportMd(msg.id, exportBtn));

      // Copy Handler
      const copyBtn = row.querySelector('.btn-copy-msg');
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(msg.content);
        if (window.showToast) window.showToast('Copied to clipboard', 'info');
      });

      // Timestamp Seeking Handler
      row.querySelectorAll('.timestamp-pill').forEach((pill) => {
        pill.addEventListener('click', (e) => {
          e.preventDefault();
          const secs = parseInt(pill.dataset.seconds, 10);
          if (!isNaN(secs)) {
            if (window.ytController) window.ytController.seekTo(secs);
            if (window.showToast) window.showToast(`Jumped to ${secs}s`, 'success');
          }
        });
      });
    }

    container.appendChild(row);
  },

  /**
   * Export single message as .md and download
   */
  async handleExportMd(messageId, btnElement) {
    if (!window.state || !window.state.currentChat) return;

    const originalContent = btnElement.innerHTML;
    btnElement.innerHTML = `<span>Exporting...</span>`;
    btnElement.disabled = true;

    try {
      const res = await fetch(`/api/chats/${window.state.currentChat.id}/messages/${messageId}/export-md`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instruction: 'auto' }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Export failed');
      }

      const downloadUrl = `/api/chats/${window.state.currentChat.id}/messages/${messageId}/download-md`;
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `research_notes_msg_${messageId}.md`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      if (window.showToast) window.showToast('Markdown file downloaded to laptop!', 'success');
    } catch (err) {
      console.error(err);
      if (window.showToast) window.showToast(err.message, 'error');
    } finally {
      btnElement.innerHTML = originalContent;
      btnElement.disabled = false;
    }
  },

  /**
   * Export full session as .md
   */
  exportFullChat() {
    if (!window.state || !window.state.currentChat || !window.state.currentChat.messages || window.state.currentChat.messages.length === 0) {
      if (window.showToast) window.showToast('No messages to export yet', 'info');
      return;
    }

    let mdContent = `# Research Session: ${window.state.currentChat.title}\n`;
    if (window.state.currentVideo) {
      mdContent += `**Video:** [${window.state.currentVideo.title}](${window.state.currentVideo.url})\n`;
    }
    mdContent += `**Export Date:** ${new Date().toLocaleString()}\n\n---\n\n`;

    window.state.currentChat.messages.forEach((msg) => {
      if (msg.role === 'user') {
        mdContent += `### 👤 Question:\n${msg.content}\n\n`;
      } else {
        mdContent += `### 🤖 Research Findings (${msg.route ? msg.route.toUpperCase() : 'AI'}):\n${msg.content}\n\n---\n\n`;
      }
    });

    const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research_chat_${window.state.currentChat.id}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    if (window.showToast) window.showToast('Full chat exported as .md!', 'success');
  }
};

window.chatController = chatController;
