/**
 * YouTube Researcher — Timeline Scrubber & Glassmorphism Theme Controller
 * Handles:
 * 1. Interactive YouTube-style timeline scrubber with real-time video sync
 * 2. Question & Citation Heat Markers placed dynamically along video duration
 * 3. Click-to-Seek video and Click-to-Locate Chat Message with glow pulse
 * 4. User-controlled Deep Black & Glassmorphism customizer with localStorage persistence
 */

class TimelineController {
  constructor() {
    this.duration = 0;
    this.currentTime = 0;
    this.isDragging = false;
    this.markers = [];
    this.defaultTheme = {
      bg: '#000000',
      card: 'rgba(10, 10, 10, 0.85)',
      surface: 'rgba(16, 16, 16, 0.85)',
      blur: 16,
      opacity: 0.75,
      accent: '#10a37f'
    };
    this.init();
  }

  init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }

  setup() {
    this.initThemeSystem();
    this.bindScrubberEvents();
  }

  // ───────────────────────────────────────────────────────────────────────────
  // 1. Time Formatting Utility
  // ───────────────────────────────────────────────────────────────────────────
  formatTime(totalSeconds) {
    if (isNaN(totalSeconds) || totalSeconds < 0) totalSeconds = 0;
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = Math.floor(totalSeconds % 60);

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }

  // ───────────────────────────────────────────────────────────────────────────
  // 2. Timeline Scrubber & Progress Updates
  // ───────────────────────────────────────────────────────────────────────────
  bindScrubberEvents() {
    const scrubberBar = document.getElementById('timeline-scrubber-bar');
    if (!scrubberBar) return;

    const onPointerMove = (e) => {
      if (!this.isDragging) return;
      this.seekFromPointer(e);
    };

    const onPointerUp = (e) => {
      if (this.isDragging) {
        this.isDragging = false;
        this.seekFromPointer(e);
        document.removeEventListener('mousemove', onPointerMove);
        document.removeEventListener('mouseup', onPointerUp);
        document.removeEventListener('touchmove', onPointerMove);
        document.removeEventListener('touchend', onPointerUp);
      }
    };

    scrubberBar.addEventListener('mousedown', (e) => {
      // Don't trigger drag if clicking directly on a marker pin
      if (e.target.closest('.yt-timeline-marker')) return;
      this.isDragging = true;
      this.seekFromPointer(e);
      document.addEventListener('mousemove', onPointerMove);
      document.addEventListener('mouseup', onPointerUp);
    });

    scrubberBar.addEventListener('touchstart', (e) => {
      if (e.target.closest('.yt-timeline-marker')) return;
      this.isDragging = true;
      const touch = e.touches[0];
      this.seekFromPointer(touch);
      document.addEventListener('touchmove', onPointerMove);
      document.addEventListener('touchend', onPointerUp);
    }, { passive: true });
  }

  seekFromPointer(e) {
    const track = document.getElementById('timeline-track');
    if (!track) return;

    const rect = track.getBoundingClientRect();
    const clientX = e.clientX || (e.touches && e.touches[0] ? e.touches[0].clientX : 0);
    let pct = (clientX - rect.left) / rect.width;
    pct = Math.max(0, Math.min(1, pct));

    const totalDuration = this.getEffectiveDuration();
    if (totalDuration > 0) {
      const targetSecs = Math.floor(pct * totalDuration);
      this.currentTime = targetSecs;
      this.updateProgress(targetSecs, totalDuration);

      if (window.ytController) {
        window.ytController.seekTo(targetSecs);
      }
    }
  }

  getEffectiveDuration() {
    if (this.duration > 0) return this.duration;

    // Check ytController player duration
    if (window.ytController && window.ytController.player && typeof window.ytController.player.getDuration === 'function') {
      const d = window.ytController.player.getDuration();
      if (d > 0) {
        this.duration = d;
        return d;
      }
    }

    // Check state transcript segments
    if (window.state && window.state.currentVideo) {
      if (window.state.currentVideo.duration && window.state.currentVideo.duration > 0) {
        this.duration = window.state.currentVideo.duration;
        return this.duration;
      }
      const segs = window.state.currentVideo.transcript_segments;
      if (Array.isArray(segs) && segs.length > 0) {
        const last = segs[segs.length - 1];
        const maxTime = (last.start || 0) + (last.duration || 0);
        if (maxTime > 0) {
          this.duration = Math.ceil(maxTime);
          return this.duration;
        }
      }
    }
    return 0;
  }

  setDuration(seconds) {
    if (seconds && seconds > 0) {
      this.duration = Math.ceil(seconds);
      const durEl = document.getElementById('timeline-duration-time');
      if (durEl) durEl.textContent = this.formatTime(this.duration);
    }
  }

  updateProgress(currentSecs, totalSecs) {
    this.currentTime = currentSecs;
    if (totalSecs && totalSecs > 0) {
      this.duration = totalSecs;
    } else {
      totalSecs = this.getEffectiveDuration();
    }

    const curEl = document.getElementById('timeline-current-time');
    const durEl = document.getElementById('timeline-duration-time');
    const progressEl = document.getElementById('timeline-progress');
    const scrubberDot = document.getElementById('timeline-scrubber-dot');

    if (curEl) curEl.textContent = this.formatTime(currentSecs);
    if (durEl && totalSecs > 0) durEl.textContent = this.formatTime(totalSecs);

    if (totalSecs > 0 && progressEl && scrubberDot) {
      const pct = Math.min(100, Math.max(0, (currentSecs / totalSecs) * 100));
      progressEl.style.width = `${pct}%`;
      scrubberDot.style.left = `${pct}%`;
    }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // 3. Question & Citation Markers along Timeline Track
  // ───────────────────────────────────────────────────────────────────────────
  renderMarkers(messages, totalDuration) {
    const layer = document.getElementById('timeline-markers-layer');
    const countBadge = document.getElementById('timeline-markers-count');
    if (!layer) return;

    layer.innerHTML = '';
    this.markers = [];

    const duration = totalDuration || this.getEffectiveDuration();
    if (!messages || messages.length === 0 || duration <= 0) {
      if (countBadge) countBadge.textContent = '0 Questions Marked';
      return;
    }

    const colorPalette = [
      { bg: '#10a37f', border: '#34d399', glow: 'rgba(16, 163, 127, 0.8)' }, // Emerald
      { bg: '#06b6d4', border: '#22d3ee', glow: 'rgba(6, 182, 212, 0.8)' },  // Cyan
      { bg: '#8b5cf6', border: '#a78bfa', glow: 'rgba(139, 92, 246, 0.8)' }, // Purple
      { bg: '#f59e0b', border: '#fbbf24', glow: 'rgba(245, 158, 11, 0.8)' }, // Amber
      { bg: '#f43f5e', border: '#fb7185', glow: 'rgba(244, 63, 94, 0.8)' }   // Rose
    ];

    let markerIndex = 0;
    const addedSeconds = new Set();

    messages.forEach((msg, msgIdx) => {
      if (msg.role !== 'assistant') return;

      // Find user question immediately preceding this assistant message
      let userQuestion = '';
      for (let i = msgIdx - 1; i >= 0; i--) {
        if (messages[i].role === 'user') {
          userQuestion = messages[i].content;
          break;
        }
      }

      // Collect timestamps from timestamps_json or regex parse
      const timestamps = [];

      if (Array.isArray(msg.timestamps_json) && msg.timestamps_json.length > 0) {
        msg.timestamps_json.forEach(item => {
          if (typeof item === 'object' && item.start !== undefined) {
            timestamps.push({ seconds: Math.floor(item.start), text: item.text || item.timestamp || '' });
          } else if (typeof item === 'string') {
            const s = window.chatController ? window.chatController.parseTimestampToSeconds(item) : 0;
            timestamps.push({ seconds: s, text: item });
          }
        });
      }

      // Also regex parse from content to capture any [6:38] or [6:38-7:06]
      const tsRegex = /(?:\[|\()(\d{1,2}:\d{2}(?::\d{2})?)(?:\s*(?:[-‑–—\u2010\u2011\u2012\u2013\u2014]|to)\s*(\d{1,2}:\d{2}(?::\d{2})?))?(?:\]|\))/gi;
      let match;
      while ((match = tsRegex.exec(msg.content)) !== null) {
        const startStr = match[1];
        const s = window.chatController ? window.chatController.parseTimestampToSeconds(startStr) : 0;
        if (!timestamps.some(t => Math.abs(t.seconds - s) < 2)) {
          timestamps.push({ seconds: s, text: match[0] });
        }
      }

      // Create pins for each timestamp
      timestamps.forEach(ts => {
        if (ts.seconds <= 0 && addedSeconds.has(0)) return;
        // Group near-duplicate timestamps
        const roundedSecs = Math.round(ts.seconds);
        if (addedSeconds.has(roundedSecs)) return;
        addedSeconds.add(roundedSecs);

        const pct = Math.min(99.5, Math.max(0.5, (ts.seconds / duration) * 100));
        const color = colorPalette[markerIndex % colorPalette.length];
        markerIndex++;

        const pin = document.createElement('div');
        pin.className = 'yt-timeline-marker';
        pin.style.left = `${pct}%`;
        pin.style.backgroundColor = color.bg;
        pin.style.color = color.border;
        pin.style.boxShadow = `0 0 10px ${color.glow}`;
        pin.title = `Jump to ${this.formatTime(ts.seconds)}`;

        const shortLabel = userQuestion 
          ? (userQuestion.length > 40 ? userQuestion.slice(0, 40) + '...' : userQuestion) 
          : 'Question Answer Highlight';

        pin.innerHTML = `
          <div class="yt-marker-tooltip">
            <span class="font-bold text-white">${this.formatTime(ts.seconds)}</span>
            <span class="text-neutral-300 ml-1.5">• ${shortLabel}</span>
            <span class="block text-[10px] text-emerald-400 mt-0.5 font-sans">Click to jump video & locate in chat ↗</span>
          </div>
        `;

        // Click handler: Seek video AND locate message in chat
        pin.addEventListener('click', (e) => {
          e.stopPropagation();
          e.preventDefault();
          this.onMarkerClick(ts.seconds, msg.id, shortLabel);
        });

        layer.appendChild(pin);
        this.markers.push({ seconds: ts.seconds, messageId: msg.id, element: pin });
      });
    });

    if (countBadge) {
      countBadge.textContent = `${this.markers.length} Question${this.markers.length === 1 ? '' : 's'} Marked`;
    }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // 4. Click-to-Seek & Click-to-Locate Chat Message
  // ───────────────────────────────────────────────────────────────────────────
  onMarkerClick(seconds, messageId, questionSnippet = '') {
    // 1. Jump video
    if (window.ytController) {
      window.ytController.seekTo(seconds);
    }
    this.updateProgress(seconds, this.duration);

    // 2. Locate and glow-highlight message in Chat panel
    if (messageId) {
      const container = document.getElementById('messages-container');
      const targetMsg = document.querySelector(`[data-msg-id="${messageId}"]`);

      if (targetMsg) {
        // Remove prior glows
        document.querySelectorAll('.message-glow-highlight').forEach(el => el.classList.remove('message-glow-highlight'));

        targetMsg.scrollIntoView({ behavior: 'smooth', block: 'center' });
        targetMsg.classList.add('message-glow-highlight');

        setTimeout(() => {
          targetMsg.classList.remove('message-glow-highlight');
        }, 3000);
      }
    }

    if (window.showToast) {
      window.showToast(`Jumped to [${this.formatTime(seconds)}] ${questionSnippet ? '— ' + questionSnippet : ''}`, 'info');
    }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // 5. Deep Black & Glassmorphism Theme Customizer
  // ───────────────────────────────────────────────────────────────────────────
  initThemeSystem() {
    const saved = localStorage.getItem('yt_researcher_theme');
    let theme = this.defaultTheme;

    if (saved) {
      try {
        theme = { ...this.defaultTheme, ...JSON.parse(saved) };
      } catch (e) {
        console.warn('Failed to parse saved theme:', e);
      }
    }

    this.applyTheme(theme);
    this.bindThemeModalEvents();
  }

  applyTheme(theme) {
    const root = document.documentElement;
    root.style.setProperty('--bg-app', theme.bg);
    root.style.setProperty('--bg-card', theme.card);
    root.style.setProperty('--bg-surface', theme.surface);
    root.style.setProperty('--glass-blur', `${theme.blur}px`);
    root.style.setProperty('--glass-opacity', theme.opacity);
    root.style.setProperty('--accent-color', theme.accent);
    root.style.setProperty('--accent-glow', `${theme.accent}55`);

    // Ensure direct body background is deep black
    document.body.style.backgroundColor = theme.bg;

    // Persist
    localStorage.setItem('yt_researcher_theme', JSON.stringify(theme));

    // Update UI controls if present
    const blurSlider = document.getElementById('blur-slider');
    const blurVal = document.getElementById('blur-val');
    const opSlider = document.getElementById('opacity-slider');
    const opVal = document.getElementById('opacity-val');

    if (blurSlider) blurSlider.value = theme.blur;
    if (blurVal) blurVal.textContent = `${theme.blur}px`;
    if (opSlider) opSlider.value = Math.round(theme.opacity * 100);
    if (opVal) opVal.textContent = `${Math.round(theme.opacity * 100)}%`;
  }

  getCurrentTheme() {
    const saved = localStorage.getItem('yt_researcher_theme');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) {}
    }
    return { ...this.defaultTheme };
  }

  bindThemeModalEvents() {
    const modal = document.getElementById('theme-modal');
    const openBtn = document.getElementById('theme-customizer-btn');
    const closeBtn = document.getElementById('close-theme-modal-btn');
    const resetBtn = document.getElementById('reset-theme-btn');
    const blurSlider = document.getElementById('blur-slider');
    const blurVal = document.getElementById('blur-val');
    const opSlider = document.getElementById('opacity-slider');
    const opVal = document.getElementById('opacity-val');

    if (!modal) return;

    const openModal = () => modal.classList.remove('hidden');
    const closeModal = () => modal.classList.add('hidden');

    if (openBtn) openBtn.addEventListener('click', openModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
        closeModal();
      }
    });

    // Darkness Presets
    const presetBtns = document.querySelectorAll('.theme-preset-btn');
    presetBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const bg = btn.dataset.bg;
        const card = btn.dataset.card;
        const surface = btn.dataset.surface;
        const current = this.getCurrentTheme();

        presetBtns.forEach(b => b.classList.remove('border-emerald-500', 'active-preset'));
        btn.classList.add('border-emerald-500', 'active-preset');

        this.applyTheme({
          ...current,
          bg: bg,
          card: card,
          surface: surface
        });
      });
    });

    // Glass Blur Slider
    if (blurSlider) {
      blurSlider.addEventListener('input', (e) => {
        const val = e.target.value;
        if (blurVal) blurVal.textContent = `${val}px`;
        const current = this.getCurrentTheme();
        this.applyTheme({ ...current, blur: parseInt(val, 10) });
      });
    }

    // Glass Opacity Slider
    if (opSlider) {
      opSlider.addEventListener('input', (e) => {
        const val = e.target.value;
        if (opVal) opVal.textContent = `${val}%`;
        const current = this.getCurrentTheme();
        this.applyTheme({ ...current, opacity: parseFloat(val) / 100 });
      });
    }

    // Accent Color Palette
    const accentBtns = document.querySelectorAll('.accent-color-btn');
    accentBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const color = btn.dataset.accent;
        accentBtns.forEach(b => b.classList.remove('ring-2', 'ring-white', 'ring-offset-2', 'ring-offset-black'));
        btn.classList.add('ring-2', 'ring-white', 'ring-offset-2', 'ring-offset-black');

        const current = this.getCurrentTheme();
        this.applyTheme({ ...current, accent: color });
      });
    });

    // Reset Defaults
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        this.applyTheme(this.defaultTheme);
        if (window.showToast) window.showToast('Theme reset to defaults', 'info');
      });
    }
  }
}

// Global Singleton
window.timelineController = new TimelineController();
