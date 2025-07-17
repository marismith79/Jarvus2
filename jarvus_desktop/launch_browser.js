const { spawn } = require('child_process');
const { chromium } = require('playwright');
const SecureProfileManager = require('./profile-manager');
const path = require('path');
const fs = require('fs');
const net = require('net');
const http = require('http');
const os = require('os');

class ChromeLauncher {
    constructor() {
        this.profileManager = new SecureProfileManager();
        this.browser = null;
        this.chromeProcess = null;
        this.isConnected = false;
        this.connectionInfo = null;
        this.debugPort = 9222; // Default CDP port
    }

    async launchChrome(selectedProfile = null, preserveSessions = true) {
        try {
            console.log('🚀 Starting Chrome browser launch process...');
            
            // Step 1: Check if debug Chrome is already running
            const isRunning = await this.checkIfChromeRunning();
            if (isRunning) {
                console.log('🔗 Found existing debug Chrome, connecting...');
                return await this.connectToExistingChrome();
            }
            
            // Step 2: Shutdown non-debugger Chrome instances to free up profiles
            console.log('🔄 Shutting down non-debugger Chrome instances...');
            await this.shutdownNonDebuggerChrome();
            await this.waitForChromeShutdown();
            
            // Step 3: Get Chrome executable path
            const chromePath = this.getChromeExecutablePath();
            console.log(`🔧 Chrome executable path: ${chromePath}`);
            
            // Check if Chrome executable exists
            if (!fs.existsSync(chromePath)) {
                throw new Error(`Chrome executable not found at: ${chromePath}`);
            }
            console.log('✅ Chrome executable found');
            
            // Step 4: Get the selected profile path
            if (!selectedProfile) {
                // Get the best available profile dynamically
                selectedProfile = this.profileManager.getBestAvailableProfile();
                if (!selectedProfile) {
                    throw new Error('No available Chrome profiles found. Please ensure Chrome is installed and has at least one profile.');
                }
            }
            
            const originalProfilePath = this.profileManager.getChromeProfilePath(selectedProfile);
            if (!originalProfilePath) {
                throw new Error(`Profile '${selectedProfile}' not found`);
            }
            console.log(`📁 Using profile: ${selectedProfile} (${originalProfilePath})`);
            
            // Use Chrome's native profile system instead of --user-data-dir
            console.log('📁 Using Chrome native profile system...');
            
            // Get the profile directory name (e.g., "Profile 5")
            const profileDirName = path.basename(originalProfilePath);
            console.log(`📁 Profile directory name: ${profileDirName}`);
            
            // Only create a temporary session backup if session preservation is enabled
            let sessionBackupPath = null;
            if (preserveSessions) {
                console.log('📋 Creating session backup for restoration...');
                sessionBackupPath = path.join(os.tmpdir(), `jarvus_session_${Date.now()}`);
                if (!fs.existsSync(sessionBackupPath)) {
                    fs.mkdirSync(sessionBackupPath, { recursive: true });
                }
                // Copy only session-related files for backup
                this.copySessionFiles(originalProfilePath, sessionBackupPath);
                console.log(`📁 Session backup path: ${sessionBackupPath}`);
            }
            
            // Step 5: Find an available debug port
            this.debugPort = await this.findAvailablePort(9222, 9230);
            console.log(`🔧 Using debug port: ${this.debugPort}`);
            
            // Step 6: Launch Chrome as child process with native profile
            console.log('🌐 Launching Chrome browser with native profile...');
            
            const chromeArgs = [
                `--remote-debugging-port=${this.debugPort}`,
                `--remote-debugging-address=127.0.0.1`,
                '--no-first-run',
                '--no-default-browser-check',
                '--password-store=basic'
            ];
            
            console.log(`🔧 Chrome launch arguments: ${chromeArgs.length} args`);
            
            // Launch Chrome process
            this.chromeProcess = spawn(chromePath, chromeArgs, {
                stdio: ['ignore', 'pipe', 'pipe'],
                detached: true
            });
            
            console.log(`🔗 Chrome process started with PID: ${this.chromeProcess.pid}`);
            
            // Set up process event handlers
            this.setupProcessEventHandlers();
            
            // Step 7: Wait for Chrome to start and CDP to be available
            console.log('⏳ Waiting for Chrome to start and CDP to be available...');
            await this.waitForCDP();
            
            // Step 8: Get the actual WebSocket endpoint from Chrome
            console.log('🔗 Getting WebSocket endpoint from Chrome...');
            const wsEndpoint = await this.getWebSocketEndpoint();
            console.log(`🔗 WebSocket endpoint: ${wsEndpoint}`);
            
            // Step 9: Connect to Chrome via CDP using chromium.connectOverCDP()
            console.log('🔗 Connecting to Chrome via CDP...');
            this.browser = await chromium.connectOverCDP(wsEndpoint);
            console.log('✅ Connected to Chrome via CDP successfully');
            
            // Step 10: Store connection information
            this.connectionInfo = {
                wsEndpoint: wsEndpoint,
                browserType: 'chrome',
                profilePath: originalProfilePath,
                sessionBackupPath: sessionBackupPath,
                selectedProfile: selectedProfile,
                preserveSessions: preserveSessions,
                launchTime: new Date().toISOString(),
                processId: this.chromeProcess.pid,
                debugPort: this.debugPort
            };
            
            console.log('✅ Chrome browser launched successfully!');
            console.log(`🔗 WebSocket Endpoint: ${this.connectionInfo.wsEndpoint}`);
            
            // Step 11: Set up browser event handlers
            this.setupBrowserEventHandlers();
            
            this.isConnected = true;
            console.log('✅ Browser connection established');
            
            // Step 12: Save connection info to file for Python to read
            console.log('💾 Saving connection info...');
            this.saveConnectionInfo();
            
            return {
                success: true,
                connectionInfo: this.connectionInfo,
                message: 'Chrome browser launched successfully with profile'
            };
            
        } catch (error) {
            console.error('❌ Failed to launch Chrome browser:', error);
            console.error('❌ Error stack:', error.stack);
            
            // Clean up on error
            await this.cleanup();
            
            return {
                success: false,
                error: error.message,
                message: 'Failed to launch Chrome browser'
            };
        }
    }
    
