const { app, BrowserWindow, ipcMain, screen, globalShortcut } = require('electron');
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
    height: 300, // Increased height to allow chat popup to be visible below the bar
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
    console.log('[MAIN] Control bar window shown');
  });

  // Prevent window from being closed
  controlBarWindow.on('close', (event) => {
    event.preventDefault();
    controlBarWindow.hide();
    console.log('[MAIN] Control bar window closed (hidden)');
  });

  // Handle window focus to prevent stealing focus from other apps
  controlBarWindow.on('focus', () => {
    controlBarWindow.blur();
    console.log('[MAIN] Control bar window focused (blurred to avoid stealing focus)');
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
    console.log('[MAIN] Drag started');
  });

  ipcMain.on('drag', (event, currentX) => {
    if (isDragging) {
      const deltaX = currentX - dragStartX;
      const newX = Math.max(0, Math.min(windowStartX + deltaX, screen.getPrimaryDisplay().workAreaSize.width - 300));
      controlBarWindow.setPosition(newX, controlBarWindow.getPosition()[1]);
      console.log('[MAIN] Dragging, newX:', newX);
    }
  });

  ipcMain.on('end-drag', () => {
    isDragging = false;
    console.log('[MAIN] Drag ended');
  });

  // Handle button clicks
  ipcMain.handle('login-click', () => {
    console.log('[MAIN] Login button clicked');
  });

  ipcMain.handle('chat-click', () => {
    console.log('[MAIN] Chat button clicked');
  });

  ipcMain.handle('options-click', () => {
    console.log('[MAIN] Options button clicked');
  });

  // Enable click-through except for interactive elements
  controlBarWindow.setIgnoreMouseEvents(true, { forward: true });

  ipcMain.on('set-ignore-mouse-events', (event, ignore) => {
    controlBarWindow.setIgnoreMouseEvents(ignore, { forward: true });
  });
}

// App event handlers
app.whenReady().then(() => {
  createControlBarWindow();
  console.log('[MAIN] App ready, control bar window created');

  // Register DevTools shortcut
  globalShortcut.register('CommandOrControl+Alt+I', () => {
    if (controlBarWindow) {
      controlBarWindow.webContents.openDevTools({ mode: 'detach' });
      console.log('[MAIN] DevTools opened via shortcut');
    }
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createControlBarWindow();
      console.log('[MAIN] App activated, control bar window created');
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
    console.log('[MAIN] All windows closed, app quit');
  }
});

// Prevent app from quitting when all windows are closed
app.on('before-quit', (event) => {
  event.preventDefault();
  app.hide();
  console.log('[MAIN] App before quit, hiding');
});

// Handle app hiding/showing
app.on('hide', () => {
  if (controlBarWindow) {
    controlBarWindow.hide();
    console.log('[MAIN] App hidden, control bar window hidden');
  }
});

app.on('show', () => {
  if (controlBarWindow) {
    controlBarWindow.show();
    console.log('[MAIN] App shown, control bar window shown');
  }
}); 