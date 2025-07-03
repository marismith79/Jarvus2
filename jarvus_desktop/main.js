const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');
const Store = require('electron-store');

const store = new Store();

let controlBarWindow = null;
let isDragging = false;
let dragStartX = 0;
let windowStartX = 0;

function createControlBarWindow() {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;
  
  // Create the control bar window
  controlBarWindow = new BrowserWindow({
    width: 300,
    height: 60,
    x: Math.floor((width - 300) / 2), // Center horizontally
    y: 20, // 20px from top
    frame: false,
    transparent: true,
    resizable: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // Load the control bar HTML
  controlBarWindow.loadFile(path.join(__dirname, 'renderer', 'control-bar.html'));

  // Set window properties for macOS
  if (process.platform === 'darwin') {
    controlBarWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
    controlBarWindow.setAlwaysOnTop(true, 'screen-saver');
  }

  // Show window when ready
  controlBarWindow.once('ready-to-show', () => {
    controlBarWindow.show();
  });

  // Prevent window from being closed
  controlBarWindow.on('close', (event) => {
    event.preventDefault();
    controlBarWindow.hide();
  });

  // Handle window focus to prevent stealing focus from other apps
  controlBarWindow.on('focus', () => {
    // Don't steal focus from other applications
    controlBarWindow.blur();
  });

  // Handle IPC messages from renderer
  ipcMain.handle('get-window-bounds', () => {
    return controlBarWindow.getBounds();
  });

  ipcMain.handle('set-window-position', (event, x, y) => {
    controlBarWindow.setPosition(x, y);
  });

  ipcMain.handle('show-window', () => {
    controlBarWindow.show();
  });

  ipcMain.handle('hide-window', () => {
    controlBarWindow.hide();
  });

  // Handle window dragging
  ipcMain.on('start-drag', (event, startX) => {
    isDragging = true;
    dragStartX = startX;
    windowStartX = controlBarWindow.getPosition()[0];
  });

  ipcMain.on('drag', (event, currentX) => {
    if (isDragging) {
      const deltaX = currentX - dragStartX;
      const newX = Math.max(0, Math.min(windowStartX + deltaX, screen.getPrimaryDisplay().workAreaSize.width - 300));
      controlBarWindow.setPosition(newX, controlBarWindow.getPosition()[1]);
    }
  });

  ipcMain.on('end-drag', () => {
    isDragging = false;
  });

  // Handle button clicks
  ipcMain.handle('login-click', () => {
    console.log('Login button clicked');
    // TODO: Implement login functionality
  });

  ipcMain.handle('chat-click', () => {
    console.log('Chat button clicked');
    // TODO: Implement chat functionality
  });

  ipcMain.handle('options-click', () => {
    console.log('Options button clicked');
    // TODO: Implement options menu
  });
}

// App event handlers
app.whenReady().then(() => {
  createControlBarWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createControlBarWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Prevent app from quitting when all windows are closed
app.on('before-quit', (event) => {
  event.preventDefault();
  app.hide();
});

// Handle app hiding/showing
app.on('hide', () => {
  if (controlBarWindow) {
    controlBarWindow.hide();
  }
});

app.on('show', () => {
  if (controlBarWindow) {
    controlBarWindow.show();
  }
}); 