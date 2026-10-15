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
      if (expandBtn) expandBtn.classList.remove('hidden');
      if (toggleBtn) toggleBtn.classList.add('text-chatgpt-accent');
    } else {
      sidebar.classList.remove('collapsed');
      if (expandBtn) expandBtn.classList.add('hidden');
      if (toggleBtn) toggleBtn.classList.remove('text-chatgpt-accent');
    }
  },

  toggleVideoDock(forceState = null) {
    this.isVideoDockCollapsed = forceState !== null ? forceState : !this.isVideoDockCollapsed;
    const dock = document.getElementById('video-dock-panel');
    const toggleBtn = document.getElementById('toggle-video-panel-btn');

    if (!dock) return;

    if (this.isVideoDockCollapsed) {
      dock.classList.add('collapsed');
      if (toggleBtn) toggleBtn.classList.add('opacity-40');
    } else {
      dock.classList.remove('collapsed');
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
