const { app, BrowserWindow, ipcMain, screen, globalShortcut } = require('electron');
const path = require('path');
const Store = require('electron-store');
const keytar = require('keytar');
const { spawn } = require('child_process');
const os = require('os');
const fs = require('fs');

const store = new Store();

let controlBarWindow = null;
let isDragging = false;
let dragStartX = 0;
let windowStartX = 0;
let chromeProcess = null;

function createControlBarWindow() {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;
  
  // Create the control bar window
  controlBarWindow = new BrowserWindow({
    width: 500,
    height: 400, // Increased height to allow chat popup to be visible below the bar
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
      preload: path.join(__dirname, 'preload.js'),
      partition: 'persist:main' // Add session sharing for authentication
    }
  });

  // Try to load from Flask server first, fallback to local files
  const flaskUrl = 'http://localhost:5001/control-bar';
  console.log('[MAIN] Attempting to load control bar from Flask server:', flaskUrl);
  
  controlBarWindow.loadURL(flaskUrl)
    .then(() => {
      console.log('[MAIN] Successfully loaded control bar from Flask server');
    })
    .catch((error) => {
      console.log('[MAIN] Flask server not available, falling back to local files:', error.message);
      controlBarWindow.loadFile(path.join(__dirname, 'renderer', 'control-bar.html'))
        .then(() => {
          console.log('[MAIN] Successfully loaded control bar from local files');
        })
        .catch((fallbackError) => {
          console.error('[MAIN] Failed to load control bar from both Flask and local files:', fallbackError);
        });
    });

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

  ipcMain.handle('is-window-visible', () => {
    return controlBarWindow.isVisible();
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

  // Handle login modal
  ipcMain.on('open-login-modal', (event, signinUrl) => {
    console.log('[MAIN] Opening login modal with URL:', signinUrl);
    
    const loginWin = new BrowserWindow({
      width: 500,
      height: 700,
      parent: controlBarWindow,
      modal: true,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'),
        partition: 'persist:main',
      },
    });
    
    loginWin.loadURL(signinUrl);
    
    // Monitor for successful login
    let hasLoggedIn = false;
    
    const captureTokensAndClose = () => {
      if (hasLoggedIn) return;
      hasLoggedIn = true;
      console.log('[MAIN] Login successful, capturing tokens...');
      
      loginWin.webContents.executeJavaScript(`
        fetch('/api/auth-tokens')
          .then(response => response.json())
          .then(data => {
            if (data.success && data.tokens) {
              console.log('[MAIN] Storing tokens in Keychain');
              window.electronAPI.storeAuthTokens(data.tokens);
            }
          })
          .catch(error => {
            console.error('[MAIN] Error capturing tokens:', error);
          });
      `);
      
      setTimeout(() => {
        console.log('[MAIN] Closing login modal');
        loginWin.close();
        controlBarWindow.webContents.send('login-modal-closed');
      }, 2000);
    };
    
    loginWin.webContents.on('did-navigate', (event, url) => {
      console.log('[MAIN] Login modal navigated to:', url);
      if (url.includes('/profile?just_logged_in=1')) {
        captureTokensAndClose();
      }
    });

    loginWin.webContents.on('did-finish-load', () => {
      const currentUrl = loginWin.webContents.getURL();
      console.log('[MAIN] Login modal finished loading:', currentUrl);
      if (currentUrl.includes('/profile?just_logged_in=1')) {
        captureTokensAndClose();
      }
    });

    loginWin.on('closed', () => {
      console.log('[MAIN] Login modal closed');
    });
  });

  // Enable click-through except for interactive elements
  controlBarWindow.setIgnoreMouseEvents(true, { forward: true });

  ipcMain.on('set-ignore-mouse-events', (event, ignore) => {
    controlBarWindow.setIgnoreMouseEvents(ignore, { forward: true });
  });
}

function getChromePath() {
  const platform = os.platform();
  
  if (platform === 'darwin') {
    return '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  } else if (platform === 'win32') {
    return 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  } else if (platform === 'linux') {
    return '/usr/bin/google-chrome';
  } else {
    throw new Error(`Unsupported platform: ${platform}`);
  }
}

