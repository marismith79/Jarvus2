const { app, BrowserWindow, ipcMain, screen, globalShortcut } = require('electron');
const path = require('path');
const Store = require('electron-store');
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
        partition: 'persist:main', // Share session with control bar
      },
    });
    
    loginWin.loadURL(signinUrl);
    
    // Monitor for successful login
    let hasLoggedIn = false;
    
    loginWin.webContents.on('did-navigate', (event, url) => {
      console.log('[MAIN] Login modal navigated to:', url);
      if (!hasLoggedIn && url.includes('/profile?just_logged_in=1')) {
        hasLoggedIn = true;
        console.log('[MAIN] Login successful, closing modal');
        loginWin.close();
        controlBarWindow.webContents.send('login-modal-closed');
      }
    });

    loginWin.webContents.on('did-finish-load', () => {
      const currentUrl = loginWin.webContents.getURL();
      console.log('[MAIN] Login modal finished loading:', currentUrl);
      if (!hasLoggedIn && currentUrl.includes('/profile?just_logged_in=1')) {
        hasLoggedIn = true;
        console.log('[MAIN] Login successful (did-finish-load), closing modal');
        loginWin.close();
        controlBarWindow.webContents.send('login-modal-closed');
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

function getUserProfilePath() {
  const platform = os.platform();
  const home = os.homedir();
  
  if (platform === 'darwin') {
    return path.join(home, 'Library', 'Application Support', 'Google', 'Chrome');
  } else if (platform === 'win32') {
    return path.join(home, 'AppData', 'Local', 'Google', 'Chrome', 'User Data');
  } else if (platform === 'linux') {
    return path.join(home, '.config', 'google-chrome');
  } else {
    throw new Error(`Unsupported platform: ${platform}`);
  }
}

function getDebugProfilePath() {
  const platform = os.platform();
  const home = os.homedir();
  
  if (platform === 'darwin') {
    return path.join(home, 'Desktop', 'Private Chrome Data Sync');
  } else if (platform === 'win32') {
    return path.join(home, 'Desktop', 'Private Chrome Data Sync');
  } else if (platform === 'linux') {
    return path.join(home, 'Desktop', 'Private Chrome Data Sync');
  } else {
    throw new Error(`Unsupported platform: ${platform}`);
  }
}

function copyProfileData(sourceProfile, targetProfile) {
  try {
    // Remove existing debug profile directory if it exists
    if (fs.existsSync(targetProfile)) {
      console.log('[MAIN] Removing existing debug profile...');
      fs.rmSync(targetProfile, { recursive: true, force: true });
    }
    
    // Create fresh target directory
    fs.mkdirSync(targetProfile, { recursive: true });
    
    console.log('[MAIN] Starting profile data copy...');
    
    // Copy all profile folders (Default, Profile 1, Profile 2, etc.)
    const items = fs.readdirSync(sourceProfile);
    
    for (const item of items) {
      const sourcePath = path.join(sourceProfile, item);
      const targetPath = path.join(targetProfile, item);
      
      // Skip certain files/folders that shouldn't be copied
      if (['Crashpad', 'Crash Reports', 'Network', 'Network Persistent State', 'Service Worker'].includes(item)) {
        continue;
      }
      
      const stats = fs.statSync(sourcePath);
      
      if (stats.isDirectory()) {
        // Copy entire profile directories
        if (!fs.existsSync(targetPath)) {
          fs.mkdirSync(targetPath, { recursive: true });
        }
        
        // Copy all files in the profile directory
        const profileFiles = fs.readdirSync(sourcePath);
        for (const file of profileFiles) {
          const sourceFile = path.join(sourcePath, file);
          const targetFile = path.join(targetPath, file);
          
          try {
            fs.copyFileSync(sourceFile, targetFile);
            console.log(`[MAIN] Copied ${item}/${file}`);
          } catch (copyError) {
            console.log(`[MAIN] Skipped ${item}/${file} (may be locked)`);
          }
        }
      } else {
        // Copy root level files
        try {
          fs.copyFileSync(sourcePath, targetPath);
          console.log(`[MAIN] Copied ${item}`);
        } catch (copyError) {
          console.log(`[MAIN] Skipped ${item} (may be locked)`);
        }
      }
    }
    
    console.log('[MAIN] Profile data copied successfully');
    console.log(`[MAIN] Debug profile location: ${targetProfile}`);
    
  } catch (error) {
    console.error('[MAIN] Error copying profile data:', error);
  }
}

function launchChromeWithDebugging() {
  try {
    const chromePath = getChromePath();
    const userProfile = getUserProfilePath();
    const debugProfile = getDebugProfilePath();
    const debugPort = 9222;
    
    console.log('[MAIN] Launching Chrome with remote debugging...');
    console.log(`[MAIN] Chrome path: ${chromePath}`);
    console.log(`[MAIN] Debug port: ${debugPort}`);
    console.log(`[MAIN] User profile: ${userProfile}`);
    console.log(`[MAIN] Debug profile: ${debugProfile}`);
    
    // Copy profile data to debug profile
    copyProfileData(userProfile, debugProfile);
    
    const chromeArgs = [
      `--remote-debugging-port=${debugPort}`,
      `--user-data-dir=${debugProfile}`,
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-background-timer-throttling',
      '--disable-backgrounding-occluded-windows',
      '--disable-renderer-backgrounding',
      '--disable-features=TranslateUI',
      '--disable-ipc-flooding-protection',
      '--new-window',
      '--force-new-window',
      '--disable-session-crashed-bubble',
      '--disable-infobars',
      '--disable-web-security',
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
    
    chromeProcess = spawn(chromePath, chromeArgs, {
      stdio: 'pipe',
      detached: false
    });
    
    chromeProcess.stdout.on('data', (data) => {
      console.log(`[CHROME] ${data.toString().trim()}`);
    });
    
    chromeProcess.stderr.on('data', (data) => {
      console.log(`[CHROME ERROR] ${data.toString().trim()}`);
    });
    
    chromeProcess.on('close', (code) => {
      console.log(`[MAIN] Chrome process exited with code ${code}`);
      chromeProcess = null;
    });
    
    chromeProcess.on('error', (error) => {
      console.error('[MAIN] Failed to start Chrome:', error);
      chromeProcess = null;
    });
    
    console.log(`[MAIN] Chrome launched with PID: ${chromeProcess.pid}`);
    console.log(`[MAIN] DevTools Protocol available at: http://localhost:${debugPort}`);
    
  } catch (error) {
    console.error('[MAIN] Error launching Chrome:', error);
  }
}

// App event handlers
app.whenReady().then(() => {
  createControlBarWindow();
  console.log('[MAIN] App ready, control bar window created');
  
  // Launch Chrome with remote debugging
  launchChromeWithDebugging();

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

// Clean up Chrome process when app quits
app.on('will-quit', () => {
  if (chromeProcess) {
    console.log('[MAIN] Terminating Chrome process...');
    chromeProcess.kill();
  }
  
  // Clean up debug profile
  try {
    const debugProfile = getDebugProfilePath();
    if (fs.existsSync(debugProfile)) {
      console.log('[MAIN] Cleaning up debug profile...');
      fs.rmSync(debugProfile, { recursive: true, force: true });
      console.log('[MAIN] Debug profile cleaned up');
    }
  } catch (error) {
    console.error('[MAIN] Error cleaning up debug profile:', error);
  }
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