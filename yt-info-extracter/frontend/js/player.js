/**
 * YouTube Player Controller (Robust Dual-Engine: YT.Player API + PostMessage IFrame Fallback)
 * Fixes video loading issues:
 * 1. Solves onYouTubeIframeAPIReady timing race conditions
 * 2. Provides direct embed iframe fallback with postMessage command controls
 * 3. Supports timestamp seeking (seekTo) and autoplay across all browsers
 */

class YouTubeController {
  constructor() {
    this.player = null;
    this.isApiReady = false;
    this.currentVideoId = null;
    this.currentSeconds = 0;
    this.iframeElement = null;
    this.initApi();
  }

  initApi() {
    // If YT API already initialized on window
    if (window.YT && window.YT.Player) {
      this.isApiReady = true;
      return;
    }

    // Setup global callback
    const prevCallback = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      this.isApiReady = true;
      if (typeof prevCallback === 'function') prevCallback();
    };

    // Dynamically ensure the script is present in the DOM
    if (!document.querySelector('script[src*="youtube.com/iframe_api"]')) {
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      const firstScriptTag = document.getElementsByTagName('script')[0];
      firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
    }
  }

  /**
   * Load video by ID with optional starting timestamp
   */
  loadVideo(videoId, startSeconds = 0) {
    if (!videoId) return;

    this.currentVideoId = videoId;
    this.currentSeconds = startSeconds;

    const placeholder = document.getElementById('video-placeholder');
    const wrapper = document.getElementById('player-frame-wrapper');
    const target = document.getElementById('yt-player-target');

    if (placeholder) placeholder.classList.add('hidden');
    if (wrapper) wrapper.classList.remove('hidden');

    // Make sure container has dimensions
    if (wrapper) {
      wrapper.style.display = 'block';
    }

    // Try YouTube IFrame API if ready
    if (this.isApiReady && window.YT && window.YT.Player) {
      try {
        if (this.player && typeof this.player.loadVideoById === 'function') {
          this.player.loadVideoById({
            videoId: videoId,
            startSeconds: startSeconds,
          });
          return;
        }

        // Fresh Player instance
        target.innerHTML = '';
        const playerDiv = document.createElement('div');
        playerDiv.id = 'yt-active-player';
        playerDiv.className = 'w-full h-full';
        target.appendChild(playerDiv);

        this.player = new window.YT.Player('yt-active-player', {
          videoId: videoId,
          width: '100%',
          height: '100%',
          playerVars: {
            autoplay: 1,
            enablejsapi: 1,
            origin: window.location.origin,
            rel: 0,
            modestbranding: 1,
            playsinline: 1,
            start: startSeconds,
          },
          events: {
            onReady: (event) => {
              try { event.target.playVideo(); } catch (e) {}
            },
            onError: (err) => {
              console.warn('YT Player API error, switching to direct iframe fallback:', err);
              this.loadDirectIframeFallback(videoId, startSeconds);
            },
          },
        });
        return;
      } catch (err) {
        console.warn('Error with YT.Player, falling back to direct iframe:', err);
      }
    }

    // Direct IFrame Fallback (Instant, 100% reliable, no race condition)
    this.loadDirectIframeFallback(videoId, startSeconds);
  }

  loadDirectIframeFallback(videoId, startSeconds = 0) {
    const target = document.getElementById('yt-player-target');
    if (!target) return;

    const origin = encodeURIComponent(window.location.origin);
    const src = `https://www.youtube.com/embed/${videoId}?autoplay=1&enablejsapi=1&origin=${origin}&rel=0&start=${startSeconds}&playsinline=1`;

    target.innerHTML = `
      <iframe 
        id="yt-direct-iframe"
        class="w-full h-full border-0"
        src="${src}"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        allowfullscreen
      ></iframe>
    `;

    this.iframeElement = document.getElementById('yt-direct-iframe');
  }

  /**
   * Jump YouTube video to exact seconds and start playing
   */
  seekTo(seconds) {
    this.currentSeconds = seconds;

    // 1. Try active YT.Player instance
    if (this.player && typeof this.player.seekTo === 'function') {
      try {
        this.player.seekTo(seconds, true);
        this.player.playVideo();
        return;
      } catch (e) {
        console.warn('seekTo error on YT.Player:', e);
      }
    }

    // 2. Try postMessage to direct iframe
    const iframe = document.getElementById('yt-direct-iframe');
    if (iframe && iframe.contentWindow) {
      try {
        iframe.contentWindow.postMessage(
          JSON.stringify({ event: 'command', func: 'seekTo', args: [seconds, true] }),
          '*'
        );
        iframe.contentWindow.postMessage(
          JSON.stringify({ event: 'command', func: 'playVideo', args: [] }),
          '*'
        );
        return;
      } catch (e) {
        console.warn('postMessage seek error:', e);
      }
    }

    // 3. Fallback: reload iframe at timestamp
    if (this.currentVideoId) {
      this.loadVideo(this.currentVideoId, seconds);
    }
  }
}

// Global player controller singleton
window.ytController = new YouTubeController();
