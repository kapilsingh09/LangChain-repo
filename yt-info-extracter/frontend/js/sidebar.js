/**
 * Sidebar Controller (Slidable/Collapsible Panels, Keyboard Shortcuts, and Session History)
 */

const sidebarController = {
  isSidebarCollapsed: false,
  isVideoDockCollapsed: false,

  init() {
    this.bindEvents();
  },

  toggleSidebar(forceState = null) {
    this.isSidebarCollapsed = forceState !== null ? forceState : !this.isSidebarCollapsed;
    const sidebar = document.getElementById('sidebar');
    const expandBtn = document.getElementById('sidebar-expand-floating-btn');
    const toggleBtn = document.getElementById('sidebar-toggle-btn');

    if (!sidebar) return;

    if (this.isSidebarCollapsed) {
      sidebar.classList.add('collapsed');
      if (expandBtn) expandBtn.classList.add('hidden'); // Mini rail handles expand directly
      if (toggleBtn) toggleBtn.classList.add('text-chatgpt-accent');
    } else {
      sidebar.classList.remove('collapsed');
      if (expandBtn) expandBtn.classList.add('hidden');
      if (toggleBtn) toggleBtn.classList.remove('text-chatgpt-accent');
    }
    localStorage.setItem('sidebar_collapsed', this.isSidebarCollapsed ? '1' : '0');
  },

  toggleVideoDock(forceState = null) {
    this.isVideoDockCollapsed = forceState !== null ? forceState : !this.isVideoDockCollapsed;
    const dock = document.getElementById('video-dock-panel');
    const toggleBtn = document.getElementById('toggle-video-panel-btn');
    const resizer = document.getElementById('workspace-resizer');

    if (!dock) return;

    if (this.isVideoDockCollapsed) {
      dock.classList.add('collapsed');
      if (resizer) resizer.style.display = 'none';
      if (toggleBtn) toggleBtn.classList.add('opacity-40');
    } else {
      dock.classList.remove('collapsed');
      if (resizer) resizer.style.display = 'flex';
      if (toggleBtn) toggleBtn.classList.remove('opacity-40');
    }
  },

  bindEvents() {
    // Buttons
    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    const closeBtn = document.getElementById('sidebar-close-btn');
    const expandBtn = document.getElementById('sidebar-expand-floating-btn');
    const dockBtn = document.getElementById('toggle-video-panel-btn');

    if (toggleBtn) toggleBtn.addEventListener('click', () => this.toggleSidebar());
    if (closeBtn) closeBtn.addEventListener('click', () => this.toggleSidebar(true));
    if (expandBtn) expandBtn.addEventListener('click', () => this.toggleSidebar(false));
    if (dockBtn) dockBtn.addEventListener('click', () => this.toggleVideoDock());

    // Mini-Rail Buttons (shown when collapsed)
    const miniExpand = document.getElementById('mini-sidebar-expand-btn');
    const miniNewChat = document.getElementById('mini-new-chat-btn');
    const miniLoadVideo = document.getElementById('mini-load-video-btn');
    const miniChats = document.getElementById('mini-chats-btn');
    const miniVideos = document.getElementById('mini-videos-btn');

    if (miniExpand) miniExpand.addEventListener('click', () => this.toggleSidebar(false));
    if (miniNewChat) {
      miniNewChat.addEventListener('click', () => {
        this.toggleSidebar(false);
        const newChatBtn = document.getElementById('new-chat-btn');
        if (newChatBtn) newChatBtn.click();
      });
    }
    if (miniLoadVideo) {
      miniLoadVideo.addEventListener('click', () => {
        this.toggleSidebar(false);
        const urlInput = document.getElementById('video-url-input');
        if (urlInput) {
          urlInput.focus();
          urlInput.select();
        }
      });
    }
    if (miniChats) {
      miniChats.addEventListener('click', () => {
        this.toggleSidebar(false);
        const list = document.getElementById('chat-list');
        if (list) list.scrollIntoView({ behavior: 'smooth' });
      });
    }
    if (miniVideos) {
      miniVideos.addEventListener('click', () => {
        this.toggleSidebar(false);
        const list = document.getElementById('video-library-list');
        if (list) list.scrollIntoView({ behavior: 'smooth' });
      });
    }

    // Shortcuts: Ctrl+B (Sidebar), Ctrl+N (New Chat)
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        this.toggleSidebar();
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'n') {
        e.preventDefault();
        if (window.createNewChat && window.state && window.state.currentVideo) {
          window.createNewChat(window.state.currentVideo.id, 'New Research Chat');
        }
      }
    });
  }
};

window.sidebarController = sidebarController;
