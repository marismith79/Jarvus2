const { app, BrowserWindow, ipcMain, screen, globalShortcut, clipboard } = require('electron');
const path = require('path');
const Store = require('electron-store');
const keytar = require('keytar');
const os = require('os');
const fs = require('fs');
const { spawn } = require('child_process');
const SecureProfileManager = require('./profile-manager');
const ChromeLauncher = require('./launch_browser');
const BrowserAPI = require('./browser_api');

const store = new Store();

// Initialize secure profile manager
const profileManager = new SecureProfileManager();

// Initialize Chrome launcher
let chromeLauncher = null;

// Initialize Browser API server
let browserAPI = null;

// Global error handlers to prevent EIO errors
process.on('uncaughtException', (error) => {
  try {
    console.error('Uncaught Exception:', error);
  } catch (e) {
    // Ignore EIO errors from console output
  }
});

process.on('unhandledRejection', (reason, promise) => {
  try {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  } catch (e) {
    // Ignore EIO errors from console output
  }
});

// Safe console logging to prevent EIO errors
function safeLog(...args) {
  try {
    console.log(...args);
  } catch (e) {
    // Ignore EIO errors from console output
  }
}

function safeWarn(...args) {
  try {
    console.warn(...args);
  } catch (e) {
    // Ignore EIO errors from console output
  }
}

function safeError(...args) {
  try {
    console.error(...args);
  } catch (e) {
    // Ignore EIO errors from console output
  }
}

