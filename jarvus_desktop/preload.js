const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Window management
  getWindowBounds: () => ipcRenderer.invoke('get-window-bounds'),
  setWindowPosition: (x, y) => ipcRenderer.invoke('set-window-position', x, y),
  showWindow: () => ipcRenderer.invoke('show-window'),
  hideWindow: () => ipcRenderer.invoke('hide-window'),
  isWindowVisible: () => ipcRenderer.invoke('is-window-visible'),
  
  // Dragging
  startDrag: (startX) => ipcRenderer.send('start-drag', startX),
  drag: (currentX) => ipcRenderer.send('drag', currentX),
  endDrag: () => ipcRenderer.send('end-drag'),
  
  // Button actions
  loginClick: () => ipcRenderer.invoke('login-click'),
  chatClick: () => ipcRenderer.invoke('chat-click'),
  optionsClick: () => ipcRenderer.invoke('options-click'),
  
  // Login modal support
  openLoginModal: (url) => ipcRenderer.send('open-login-modal', url),
  onLoginModalClosed: (callback) => {
    ipcRenderer.removeAllListeners('login-modal-closed');
    ipcRenderer.on('login-modal-closed', callback);
  },
  
  // Chat toggle support
  onToggleChat: (callback) => {
    ipcRenderer.removeAllListeners('toggle-chat');
    ipcRenderer.on('toggle-chat', callback);
  },
  
  // Control bar movement support
  onMoveControlBar: (callback) => {
    ipcRenderer.removeAllListeners('move-control-bar');
    ipcRenderer.on('move-control-bar', callback);
  },
  
  // Stop control bar movement support
  onStopMoveControlBar: (callback) => {
    ipcRenderer.removeAllListeners('stop-move-control-bar');
    ipcRenderer.on('stop-move-control-bar', callback);
  },
  
  // Control bar visibility toggle support
  onToggleControlBarVisibility: (callback) => {
    ipcRenderer.removeAllListeners('toggle-control-bar-visibility');
    ipcRenderer.on('toggle-control-bar-visibility', callback);
  },
  
  // Token management
  storeAuthTokens: (tokens) => ipcRenderer.invoke('store-auth-tokens', tokens),
  getAuthTokens: () => ipcRenderer.invoke('get-auth-tokens'),
  clearAuthTokens: () => ipcRenderer.invoke('clear-auth-tokens'),
  
  // Browser management
  launchBrowser: () => ipcRenderer.invoke('launch-browser'),
  closeBrowser: () => ipcRenderer.invoke('close-browser'),
  
  // Platform info
  platform: process.platform,

  // Click-through toggle
  setIgnoreMouseEvents: (ignore) => ipcRenderer.send('set-ignore-mouse-events', ignore),
  
  // Profile management
  discoverChromeProfiles: () => ipcRenderer.invoke('discover-chrome-profiles'),
  getDefaultChromeProfile: () => ipcRenderer.invoke('get-default-chrome-profile'),
  launchBrowserWithProfile: (profileName) => ipcRenderer.invoke('launch-browser-with-profile', profileName),
  getChromeProfileInfo: (profileName) => ipcRenderer.invoke('get-chrome-profile-info', profileName),
  getDecryptedProfilePath: () => ipcRenderer.invoke('get-decrypted-profile-path'),
  syncProfileData: () => ipcRenderer.invoke('sync-profile-data')
}); 