    async getWebSocketEndpoint() {
        // Get the actual WebSocket endpoint from Chrome's CDP
        return new Promise((resolve, reject) => {
            const req = http.get(`http://127.0.0.1:${this.debugPort}/json/version`, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    try {
                        const response = JSON.parse(data);
                        if (response.webSocketDebuggerUrl) {
                            resolve(response.webSocketDebuggerUrl);
                        } else {
                            reject(new Error('No WebSocket debugger URL found in Chrome response'));
                        }
                    } catch (error) {
                        reject(new Error(`Failed to parse Chrome response: ${error.message}`));
                    }
                });
            });
            
            req.on('error', (error) => {
                reject(new Error(`Failed to get WebSocket endpoint: ${error.message}`));
            });
            
            req.setTimeout(5000, () => {
                req.destroy();
                reject(new Error('Timeout getting WebSocket endpoint'));
            });
        });
    }
    
    async findAvailablePort(startPort, endPort) {
        for (let port = startPort; port <= endPort; port++) {
            try {
                await this.testPort(port);
                return port;
            } catch (error) {
                // Port is in use, try next one
                continue;
            }
        }
        throw new Error(`No available ports found between ${startPort} and ${endPort}`);
    }
    
    testPort(port) {
        return new Promise((resolve, reject) => {
            const server = net.createServer();
            server.listen(port, '127.0.0.1', () => {
                server.once('close', () => resolve(port));
                server.close();
            });
            server.on('error', reject);
        });
    }
    
    async waitForCDP(timeout = 20000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            try {
                // Try to connect to CDP endpoint
                const isAvailable = await this.testCDPEndpoint();
                if (isAvailable) {
                    console.log('✅ CDP endpoint is available');
                    return;
                }
            } catch (error) {
                // CDP not ready yet, wait a bit
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }
        
        throw new Error(`CDP endpoint not available after ${timeout}ms`);
    }
    
    testCDPEndpoint() {
        return new Promise((resolve) => {
            const req = http.get(`http://127.0.0.1:${this.debugPort}/json/version`, (res) => {
                if (res.statusCode === 200) {
                    resolve(true);
                } else {
                    resolve(false);
                }
            });
            
            req.on('error', () => {
                resolve(false);
            });
            
            req.setTimeout(1000, () => {
                req.destroy();
                resolve(false);
            });
        });
    }
    
    async checkIfChromeRunning() {
        // Check common CDP ports
        const ports = [9222, 9223, 9224, 9225, 9226, 9227, 9228, 9229, 9230];
        
        for (const port of ports) {
            try {
                const isAvailable = await this.testCDPEndpointOnPort(port);
                if (isAvailable) {
                    this.debugPort = port;
                    console.log(`✅ Found Chrome running on port ${port}`);
                    return true;
                }
            } catch (error) {
                // Continue to next port
            }
        }
        
        return false;
    }
    
    testCDPEndpointOnPort(port) {
        return new Promise((resolve) => {
            const req = http.get(`http://127.0.0.1:${port}/json/version`, (res) => {
                if (res.statusCode === 200) {
                    resolve(true);
                } else {
                    resolve(false);
                }
            });
            
            req.on('error', () => {
                resolve(false);
            });
            
            req.setTimeout(1000, () => {
                req.destroy();
                resolve(false);
            });
        });
    }
    
    async connectToExistingChrome() {
        try {
            console.log(`🔗 Connecting to existing Chrome on port ${this.debugPort}...`);
            const wsEndpoint = await this.getWebSocketEndpoint();
            
            this.browser = await chromium.connectOverCDP(wsEndpoint);
            console.log('✅ Connected to existing Chrome successfully');
            
            // Try to detect the profile being used by the existing Chrome instance
            let detectedProfile = null;
            let detectedProfilePath = null;
            
            try {
                // Get Chrome version info which might contain profile info
                const versionInfo = await new Promise((resolve, reject) => {
                    http.get(`http://127.0.0.1:${this.debugPort}/json/version`, (res) => {
                        let data = '';
                        res.on('data', chunk => data += chunk);
                        res.on('end', () => {
                            try {
                                resolve(JSON.parse(data));
                            } catch (err) {
                                reject(err);
                            }
                        });
                    }).on('error', reject);
                });
                
                // Try to find the profile from the user data directory
                // This is a best-effort approach since Chrome doesn't expose this directly
                const allProfiles = this.profileManager.discoverAvailableProfiles();
                for (const [profileName, profileInfo] of Object.entries(allProfiles)) {
                    if (profileInfo.path && fs.existsSync(profileInfo.path)) {
                        // Check if this profile is currently in use by looking for lock files
                        const lockFile = path.join(profileInfo.path, 'lockfile');
                        if (fs.existsSync(lockFile)) {
                            detectedProfile = profileName;
                            detectedProfilePath = profileInfo.path;
                            break;
                        }
                    }
                }
                
                // If no profile detected, use the first available one
                if (!detectedProfile) {
                    detectedProfile = this.profileManager.getBestAvailableProfile();
                    if (detectedProfile) {
                        detectedProfilePath = this.profileManager.getChromeProfilePath(detectedProfile);
                    }
                }
                
            } catch (error) {
                console.warn('Could not detect profile for existing Chrome:', error.message);
            }
            
            // Store connection information
            this.connectionInfo = {
                wsEndpoint: wsEndpoint,
                browserType: 'chrome',
                profilePath: detectedProfilePath || 'EXISTING_CHROME',
                selectedProfile: detectedProfile || 'UNKNOWN',
                preserveSessions: true,
                launchTime: new Date().toISOString(),
                processId: 'EXISTING',
                debugPort: this.debugPort
            };
            
            console.log('✅ Connected to existing Chrome browser!');
            console.log(`🔗 WebSocket Endpoint: ${this.connectionInfo.wsEndpoint}`);
            console.log(`📁 Detected Profile: ${detectedProfile || 'Unknown'}`);
            
            // Set up browser event handlers
            console.log('🔧 Setting up browser event handlers...');
            this.setupBrowserEventHandlers();
            
            this.isConnected = true;
            console.log('✅ Browser connection established');
            
            // Save connection info to file for Python to read
            console.log('💾 Saving connection info...');
            this.saveConnectionInfo();
            
            // Restore session after connection
            await this.restoreSession();
            
            return {
                success: true,
                connectionInfo: this.connectionInfo,
                message: 'Connected to existing Chrome browser with session restored'
            };
            
        } catch (error) {
            console.error('❌ Failed to connect to existing Chrome:', error);
            return {
                success: false,
                error: error.message,
                message: 'Failed to connect to existing Chrome browser'
            };
        }
    }
    
    setupProcessEventHandlers() {
        if (!this.chromeProcess) return;
        
        // Handle stdout
        this.chromeProcess.stdout.on('data', (data) => {
            const output = data.toString().trim();
            if (output) {
                console.log(`[CHROME] ${output}`);
            }
        });
        
        // Handle stderr
        this.chromeProcess.stderr.on('data', (data) => {
            const output = data.toString().trim();
            if (output && !output.includes('DevTools listening')) {
                console.error(`[CHROME ERROR] ${output}`);
            }
        });
        
        // Handle process exit
        this.chromeProcess.on('exit', (code, signal) => {
            console.log(`🔒 Chrome process exited with code ${code}, signal ${signal}`);
            
            // Don't clean up if the process was terminated by SIGINT/SIGTERM (Ctrl+C)
            // This allows the browser to persist when the Electron app is quit
            if (signal === 'SIGINT' || signal === 'SIGTERM') {
                console.log('🔄 Chrome process terminated by signal, keeping browser session alive');
                this.isConnected = false;
                return;
            }
            
            this.isConnected = false;
            this.cleanup();
        });
        
        // Handle process error
        this.chromeProcess.on('error', (error) => {
            console.error(`❌ Chrome process error: ${error.message}`);
            this.isConnected = false;
            this.cleanup();
        });
    }
    
    setupBrowserEventHandlers() {
        if (!this.browser) return;
        
        // Handle browser disconnection
        this.browser.on('disconnected', () => {
            console.log('🔌 Chrome browser disconnected');
            this.isConnected = false;
            this.cleanup();
        });
        
        // Handle browser close
        this.browser.on('close', () => {
            console.log('🔒 Chrome browser closed');
            this.isConnected = false;
            this.cleanup();
        });
    }
    
    saveConnectionInfo() {
        try {
            const connectionFile = path.join(__dirname, 'browser_connection.json');
            fs.writeFileSync(connectionFile, JSON.stringify(this.connectionInfo, null, 2));
            console.log(`💾 Connection info saved to: ${connectionFile}`);
        } catch (error) {
            console.error('❌ Failed to save connection info:', error);
        }
    }
    
    async closeBrowser() {
        try {
            console.log('🔄 Closing Chrome browser...');
            
            // Close Playwright browser connection
            if (this.browser) {
                await this.browser.close();
                this.browser = null;
            }
            
            // Kill Chrome process
            if (this.chromeProcess) {
                console.log(`🔄 Terminating Chrome process (PID: ${this.chromeProcess.pid})...`);
                this.chromeProcess.kill('SIGTERM');
                
                // Wait a bit for graceful shutdown
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Force kill if still running
                if (!this.chromeProcess.killed) {
                    console.log('🔄 Force killing Chrome process...');
                    this.chromeProcess.kill('SIGKILL');
                }
                
                this.chromeProcess = null;
            }
            
            this.isConnected = false;
            
            // Clean up connection file
            const connectionFile = path.join(__dirname, 'browser_connection.json');
            if (fs.existsSync(connectionFile)) {
                fs.unlinkSync(connectionFile);
                console.log('🗑️ Connection file cleaned up');
            }
            
            console.log('✅ Chrome browser closed successfully');
            return { success: true, message: 'Chrome browser closed successfully' };
            
        } catch (error) {
            console.error('❌ Failed to close Chrome browser:', error);
            return { success: false, error: error.message };
        }
    }
    
    getConnectionInfo() {
        return this.connectionInfo;
    }
    
    isBrowserConnected() {
        return this.isConnected && this.browser !== null;
    }
    
    async cleanup() {
        // Clean up connection file
        const connectionFile = path.join(__dirname, 'browser_connection.json');
        if (fs.existsSync(connectionFile)) {
            try {
                fs.unlinkSync(connectionFile);
                console.log('🗑️ Connection file cleaned up');
            } catch (error) {
                console.error('❌ Failed to clean up connection file:', error);
            }
        }
        
        // Clean up session backup files
        if (this.connectionInfo && this.connectionInfo.sessionBackupPath) {
            try {
                if (fs.existsSync(this.connectionInfo.sessionBackupPath)) {
                    fs.rmSync(this.connectionInfo.sessionBackupPath, { recursive: true, force: true });
                    console.log('🗑️ Session backup cleaned up');
                }
            } catch (error) {
                console.error('❌ Failed to clean up session backup:', error);
            }
        }
    }
    
    getChromeExecutablePath() {
        const platform = process.platform;
        
        if (platform === 'darwin') {
            // macOS
            return '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
        } else if (platform === 'win32') {
            // Windows
            return 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
        } else {
            // Linux
            return '/usr/bin/google-chrome';
        }
    }

    // Copy profile files (shallow copy, no encryption)
    copyProfileFiles(src, dest, preserveSessions = true) {
        // Files to always ignore (system files, locks, etc.)
        const alwaysIgnore = [
            "lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket", 
            "Crashpad", "Safe Browsing", "TransportSecurity", "Visited Links", 
            "Network Persistent State", "QuotaManager", "QuotaManager-journal", 
            "Service Worker", "Code Cache", "GrShaderCache", "GPUCache", 
            "DawnCache", "ShaderCache", "File System", "Extension State", 
            "IndexedDB", "Local Storage", "Session Storage", "Sync Data", 
            "WebStorage", "databases", "blob_storage", "pepper_flash", 
            "Platform Notifications", "Notification", "Storage", "Cache Storage", 
            "Cookies-journal", "Cookies", "Favicons", "History Provider Cache", 
            "Top Sites", "Web Data", "Login Data", "Login Data-journal", 
            "Network Action Predictor", "Shortcuts", "Bookmarks", 
            "Preferences", "Secure Preferences", "Affiliation Database", 
            "Affiliation Database-journal", "AutofillStrikeDatabase", 
            "AutofillStrikeDatabase-journal", "BudgetDatabase", 
            "BudgetDatabase-journal", "Contact Info", "Contact Info-journal", 
            "DownloadMetadata", "DownloadMetadata-journal", "Media History", 
            "Media History-journal", "Tab Groups", "Tab Groups-journal", 
            "Top Sites-journal", "Web Data-journal", "WebRTCEventLog", 
            "WebRTCEventLog-journal", "Visited Links-journal", 
            "Webstore Downloads", "Webstore Downloads-journal", 
            "Sync Extension Settings", "Sync Extension Settings-journal", 
            "Sync Preferences", "Sync Preferences-journal", 
            "Sync Secure Preferences", "Sync Secure Preferences-journal", 
            "Sync Web Data", "Sync Web Data-journal", 
            "Sync Webstore Downloads", "Sync Webstore Downloads-journal", 
            "Sync Webstore Extensions", "Sync Webstore Extensions-journal", 
            "Sync Webstore Preferences", "Sync Webstore Preferences-journal", 
            "Sync Webstore Secure Preferences", "Sync Webstore Secure Preferences-journal", 
            "Sync Webstore Web Data", "Sync Webstore Web Data-journal"
        ];
        
        // Session-related files to include when preserveSessions is true
        const sessionFiles = [
            "Sessions", "Sessions-journal", "Tabs", "Tabs-journal", 
            "TabRestoreService", "TabRestoreService-journal"
        ];
        
        // Build final ignore list
        const ignoreList = [...alwaysIgnore];
        if (!preserveSessions) {
            ignoreList.push(...sessionFiles);
        }
        
        console.log(`📋 Copying profile files (preserveSessions: ${preserveSessions})`);
        if (preserveSessions) {
            console.log(`📋 Including session files: ${sessionFiles.join(', ')}`);
        }
        
        if (!fs.existsSync(src)) return;
        
        // Copy files and directories at the root level only (no recursion)
        this.copyDirectoryContents(src, dest, ignoreList, false);
    }

    copyDirectoryContents(src, dest, ignoreList, isRecursive = false) {
        if (!fs.existsSync(src)) return;
        
        const items = fs.readdirSync(src);
        let copiedCount = 0;
        
        for (const item of items) {
            if (ignoreList.includes(item)) continue;
            
            const srcPath = path.join(src, item);
            const destPath = path.join(dest, item);
            const stat = fs.statSync(srcPath);
            
            if (stat.isDirectory()) {
                // Only copy directory structure, not contents (to avoid recursion)
                if (!isRecursive) {
                fs.mkdirSync(destPath, { recursive: true });
                    // Don't recursively copy directory contents to avoid excessive logging
                }
            } else if (stat.isFile()) {
                try {
                    fs.copyFileSync(srcPath, destPath);
                    copiedCount++;
                    if (isRecursive) {
                        console.log(`📋 Copied: ${item}`);
                    }
                } catch (error) {
                    console.warn(`⚠️ Failed to copy ${item}:`, error.message);
                }
            }
        }
        
        if (!isRecursive) {
            console.log(`📋 Copied ${copiedCount} files from profile`);
        }
    }

    copySessionFiles(src, dest) {
        // Only copy session-related files for backup/restoration
        const sessionFiles = [
            "Sessions", "Sessions-journal", "Tabs", "Tabs-journal", 
            "TabRestoreService", "TabRestoreService-journal"
        ];
        
        console.log(`📋 Copying session files: ${sessionFiles.join(', ')}`);
        
        if (!fs.existsSync(src)) return;
        
        const items = fs.readdirSync(src);
        let copiedCount = 0;
        
        for (const item of items) {
            if (!sessionFiles.includes(item)) continue;
            
            const srcPath = path.join(src, item);
            const destPath = path.join(dest, item);
            const stat = fs.statSync(srcPath);
            
            if (stat.isFile()) {
                try {
                fs.copyFileSync(srcPath, destPath);
                    copiedCount++;
                    console.log(`📋 Copied session file: ${item}`);
                } catch (error) {
                    console.warn(`⚠️ Failed to copy session file ${item}:`, error.message);
                }
            }
        }
        
        console.log(`📋 Copied ${copiedCount} session files`);
    }

    // Session management methods
    async getSessionInfo() {
        if (!this.browser || !this.isConnected) {
            console.warn('Browser not connected, cannot get session info');
            return null;
        }
        try {
            // Give the browser a moment to fully initialize
            await new Promise(resolve => setTimeout(resolve, 1000));
            let pages = [];
            let sessionInfo = { totalPages: 0, pages: [] };
            // Try Playwright's pages() first
            if (this.browser.pages && typeof this.browser.pages === 'function') {
                try {
                    pages = await this.browser.pages();
                } catch (e) {
                    pages = [];
                }
            }
            // Fallback: Use DevTools Protocol if no pages found
            if (!pages || pages.length === 0) {
                try {
                    const port = this.debugPort;
                    const jsonList = await new Promise((resolve, reject) => {
                        http.get(`http://127.0.0.1:${port}/json`, (res) => {
                            let data = '';
                            res.on('data', chunk => data += chunk);
                            res.on('end', () => {
                                try {
                                    resolve(JSON.parse(data));
                                } catch (err) {
                                    reject(err);
                                }
                            });
                        }).on('error', reject);
                    });
                    for (const tab of jsonList) {
                        if (tab.type === 'page' && tab.url && tab.url !== 'about:blank') {
                            sessionInfo.pages.push({ url: tab.url, title: tab.title || '' });
                        }
                    }
                    sessionInfo.totalPages = sessionInfo.pages.length;
                    console.log(`📊 [DTP] Session info: ${sessionInfo.totalPages} pages`);
                    return sessionInfo;
                } catch (err) {
                    console.warn('DevTools Protocol fallback failed:', err.message);
                }
            } else {
                for (const page of pages) {
                    try {
                        const url = page.url();
                        const title = await page.title();
                        sessionInfo.pages.push({ url, title });
                    } catch (error) {
                        console.warn('Could not get page info:', error.message);
                    }
                }
                sessionInfo.totalPages = pages.length;
                console.log(`📊 Session info: ${pages.length} pages`);
                return sessionInfo;
            }
            return sessionInfo;
        } catch (error) {
            console.error('Error getting session info:', error);
            return null;
        }
    }

    async restoreSession() {
        if (!this.browser || !this.isConnected) {
            console.warn('Browser not connected, cannot restore session');
            return false;
        }
        try {
            console.log('🔄 Restoring previous session...');
            await new Promise(resolve => setTimeout(resolve, 1000));
            let pages = [];
            // Try Playwright's pages() first
            if (this.browser.pages && typeof this.browser.pages === 'function') {
                try {
                    pages = await this.browser.pages();
                } catch (e) {
                    pages = [];
                }
            }
            // Fallback: Use DevTools Protocol if no pages found
            if (!pages || pages.length === 0) {
                try {
                    const port = this.debugPort;
                    const jsonList = await new Promise((resolve, reject) => {
                        http.get(`http://127.0.0.1:${port}/json`, (res) => {
                            let data = '';
                            res.on('data', chunk => data += chunk);
                            res.on('end', () => {
                                try {
                                    resolve(JSON.parse(data));
                                } catch (err) {
                                    reject(err);
                                }
                            });
                        }).on('error', reject);
                    });
                    const openTabs = jsonList.filter(tab => tab.type === 'page' && tab.url && tab.url !== 'about:blank');
                    if (openTabs.length === 0) {
                        // Open a new page if none exist
                        await this.browser.newPage();
                        console.log('✅ [DTP] Created new page for session');
                    } else {
                        console.log(`✅ [DTP] Session restored with ${openTabs.length} pages`);
                    }
                    return true;
                } catch (err) {
                    console.warn('DevTools Protocol fallback failed:', err.message);
                }
            } else {
                if (pages.length === 0) {
                    await this.browser.newPage();
                    console.log('✅ Created new page for session');
                } else {
                    console.log(`✅ Session restored with ${pages.length} pages`);
                }
                return true;
            }
            return false;
        } catch (error) {
            console.error('❌ Error restoring session:', error);
            return false;
        }
    }

    // Shutdown non-debugger Chrome instances
    async shutdownNonDebuggerChrome() {
        try {
            console.log('🔄 Checking for non-debugger Chrome instances...');
            
            const platform = process.platform;
            let command, args;
            
            if (platform === 'darwin') {
                // macOS - use ps to find Chrome processes and filter out debug ones
                command = 'ps';
                args = ['-eo', 'pid,command'];
            } else if (platform === 'win32') {
                // Windows - use tasklist
                command = 'tasklist';
                args = ['/FI', 'IMAGENAME eq chrome.exe', '/FO', 'CSV'];
            } else {
                // Linux - use ps
                command = 'ps';
                args = ['-eo', 'pid,command'];
            }
            
            return new Promise((resolve, reject) => {
                const process = spawn(command, args, { stdio: 'pipe' });
                let output = '';
                
                process.stdout.on('data', (data) => {
                    output += data.toString();
                });
                
                process.on('close', async (code) => {
                    if (code === 0) {
                        // Parse output to find Chrome processes
                        const lines = output.split('\n');
                        const chromePids = [];
                        
                        for (const line of lines) {
                            if (line.includes('Google Chrome') || line.includes('chrome.exe')) {
                                // Check if this Chrome process is NOT in debug mode
                                if (!line.includes('--remote-debugging-port')) {
                                    // Extract PID
                                    const pidMatch = line.match(/^\s*(\d+)/);
                                    if (pidMatch) {
                                        chromePids.push(pidMatch[1]);
                                    }
                                }
                            }
                        }
                        
                        if (chromePids.length > 0) {
                            console.log(`🔄 Found ${chromePids.length} non-debugger Chrome processes, shutting them down...`);
                            
                            // Kill each non-debugger Chrome process
                            for (const pid of chromePids) {
                                try {
                                    if (platform === 'darwin' || platform === 'linux') {
                                        spawn('kill', [pid], { stdio: 'ignore' });
                                    } else {
                                        spawn('taskkill', ['/PID', pid, '/F'], { stdio: 'ignore' });
                                    }
                                } catch (error) {
                                    console.warn(`⚠️ Failed to kill Chrome process ${pid}:`, error.message);
                                }
                            }
                            
                            console.log('✅ Non-debugger Chrome instances shut down');
                            resolve(true);
                        } else {
                            console.log('✅ No non-debugger Chrome instances found');
                            resolve(true);
                        }
                    } else {
                        console.warn(`⚠️ Process listing returned code ${code}`);
                        resolve(false);
                    }
                });
                
                process.on('error', (error) => {
                    console.warn('⚠️ Error listing processes:', error.message);
                    resolve(false);
                });
            });
            
        } catch (error) {
            console.error('❌ Error in shutdownNonDebuggerChrome:', error);
            return false;
        }
    }

    // Wait for Chrome processes to fully terminate
    async waitForChromeShutdown(timeout = 10000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            try {
                // Check if any Chrome processes are still running
                const platform = process.platform;
                let command, args;
                
                if (platform === 'darwin') {
                    command = 'pgrep';
                    args = ['-f', 'Google Chrome'];
                } else if (platform === 'win32') {
                    command = 'tasklist';
                    args = ['/FI', 'IMAGENAME eq chrome.exe'];
                } else {
                    command = 'pgrep';
                    args = ['-f', 'google-chrome'];
                }
                
                const result = await new Promise((resolve) => {
                    const process = spawn(command, args, { stdio: 'pipe' });
                    let output = '';
                    
                    process.stdout.on('data', (data) => {
                        output += data.toString();
                    });
                    
                    process.on('close', (code) => {
                        resolve({ code, output });
                    });
                });
                
                // If no Chrome processes found, we're done
                if (result.code !== 0 || result.output.trim() === '') {
                    console.log('✅ Chrome processes fully terminated');
                    return true;
                }
                
                // Wait a bit before checking again
                await new Promise(resolve => setTimeout(resolve, 500));
                
            } catch (error) {
                console.warn('⚠️ Error checking Chrome processes:', error.message);
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }
        
        console.warn('⚠️ Timeout waiting for Chrome shutdown');
        return false;
    }
}

// Export the launcher class
module.exports = ChromeLauncher;

// If this file is run directly, launch the browser
if (require.main === module) {
    const launcher = new ChromeLauncher();
    
    // Handle process termination
    // process.on('SIGINT', async () => {
    //     console.log('\n🛑 Received SIGINT, closing browser...');
    //     await launcher.closeBrowser();
    //     process.exit(0);
    // });
    
    // process.on('SIGTERM', async () => {
    //     console.log('\n🛑 Received SIGTERM, closing browser...');
    //     await launcher.closeBrowser();
    //     process.exit(0);
    // });
    
    // Launch the browser
    launcher.launchChrome()
        .then((result) => {
            if (result.success) {
                console.log('🎉 Browser launch completed successfully!');
                console.log('📊 Connection Info:', JSON.stringify(result.connectionInfo, null, 2));
            } else {
                console.error('💥 Browser launch failed:', result.error);
                process.exit(1);
            }
        })
        .catch((error) => {
            console.error('💥 Unexpected error during browser launch:', error);
            process.exit(1);
        });
} 