let controlBarWindow = null;
let isDragging = false;
let dragStartX = 0;
let windowStartX = 0;
let previouslyFocusedWindow = null;

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
  safeLog('[MAIN] Attempting to load control bar from Flask server:', flaskUrl);
  
  controlBarWindow.loadURL(flaskUrl)
    .then(() => {
      safeLog('[MAIN] Successfully loaded control bar from Flask server');
    })
    .catch((error) => {
      safeLog('[MAIN] Flask server not available, falling back to local files:', error.message);
      controlBarWindow.loadFile(path.join(__dirname, 'renderer', 'control-bar.html'))
        .then(() => {
          safeLog('[MAIN] Successfully loaded control bar from local files');
        })
        .catch((fallbackError) => {
          safeError('[MAIN] Failed to load control bar from both Flask and local files:', fallbackError);
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
    safeLog('[MAIN] Control bar window shown');
  });

  // Prevent window from being closed
  controlBarWindow.on('close', (event) => {
    event.preventDefault();
    controlBarWindow.hide();
    safeLog('[MAIN] Control bar window closed (hidden)');
  });

  // Handle IPC messages from renderer
  ipcMain.handle('get-window-bounds', () => {
    return controlBarWindow.getBounds();
  });

  ipcMain.handle('set-window-position', (event, x, y) => {
    controlBarWindow.setPosition(x, y);
  });

  ipcMain.handle('show-window', () => {
    safeLog('[MAIN] show-window IPC handler called');
    
    // On macOS, we don't need to track focus since we use app.hide() to restore focus
    if (process.platform !== 'darwin') {
      // Store the currently focused window BEFORE showing the control bar (for non-macOS platforms)
      const focusedWindow = BrowserWindow.getFocusedWindow();
      safeLog('[MAIN] getFocusedWindow returned:', focusedWindow ? 'window object' : 'null');
      safeLog('[MAIN] controlBarWindow:', controlBarWindow ? 'window object' : 'null');
      safeLog('[MAIN] focusedWindow === controlBarWindow:', focusedWindow === controlBarWindow);
      
      if (focusedWindow && focusedWindow !== controlBarWindow) {
        previouslyFocusedWindow = focusedWindow;
        safeLog('[MAIN] Stored previously focused window before showing control bar');
      } else {
        safeLog('[MAIN] No previously focused window stored (focusedWindow was null or control bar)');
      }
    }
    
    controlBarWindow.show();
    registerControlBarShortcuts();
  });

  ipcMain.handle('hide-window', () => {
    safeLog('[MAIN] hide-window IPC handler called');
    controlBarWindow.hide();
    unregisterControlBarShortcuts();
    
    // On macOS, hide the entire app to restore focus to the previously active application
    if (process.platform === 'darwin') {
      safeLog('[MAIN] Hiding entire app to restore focus to previously active application');
      app.hide();
    } else {
      // For other platforms, try to focus other Electron windows
      safeLog('[MAIN] previouslyFocusedWindow:', previouslyFocusedWindow ? 'window object' : 'null');
      if (previouslyFocusedWindow && !previouslyFocusedWindow.isDestroyed()) {
        previouslyFocusedWindow.focus();
        safeLog('[MAIN] Restored focus to previously focused window');
      } else {
        safeLog('[MAIN] No previously focused window available, trying alternative');
        // If no previously focused window, try to focus the most recently used window
        const allWindows = BrowserWindow.getAllWindows();
        const otherWindows = allWindows.filter(win => win !== controlBarWindow && !win.isDestroyed());
        safeLog('[MAIN] Found', otherWindows.length, 'other windows');
        
        if (otherWindows.length > 0) {
          // Focus the first available window
          otherWindows[0].focus();
          safeLog('[MAIN] Focused alternative window');
        } else {
          safeLog('[MAIN] No alternative windows found to focus');
        }
      }
    }
  });

  ipcMain.handle('is-window-visible', () => {
    safeLog('[MAIN] is-window-visible IPC handler called, returning:', controlBarWindow.isVisible());
    return controlBarWindow.isVisible();
  });

  // Handle window dragging
  ipcMain.on('start-drag', (event, startX) => {
    isDragging = true;
    dragStartX = startX;
    windowStartX = controlBarWindow.getPosition()[0];
    safeLog('[MAIN] Drag started');
  });

  ipcMain.on('drag', (event, currentX) => {
    if (isDragging) {
      const deltaX = currentX - dragStartX;
      const newX = Math.max(0, Math.min(windowStartX + deltaX, screen.getPrimaryDisplay().workAreaSize.width - 300));
      controlBarWindow.setPosition(newX, controlBarWindow.getPosition()[1]);
      safeLog('[MAIN] Dragging, newX:', newX);
    }
  });

  ipcMain.on('end-drag', () => {
    isDragging = false;
    safeLog('[MAIN] Drag ended');
  });

  // Handle button clicks
  ipcMain.handle('login-click', () => {
    safeLog('[MAIN] Login button clicked');
  });

  ipcMain.handle('chat-click', () => {
    safeLog('[MAIN] Chat button clicked');
  });

  ipcMain.handle('options-click', () => {
    safeLog('[MAIN] Options button clicked');
  });

  // Handle login modal
  ipcMain.on('open-login-modal', (event, signinUrl) => {
    safeLog('[MAIN] Opening login modal with URL:', signinUrl);
    
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
      safeLog('[MAIN] Login successful, capturing tokens...');
      
      loginWin.webContents.executeJavaScript(`
        fetch('/api/auth-tokens')
          .then(response => response.json())
          .then(data => {
            if (data.success && data.tokens) {
              safeLog('[MAIN] Storing tokens in Keychain');
              window.electronAPI.storeAuthTokens(data.tokens);
            }
          })
          .catch(error => {
            safeError('[MAIN] Error capturing tokens:', error);
          });
      `);
      
      setTimeout(() => {
        safeLog('[MAIN] Closing login modal');
        loginWin.close();
        controlBarWindow.webContents.send('login-modal-closed');
      }, 2000);
    };
    
    loginWin.webContents.on('did-navigate', (event, url) => {
      safeLog('[MAIN] Login modal navigated to:', url);
      if (url.includes('/profile?just_logged_in=1')) {
        captureTokensAndClose();
      }
    });

    loginWin.webContents.on('did-finish-load', () => {
      const currentUrl = loginWin.webContents.getURL();
      safeLog('[MAIN] Login modal finished loading:', currentUrl);
      if (currentUrl.includes('/profile?just_logged_in=1')) {
        captureTokensAndClose();
      }
    });

    loginWin.on('closed', () => {
      safeLog('[MAIN] Login modal closed');
    });
  });

  // Enable click-through except for interactive elements
  controlBarWindow.setIgnoreMouseEvents(true, { forward: true });

  ipcMain.on('set-ignore-mouse-events', (event, ignore) => {
    controlBarWindow.setIgnoreMouseEvents(ignore, { forward: true });
  });
}

