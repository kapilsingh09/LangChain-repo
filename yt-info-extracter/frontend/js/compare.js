/**
 * Comparison View Controller (Side-by-Side Research Comparison)
 */

const compareController = {
  async loadAllChatsForComparison() {
    try {
      const res = await fetch('/api/chats');
      if (!res.ok) return;
      const chats = await res.json();
      if (window.state) window.state.allChats = chats;

      const selLeft = document.getElementById('compare-select-left');
      const selRight = document.getElementById('compare-select-right');
      if (!selLeft || !selRight) return;

      selLeft.innerHTML = '<option value="">Select Session 1...</option>';
      selRight.innerHTML = '<option value="">Select Session 2...</option>';

      chats.forEach((c) => {
        const opt1 = document.createElement('option');
        opt1.value = c.id;
        opt1.textContent = `#${c.id} - ${c.title}`;
        selLeft.appendChild(opt1);

        const opt2 = document.createElement('option');
        opt2.value = c.id;
        opt2.textContent = `#${c.id} - ${c.title}`;
        selRight.appendChild(opt2);
      });

      if (chats.length >= 2) {
        selLeft.selectedIndex = 1;
        selRight.selectedIndex = 2;
      }
    } catch (e) {
      console.error('Error fetching chats for comparison:', e);
    }
  },

  async runComparison() {
    const selLeft = document.getElementById('compare-select-left');
    const selRight = document.getElementById('compare-select-right');
    const leftId = selLeft ? selLeft.value : null;
    const rightId = selRight ? selRight.value : null;

    if (!leftId || !rightId) {
      if (window.showToast) window.showToast('Please select two chat sessions to compare', 'error');
      return;
    }
    if (leftId === rightId) {
      if (window.showToast) window.showToast('Please pick two different chat sessions', 'error');
      return;
    }

    try {
      const res = await fetch(`/api/compare?chat_ids=${leftId},${rightId}`);
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to compare');
      }

      const [chatLeft, chatRight] = await res.json();

      const colLeftTitle = document.getElementById('col-left-title');
      const colLeftMeta = document.getElementById('col-left-meta');
      const colLeftMessages = document.getElementById('col-left-messages');
      const colRightTitle = document.getElementById('col-right-title');
      const colRightMeta = document.getElementById('col-right-meta');
      const colRightMessages = document.getElementById('col-right-messages');

      if (colLeftTitle) colLeftTitle.textContent = chatLeft.title;
      if (colLeftMeta) colLeftMeta.textContent = `Chat #${chatLeft.id} • ${chatLeft.messages.length} messages`;
      this.renderCompareColumn(colLeftMessages, chatLeft.messages);

      if (colRightTitle) colRightTitle.textContent = chatRight.title;
      if (colRightMeta) colRightMeta.textContent = `Chat #${chatRight.id} • ${chatRight.messages.length} messages`;
      this.renderCompareColumn(colRightMessages, chatRight.messages);

      if (window.showToast) window.showToast('Comparison loaded side-by-side', 'success');
    } catch (err) {
      console.error(err);
      if (window.showToast) window.showToast(err.message, 'error');
    }
  },

  renderCompareColumn(container, messages) {
    if (!container) return;
    container.innerHTML = '';
    if (!messages || messages.length === 0) {
      container.innerHTML = '<div class="text-center text-xs text-chatgpt-textMuted p-6">No messages in this chat.</div>';
      return;
    }

    messages.forEach((m) => {
      const card = document.createElement('div');
      card.className = `flex flex-col gap-1 ${m.role === 'user' ? 'items-end' : 'items-start'}`;
      if (m.role === 'user') {
        card.innerHTML = `<div class="user-bubble text-xs">${chatController.escapeHtml(m.content)}</div>`;
      } else {
        const formatted = chatController.renderMarkdownWithTimestamps(m.content);
        card.innerHTML = `
          <div class="p-3 rounded-xl bg-chatgpt-surface border border-chatgpt-border w-full text-xs">
            <div class="flex items-center justify-between mb-2 pb-1 border-b border-chatgpt-borderSubtle">
              <span class="route-badge rag">${m.route ? m.route.toUpperCase() : 'AI'}</span>
              <span class="text-[10px] text-chatgpt-textMuted">${new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
            <div class="markdown-body">${formatted}</div>
          </div>
        `;
        card.querySelectorAll('.timestamp-pill').forEach((pill) => {
          pill.addEventListener('click', (e) => {
            e.preventDefault();
            const secs = parseInt(pill.dataset.seconds, 10);
            if (!isNaN(secs) && window.ytController) window.ytController.seekTo(secs);
          });
        });
      }
      container.appendChild(card);
    });
  }
};

window.compareController = compareController;
