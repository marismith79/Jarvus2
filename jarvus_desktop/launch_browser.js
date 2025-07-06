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

    async launchChrome() {
        try {
            console.log('🚀 Starting Chrome browser launch process...');
            
            // Step 1: Get Chrome executable path
            const chromePath = this.getChromeExecutablePath();
            console.log(`🔧 Chrome executable path: ${chromePath}`);
            
            // Check if Chrome executable exists
            if (!fs.existsSync(chromePath)) {
                throw new Error(`Chrome executable not found at: ${chromePath}`);
            }
            console.log('✅ Chrome executable found');
            
            // Step 2: Get the original Chrome profile path directly
            console.log('👤 Getting Chrome profile path...');
            const originalProfilePath = this.profileManager.getChromeProfilePath();
            if (!originalProfilePath) {
                throw new Error('Failed to get Chrome profile path');
            }
            console.log(`📁 Original Chrome profile path: ${originalProfilePath}`);
            
            // Create a temporary copy of the profile for this session
            console.log('📋 Creating temporary profile copy...');
            const tempProfilePath = path.join(os.tmpdir(), `jarvus_chrome_${Date.now()}`);
            if (!fs.existsSync(tempProfilePath)) {
                fs.mkdirSync(tempProfilePath, { recursive: true });
            }
            
            // Copy essential profile files (without encryption)
            console.log('📋 Copying profile files...');
            this.copyProfileFiles(originalProfilePath, tempProfilePath);
            console.log(`📁 Temporary profile path: ${tempProfilePath}`);
            
            // Step 3: Find an available debug port
            this.debugPort = await this.findAvailablePort(9222, 9230);
            console.log(`🔧 Using debug port: ${this.debugPort}`);
            
            // Step 4: Launch Chrome as child process with secure profile
            console.log('🌐 Launching Chrome browser with secure profile...');
            
            const chromeArgs = [
                `--user-data-dir=${tempProfilePath}`,
                `--remote-debugging-port=${this.debugPort}`,
                `--remote-debugging-address=127.0.0.1`,
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-features=VizDisplayCompositor',
                '--enable-automation',
                '--password-store=basic',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-process-singleton',
                '--disable-background-networking',
                '--disable-component-extensions-with-background-pages',
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-sync',
                '--disable-translate',
                '--hide-scrollbars',
                '--mute-audio',
                '--disable-plugins-discovery',
                '--disable-plugins'
            ];
            
            console.log('🔧 Chrome launch arguments:');
            chromeArgs.forEach(arg => console.log(`   ${arg}`));
            
            // Launch Chrome process
            this.chromeProcess = spawn(chromePath, chromeArgs, {
                stdio: ['ignore', 'pipe', 'pipe'],
                detached: false
            });
            
            console.log(`🔗 Chrome process started with PID: ${this.chromeProcess.pid}`);
            
            // Set up process event handlers
            this.setupProcessEventHandlers();
            
            // Step 5: Wait for Chrome to start and CDP to be available
            console.log('⏳ Waiting for Chrome to start and CDP to be available...');
            await this.waitForCDP();
            
            // Step 6: Get the actual WebSocket endpoint from Chrome
            console.log('🔗 Getting WebSocket endpoint from Chrome...');
            const wsEndpoint = await this.getWebSocketEndpoint();
            console.log(`🔗 WebSocket endpoint: ${wsEndpoint}`);
            
            // Step 7: Connect to Chrome via CDP using chromium.connectOverCDP()
            console.log('🔗 Connecting to Chrome via CDP...');
            this.browser = await chromium.connectOverCDP(wsEndpoint);
            console.log('✅ Connected to Chrome via CDP successfully');
            
            // Step 8: Store connection information
            this.connectionInfo = {
                wsEndpoint: wsEndpoint,
                browserType: 'chrome',
                profilePath: tempProfilePath,
                originalProfilePath: originalProfilePath,
                launchTime: new Date().toISOString(),
                processId: this.chromeProcess.pid,
                debugPort: this.debugPort
            };
            
            console.log('✅ Chrome browser launched successfully!');
            console.log(`🔗 WebSocket Endpoint: ${this.connectionInfo.wsEndpoint}`);
            console.log(`📁 Temporary Profile Path: ${this.connectionInfo.profilePath}`);
            console.log(`📁 Original Profile Path: ${this.connectionInfo.originalProfilePath}`);
            console.log(`🔗 Process ID: ${this.connectionInfo.processId}`);
            
            // Step 9: Set up browser event handlers
            console.log('🔧 Setting up browser event handlers...');
            this.setupBrowserEventHandlers();
            
            this.isConnected = true;
            console.log('✅ Browser connection established');
            
            // Step 10: Save connection info to file for Python to read
            console.log('💾 Saving connection info...');
            this.saveConnectionInfo();
            
            // Step 11: Test page creation
            console.log('🧪 Testing page creation...');
            try {
                const contexts = this.browser.contexts();
                let context = contexts[0];
                
                if (!context) {
                    console.log('📄 Creating new browser context...');
                    context = await this.browser.newContext();
                }
                
                const page = await context.newPage();
                console.log('✅ New page created successfully');
                
                console.log('🧪 Navigating to test page...');
                await page.goto('https://example.com');
                console.log('✅ Test page loaded successfully');
                
                // Get page title to confirm it loaded
                const title = await page.title();
                console.log(`📄 Page title: "${title}"`);
                
                // Check if page is visible
                const isVisible = await page.isVisible('body');
                console.log(`👁️ Page visible: ${isVisible}`);
                
            } catch (pageError) {
                console.error('❌ Error creating or navigating page:', pageError.message);
                throw pageError;
            }
            
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
            
            // Store connection information
            this.connectionInfo = {
                wsEndpoint: wsEndpoint,
                browserType: 'chrome',
                profilePath: 'EXISTING_CHROME',
                launchTime: new Date().toISOString(),
                processId: 'EXISTING',
                debugPort: this.debugPort
            };
            
            console.log('✅ Connected to existing Chrome browser!');
            console.log(`🔗 WebSocket Endpoint: ${this.connectionInfo.wsEndpoint}`);
            console.log(`📁 Profile Path: ${this.connectionInfo.profilePath}`);
            
            // Set up browser event handlers
            console.log('🔧 Setting up browser event handlers...');
            this.setupBrowserEventHandlers();
            
            this.isConnected = true;
            console.log('✅ Browser connection established');
            
            // Save connection info to file for Python to read
            console.log('💾 Saving connection info...');
            this.saveConnectionInfo();
            
            // Test page creation
            console.log('🧪 Testing page creation...');
            try {
                const page = this.browser.pages()[0] || await this.browser.newPage();
                console.log('✅ Page available successfully');
                
                console.log('🧪 Navigating to test page...');
                await page.goto('https://example.com');
                console.log('✅ Test page loaded successfully');
                
                // Get page title to confirm it loaded
                const title = await page.title();
                console.log(`📄 Page title: "${title}"`);
                
                // Check if page is visible
                const isVisible = await page.isVisible('body');
                console.log(`👁️ Page visible: ${isVisible}`);
                
            } catch (pageError) {
                console.error('❌ Error creating or navigating page:', pageError.message);
                throw pageError;
            }
            
            return {
                success: true,
                connectionInfo: this.connectionInfo,
                message: 'Connected to existing Chrome browser successfully'
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
    copyProfileFiles(src, dest) {
        const ignore = ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket", "Crashpad", "Safe Browsing", "TransportSecurity", "Visited Links", "Network Persistent State", "QuotaManager", "QuotaManager-journal", "Service Worker", "Code Cache", "GrShaderCache", "GPUCache", "DawnCache", "ShaderCache", "File System", "Extension State", "IndexedDB", "Local Storage", "Session Storage", "Sessions", "Sync Data", "WebStorage", "databases", "blob_storage", "pepper_flash", "Platform Notifications", "Notification", "Storage", "Cache Storage", "Cookies-journal", "Cookies", "Favicons", "History Provider Cache", "Top Sites", "Web Data", "Login Data", "Login Data-journal", "Network Action Predictor", "Shortcuts", "Bookmarks", "Preferences", "Secure Preferences", "Affiliation Database", "Affiliation Database-journal", "AutofillStrikeDatabase", "AutofillStrikeDatabase-journal", "BudgetDatabase", "BudgetDatabase-journal", "Contact Info", "Contact Info-journal", "DownloadMetadata", "DownloadMetadata-journal", "Media History", "Media History-journal", "Tab Groups", "Tab Groups-journal", "TabRestoreService", "TabRestoreService-journal", "Tabs", "Tabs-journal", "Top Sites-journal", "Web Data-journal", "WebRTCEventLog", "WebRTCEventLog-journal", "Visited Links-journal", "Webstore Downloads", "Webstore Downloads-journal", "Sync Extension Settings", "Sync Extension Settings-journal", "Sync Preferences", "Sync Preferences-journal", "Sync Secure Preferences", "Sync Secure Preferences-journal", "Sync Web Data", "Sync Web Data-journal", "Sync Webstore Downloads", "Sync Webstore Downloads-journal", "Sync Webstore Extensions", "Sync Webstore Extensions-journal", "Sync Webstore Preferences", "Sync Webstore Preferences-journal", "Sync Webstore Secure Preferences", "Sync Webstore Secure Preferences-journal", "Sync Webstore Web Data", "Sync Webstore Web Data-journal", "Sync Webstore Webstore Downloads", "Sync Webstore Webstore Downloads-journal", "Sync Webstore Webstore Extensions", "Sync Webstore Webstore Extensions-journal", "Sync Webstore Webstore Preferences", "Sync Webstore Webstore Preferences-journal", "Sync Webstore Webstore Secure Preferences", "Sync Webstore Webstore Secure Preferences-journal", "Sync Webstore Webstore Web Data", "Sync Webstore Webstore Web Data-journal", "Sync Webstore Webstore Webstore Downloads", "Sync Webstore Webstore Webstore Downloads-journal", "Sync Webstore Webstore Webstore Extensions", "Sync Webstore Webstore Webstore Extensions-journal", "Sync Webstore Webstore Webstore Preferences", "Sync Webstore Webstore Webstore Preferences-journal", "Sync Webstore Webstore Webstore Secure Preferences", "Sync Webstore Webstore Webstore Secure Preferences-journal", "Sync Webstore Webstore Webstore Web Data", "Sync Webstore Webstore Webstore Web Data-journal"];
        if (!fs.existsSync(src)) return;
        const items = fs.readdirSync(src);
        for (const item of items) {
            if (ignore.includes(item)) continue;
            const srcPath = path.join(src, item);
            const destPath = path.join(dest, item);
            const stat = fs.statSync(srcPath);
            if (stat.isDirectory()) {
                fs.mkdirSync(destPath, { recursive: true });
                this.copyProfileFiles(srcPath, destPath);
            } else if (stat.isFile()) {
                fs.copyFileSync(srcPath, destPath);
            }
        }
    }
}

// Export the launcher class
module.exports = ChromeLauncher;

// If this file is run directly, launch the browser
if (require.main === module) {
    const launcher = new ChromeLauncher();
    
    // Handle process termination
    process.on('SIGINT', async () => {
        console.log('\n🛑 Received SIGINT, closing browser...');
        await launcher.closeBrowser();
        process.exit(0);
    });
    
    process.on('SIGTERM', async () => {
        console.log('\n🛑 Received SIGTERM, closing browser...');
        await launcher.closeBrowser();
        process.exit(0);
    });
    
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