function setupPlaywrightBrowser() {
  safeLog('[MAIN] Setting up Playwright browser control...');
  
  // Launch browser directly from Electron using Node.js Playwright
  setTimeout(async () => {
    safeLog('[MAIN] Launching Chrome browser directly from Electron...');
    
    try {
      // Create new Chrome launcher instance
      chromeLauncher = new ChromeLauncher();
      
      // Launch Chrome with Profile 6
      const result = await chromeLauncher.launchChrome();
      
      if (result.success) {
        safeLog('[MAIN] ✅ Browser launched successfully from Electron');
        safeLog(`[MAIN] WebSocket Endpoint: ${result.connectionInfo.wsEndpoint}`);
        safeLog(`[MAIN] Profile Path: ${result.connectionInfo.profilePath}`);
        
        // Start Browser API server
        safeLog('[MAIN] Starting Browser API server...');
        try {
          browserAPI = new BrowserAPI();
          await browserAPI.start();
          safeLog('[MAIN] ✅ Browser API server started successfully on port 3001');
        } catch (apiError) {
          safeError('[MAIN] ❌ Failed to start Browser API server:', apiError);
        }
      } else {
        safeError('[MAIN] ❌ Failed to launch browser from Electron:', result.error);
      }
    } catch (error) {
      safeError('[MAIN] ❌ Error launching browser from Electron:', error);
    }
    
  }, 1000); // Reduced wait time from 2 seconds to 1 second
  
  safeLog('[MAIN] Browser management is now handled directly by Electron with secure profile integration');
}

function registerVisibilityShortcuts() {
  // Register control bar visibility toggle shortcuts (always active)
  globalShortcut.register('CommandOrControl+Up', () => {
    if (controlBarWindow) {
      controlBarWindow.webContents.send('toggle-control-bar-visibility');
    }
  });
  globalShortcut.register('CommandOrControl+Down', () => {
    if (controlBarWindow) {
      controlBarWindow.webContents.send('toggle-control-bar-visibility');
    }
  });
}

function registerControlBarShortcuts() {
  // Register DevTools shortcut
  globalShortcut.register('CommandOrControl+Alt+I', () => {
    if (controlBarWindow) {
      controlBarWindow.webContents.openDevTools({ mode: 'detach' });
    }
  });
  // Register chat toggle shortcut
  globalShortcut.register('CommandOrControl+Enter', () => {
    if (controlBarWindow) {
      controlBarWindow.webContents.send('toggle-chat');
    }
  });
  // Register control bar movement shortcuts
  globalShortcut.register('CommandOrControl+Left', () => {
    if (controlBarWindow && controlBarWindow.isVisible()) {
      controlBarWindow.webContents.send('move-control-bar', 'left');
    }
  });
  globalShortcut.register('CommandOrControl+Right', () => {
    if (controlBarWindow && controlBarWindow.isVisible()) {
      controlBarWindow.webContents.send('move-control-bar', 'right');
    }
  });
  // Register input bar focus shortcut
  globalShortcut.register('CommandOrControl+Enter', () => {
    if (controlBarWindow && controlBarWindow.isVisible()) {
      controlBarWindow.webContents.send('focus-input-bar');
    }
  });
}

function registerGlobalShortcuts() {
  registerVisibilityShortcuts();
  registerControlBarShortcuts();
}

function unregisterControlBarShortcuts() {
  // Unregister only the control bar specific shortcuts, not visibility toggles
  globalShortcut.unregister('CommandOrControl+Alt+I');
  globalShortcut.unregister('CommandOrControl+Enter');
  globalShortcut.unregister('CommandOrControl+Left');
  globalShortcut.unregister('CommandOrControl+Right');
}

// Add hotkey management IPC handlers
ipcMain.handle('register-shortcuts', () => {
  safeLog('[MAIN] register-shortcuts IPC handler called');
  registerControlBarShortcuts();
});

ipcMain.handle('unregister-shortcuts', () => {
  safeLog('[MAIN] unregister-shortcuts IPC handler called');
  unregisterControlBarShortcuts();
});

