const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Window management
  getWindowBounds: () => ipcRenderer.invoke('get-window-bounds'),
  setWindowPosition: (x, y) => ipcRenderer.invoke('set-window-position', x, y),
  showWindow: () => ipcRenderer.invoke('show-window'),
  hideWindow: () => ipcRenderer.invoke('hide-window'),
  
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
  
  // Token management
  storeAuthTokens: (tokens) => ipcRenderer.invoke('store-auth-tokens', tokens),
  getAuthTokens: () => ipcRenderer.invoke('get-auth-tokens'),
  clearAuthTokens: () => ipcRenderer.invoke('clear-auth-tokens'),
  
  // Platform info
  platform: process.platform,

  // Click-through toggle
  setIgnoreMouseEvents: (ignore) => ipcRenderer.send('set-ignore-mouse-events', ignore)
}); 