function setupWebDriver() {
  console.log('[MAIN] Setting up WebDriver for browser control...');
  
  // Launch Chrome with remote debugging (for WebDriver connection)
  const chromeArgs = [
    '--remote-debugging-port=9222',  // Only this flag needed
    '--no-first-run',
    '--no-default-browser-check',
    // NO --disable-web-security
    // NO profile copying needed
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-features=TranslateUI',
    '--disable-ipc-flooding-protection',
    '--new-window',
    '--force-new-window',
    '--disable-session-crashed-bubble',
    '--disable-infobars',
    '--disable-features=VizDisplayCompositor',
    '--no-default-browser-check',
    '--disable-default-apps',
    '--disable-sync',
    '--disable-background-networking',
    '--disable-component-extensions-with-background-pages',
    '--disable-extensions-file-access-check',
    '--disable-extensions-http-throttling',
    '--disable-hang-monitor',
    '--disable-prompt-on-repost',
    '--disable-domain-reliability',
    '--disable-client-side-phishing-detection',
    '--disable-component-update',
    '--disable-background-mode'
  ];
  
  // Launch Chrome normally (no profile copying needed)
  const chromePath = getChromePath();
  chromeProcess = spawn(chromePath, chromeArgs, {
    stdio: 'pipe',
    detached: false
  });
  
  console.log('[MAIN] Chrome launched with WebDriver support');
}

// App event handlers
app.whenReady().then(() => {
  createControlBarWindow();
  console.log('[MAIN] App ready, control bar window created');
  
  // Setup WebDriver instead of direct Chrome control
  setupWebDriver();

  // Register DevTools shortcut
  globalShortcut.register('CommandOrControl+Alt+I', () => {
    if (controlBarWindow) {
      controlBarWindow.webContents.openDevTools({ mode: 'detach' });
      console.log('[MAIN] DevTools opened via shortcut');
    }
  });

  // Register chat toggle shortcut
  globalShortcut.register('CommandOrControl+Enter', () => {
    if (controlBarWindow) {
      controlBarWindow.webContents.send('toggle-chat');
      console.log('[MAIN] Chat toggle shortcut triggered');
    }
  });

  // Register control bar movement shortcuts
  globalShortcut.register('CommandOrControl+Left', () => {
    if (controlBarWindow) {
      controlBarWindow.webContents.send('move-control-bar', 'left');
      console.log('[MAIN] Move control bar left shortcut triggered');
    }
  });

  globalShortcut.register('CommandOrControl+Right', () => {
    if (controlBarWindow) {
      controlBarWindow.webContents.send('move-control-bar', 'right');
      console.log('[MAIN] Move control bar right shortcut triggered');
    }
  });

  // Register control bar visibility toggle shortcuts
  globalShortcut.register('CommandOrControl+Up', () => {
    if (controlBarWindow) {
      controlBarWindow.webContents.send('toggle-control-bar-visibility');
      console.log('[MAIN] Toggle control bar visibility shortcut triggered (Up)');
    }
  });

  globalShortcut.register('CommandOrControl+Down', () => {
    if (controlBarWindow) {
      controlBarWindow.webContents.send('toggle-control-bar-visibility');
      console.log('[MAIN] Toggle control bar visibility shortcut triggered (Down)');
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

// Clean up Chrome process when app quits
app.on('will-quit', () => {
  if (chromeProcess) {
    console.log('[MAIN] Terminating Chrome process...');
    chromeProcess.kill();
  }
  
  // No profile cleanup needed anymore
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

async function storeAuthTokens(tokens) {
  try {
    await keytar.setPassword('JarvusApp', 'auth_tokens', JSON.stringify(tokens));
    console.log('[MAIN] ✅ Tokens stored in Keychain');
  } catch (error) {
    console.error('[MAIN] ❌ Error storing tokens:', error);
  }
}

async function getAuthTokens() {
  try {
    const tokens = await keytar.getPassword('JarvusApp', 'auth_tokens');
    return tokens ? JSON.parse(tokens) : null;
  } catch (error) {
    console.error('[MAIN] ❌ Error getting tokens:', error);
    return null;
  }
}

async function clearAuthTokens() {
  try {
    await keytar.deletePassword('JarvusApp', 'auth_tokens');
    console.log('[MAIN] ✅ Tokens cleared from Keychain');
  } catch (error) {
    console.error('[MAIN] ❌ Error clearing tokens:', error);
  }
}

ipcMain.handle('store-auth-tokens', async (event, tokens) => {
  console.log('[MAIN] IPC: store-auth-tokens called');
  await storeAuthTokens(tokens);
});

ipcMain.handle('get-auth-tokens', async () => {
  console.log('[MAIN] IPC: get-auth-tokens called');
  return await getAuthTokens();
});

ipcMain.handle('clear-auth-tokens', async () => {
  console.log('[MAIN] IPC: clear-auth-tokens called');
  await clearAuthTokens();
}); 