// App event handlers
app.whenReady().then(() => {
  createControlBarWindow();
  safeLog('[MAIN] App ready, control bar window created');
  registerGlobalShortcuts(); // This registers both visibility and control bar shortcuts
  
  // Setup Playwright browser control
  setupPlaywrightBrowser();  // <-- THIS STARTS THE DEBUG BROWSER

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createControlBarWindow();
      safeLog('[MAIN] App activated, control bar window created');
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
    safeLog('[MAIN] All windows closed, app quit');
  }
});

// Prevent app from quitting when all windows are closed
app.on('before-quit', (event) => {
  event.preventDefault();
  app.hide();
  safeLog('[MAIN] App before quit, hiding');
});

// Clean up when app quits
app.on('will-quit', () => {
  safeLog('[MAIN] App quitting...');
  
  // Stop Browser API server
  if (browserAPI) {
    browserAPI.stop();
    safeLog('[MAIN] Browser API server stopped');
  }
  
  // Close browser
  if (chromeLauncher) {
    chromeLauncher.closeBrowser().then(() => {
      safeLog('[MAIN] Browser closed during app quit');
    }).catch((error) => {
      safeError('[MAIN] Error closing browser during quit:', error);
    });
  }
  
  safeLog('[MAIN] Browser cleanup completed');
});

// Handle app hiding/showing
app.on('hide', () => {
  if (controlBarWindow) {
    controlBarWindow.hide();
    safeLog('[MAIN] App hidden, control bar window hidden');
  }
});

app.on('show', () => {
  if (controlBarWindow) {
    controlBarWindow.show();
    safeLog('[MAIN] App shown, control bar window shown');
  }
});

async function storeAuthTokens(tokens) {
  try {
    await keytar.setPassword('JarvusApp', 'auth_tokens', JSON.stringify(tokens));
    safeLog('[MAIN] ✅ Tokens stored in Keychain');
  } catch (error) {
    safeError('[MAIN] ❌ Error storing tokens:', error);
  }
}

async function getAuthTokens() {
  try {
    const tokens = await keytar.getPassword('JarvusApp', 'auth_tokens');
    return tokens ? JSON.parse(tokens) : null;
  } catch (error) {
    safeError('[MAIN] ❌ Error getting tokens:', error);
    return null;
  }
}

async function clearAuthTokens() {
  try {
    await keytar.deletePassword('JarvusApp', 'auth_tokens');
    safeLog('[MAIN] ✅ Tokens cleared from Keychain');
  } catch (error) {
    safeError('[MAIN] ❌ Error clearing tokens:', error);
  }
}

ipcMain.handle('store-auth-tokens', async (event, tokens) => {
  safeLog('[MAIN] IPC: store-auth-tokens called');
  await storeAuthTokens(tokens);
});

ipcMain.handle('get-auth-tokens', async () => {
  safeLog('[MAIN] IPC: get-auth-tokens called');
  return await getAuthTokens();
});

ipcMain.handle('clear-auth-tokens', async () => {
  safeLog('[MAIN] IPC: clear-auth-tokens called');
  await clearAuthTokens();
});

// Quit app handler
ipcMain.handle('quit-app', () => {
  safeLog('[MAIN] IPC: quit-app called - quitting app');
  app.exit(0);
});

// Browser management IPC handlers
ipcMain.handle('launch-browser', async () => {
  safeLog('[MAIN] IPC: launch-browser called');
  
  try {
    // Create new Chrome launcher instance
    chromeLauncher = new ChromeLauncher();
    
    // Launch Chrome with Profile 6
    const result = await chromeLauncher.launchChrome();
    
    if (result.success) {
      safeLog('[MAIN] ✅ Chrome browser launched successfully');
      safeLog(`[MAIN] WebSocket Endpoint: ${result.connectionInfo.wsEndpoint}`);
      safeLog(`[MAIN] Profile Path: ${result.connectionInfo.profilePath}`);
    } else {
      safeError('[MAIN] ❌ Failed to launch Chrome browser:', result.error);
    }
    
    return result;
    
  } catch (error) {
    safeError('[MAIN] Failed to launch browser:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('close-browser', async () => {
  safeLog('[MAIN] IPC: close-browser called');
  
  try {
    if (chromeLauncher) {
      const result = await chromeLauncher.closeBrowser();
      chromeLauncher = null;
      
      if (result.success) {
        safeLog('[MAIN] ✅ Chrome browser closed successfully');
      } else {
        safeError('[MAIN] ❌ Failed to close Chrome browser:', result.error);
      }
      
      return result;
    } else {
      safeLog('[MAIN] No Chrome launcher instance to close');
      return { success: false, message: 'No browser instance to close' };
    }
    
  } catch (error) {
    safeError('[MAIN] Failed to close browser:', error);
    return { success: false, error: error.message };
  }
});

// Profile management IPC handlers
ipcMain.handle('discover-chrome-profiles', async () => {
  safeLog('[MAIN] IPC: discover-chrome-profiles called');
  try {
    const profiles = profileManager.discoverAvailableProfiles();
    return { success: true, profiles };
  } catch (error) {
    safeError('[MAIN] Failed to discover Chrome profiles:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-default-chrome-profile', async () => {
  safeLog('[MAIN] IPC: get-default-chrome-profile called');
  try {
    const defaultProfile = profileManager.getDefaultProfile();
    if (defaultProfile) {
      const profiles = profileManager.discoverAvailableProfiles();
      const profileInfo = profiles[defaultProfile] || {};
      return { 
        success: true, 
        default_profile: defaultProfile,
        profile_info: profileInfo
      };
    } else {
      return { success: false, error: 'No default profile found' };
    }
  } catch (error) {
    safeError('[MAIN] Failed to get default Chrome profile:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('launch-browser-with-profile', async (event, profileName) => {
  safeLog(`[MAIN] IPC: launch-browser-with-profile called with profile: ${profileName}`);
  try {
    // Create new Chrome launcher instance
    chromeLauncher = new ChromeLauncher();
    
    // Launch Chrome with the specified profile (Profile 6 is hardcoded in launcher)
    const result = await chromeLauncher.launchChrome();
    
    if (result.success) {
      safeLog('[MAIN] ✅ Chrome browser launched successfully with profile');
      safeLog(`[MAIN] WebSocket Endpoint: ${result.connectionInfo.wsEndpoint}`);
      safeLog(`[MAIN] Profile Path: ${result.connectionInfo.profilePath}`);
    } else {
      safeError('[MAIN] ❌ Failed to launch Chrome browser with profile:', result.error);
    }
    
    return result;
    
  } catch (error) {
    safeError('[MAIN] Failed to launch browser with profile:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-chrome-profile-info', async (event, profileName) => {
  safeLog(`[MAIN] IPC: get-chrome-profile-info called for profile: ${profileName}`);
  try {
    const profiles = profileManager.discoverAvailableProfiles();
    if (profileName in profiles) {
      return { success: true, profile_info: profiles[profileName] };
    } else {
      return { success: false, error: `Profile '${profileName}' not found` };
    }
  } catch (error) {
    safeError('[MAIN] Failed to get Chrome profile info:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-decrypted-profile-path', async () => {
  safeLog('[MAIN] IPC: get-decrypted-profile-path called');
  try {
    const profilePath = profileManager.getDecryptedProfilePath();
    if (profilePath) {
      return { success: true, profile_path: profilePath };
    } else {
      return { success: false, error: 'No decrypted profile path available' };
    }
  } catch (error) {
    safeError('[MAIN] Failed to get decrypted profile path:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('sync-profile-data', async () => {
  safeLog('[MAIN] IPC: sync-profile-data called');
  try {
    const success = profileManager.syncProfileData();
    return { success, message: success ? 'Profile data synced successfully' : 'Failed to sync profile data' };
  } catch (error) {
    safeError('[MAIN] Failed to sync profile data:', error);
    return { success: false, error: error.message };
  }
});

// Clipboard management IPC handler
ipcMain.handle('copy-to-clipboard', async (event, text) => {
  try {
    clipboard.writeText(text);
    safeLog('[MAIN] ✅ Text copied to clipboard');
    return { success: true };
  } catch (error) {
    safeError('[MAIN] ❌ Error copying to clipboard:', error);
    return { success: false, error: error.message };
  }
}); 