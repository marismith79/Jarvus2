const express = require('express');
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

class BrowserAPI {
    constructor() {
        this.app = express();
        this.browser = null;
        this.context = null;
        this.pages = [];
        this.currentPage = null;
        this.isConnected = false;
        this.port = 3001; // Different from Flask server
        
        this.setupMiddleware();
        this.setupRoutes();
    }
    
    setupMiddleware() {
        this.app.use(express.json());
        this.app.use(express.urlencoded({ extended: true }));
        
        // CORS for web app
        this.app.use((req, res, next) => {
            res.header('Access-Control-Allow-Origin', 'http://localhost:5001');
            res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
            res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
            if (req.method === 'OPTIONS') {
                res.sendStatus(200);
            } else {
                next();
            }
        });
    }
    
    setupRoutes() {
        // Health check
        this.app.get('/api/browser/health', (req, res) => {
            res.json({ 
                success: true, 
                connected: this.isConnected,
                pages: this.pages.length,
                current_page: this.currentPage ? {
                    url: this.currentPage.url(),
                    title: this.currentPage.title()
                } : null,
                server_status: 'running'
            });
        });
        
        // Connect to browser
        this.app.post('/api/browser/connect', async (req, res) => {
            try {
                const result = await this.connectToBrowser();
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Navigate to URL
        this.app.post('/api/browser/navigate', async (req, res) => {
            try {
                const { url, new_tab = true } = req.body;
                const result = await this.navigateToUrl(url, new_tab);
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Click element
        this.app.post('/api/browser/click', async (req, res) => {
            try {
                const { selector, selector_type = 'css' } = req.body;
                const result = await this.clickElement(selector, selector_type);
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Type text
        this.app.post('/api/browser/type', async (req, res) => {
            try {
                const { selector, text, selector_type = 'css' } = req.body;
                const result = await this.typeText(selector, text, selector_type);
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Get page content
        this.app.get('/api/browser/content', async (req, res) => {
            try {
                const result = await this.getPageContent();
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Get tabs
        this.app.get('/api/browser/tabs', async (req, res) => {
            try {
                const result = await this.getTabs();
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Switch to tab
        this.app.post('/api/browser/switch-tab', async (req, res) => {
            try {
                const { tab_index } = req.body;
                const result = await this.switchToTab(tab_index);
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Close current tab
        this.app.post('/api/browser/close-tab', async (req, res) => {
            try {
                const result = await this.closeCurrentTab();
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Execute JavaScript
        this.app.post('/api/browser/execute-js', async (req, res) => {
            try {
                const { script } = req.body;
                const result = await this.executeJavaScript(script);
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Take screenshot
        this.app.post('/api/browser/screenshot', async (req, res) => {
            try {
                const { path: screenshotPath } = req.body;
                const result = await this.takeScreenshot(screenshotPath);
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Take automatic screenshot (base64 only)
        this.app.post('/api/browser/screenshot-auto', async (req, res) => {
            try {
                const result = await this.takeScreenshot();
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Get fonts
        this.app.get('/api/browser/fonts', async (req, res) => {
            try {
                const result = await this.getFonts();
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Fill form
        this.app.post('/api/browser/fill-form', async (req, res) => {
            try {
                const { form_data } = req.body;
                const result = await this.fillForm(form_data);
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Press key
        this.app.post('/api/browser/press-key', async (req, res) => {
            try {
                const { key } = req.body;
                const result = await this.pressKey(key);
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Get element info
        this.app.post('/api/browser/element-info', async (req, res) => {
            try {
                const { selector, selector_type = 'css' } = req.body;
                const result = await this.getElementInfo(selector, selector_type);
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Get all links
        this.app.get('/api/browser/links', async (req, res) => {
            try {
                const result = await this.getAllLinks();
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Get page metadata
        this.app.get('/api/browser/metadata', async (req, res) => {
            try {
                const result = await this.getPageMetadata();
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Scroll page
        this.app.post('/api/browser/scroll', async (req, res) => {
            try {
                const { direction, amount, selector } = req.body;
                const result = await this.scrollPage(direction, amount, selector);
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Highlight element
        this.app.post('/api/browser/highlight', async (req, res) => {
            try {
                const { selector, color, duration } = req.body;
                const result = await this.highlightElement(selector, color, duration);
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
        
        // Wait for page load
        this.app.post('/api/browser/wait-load', async (req, res) => {
            try {
                const { timeout } = req.body;
                const result = await this.waitForPageLoad(timeout);
                res.json(result);
            } catch (error) {
                res.json({ success: false, error: error.message });
            }
        });
    }
    
    async connectToBrowser() {
        try {
            if (this.isConnected && this.browser) {
                return { success: true, message: 'Already connected' };
            }
            
            // Read connection info from file
            const connectionFile = path.join(__dirname, 'browser_connection.json');
            if (!fs.existsSync(connectionFile)) {
                return { success: false, error: 'No browser connection info available' };
            }
            
            const connectionInfo = JSON.parse(fs.readFileSync(connectionFile, 'utf8'));
            
            // Connect to existing browser
            this.browser = await chromium.connectOverCDP(connectionInfo.wsEndpoint);
            
            // Wait for at least one context to appear (max 2 seconds)
            let retries = 20;
            while (
                this.browser.contexts &&
                typeof this.browser.contexts === 'function' &&
                this.browser.contexts().length === 0 &&
                retries-- > 0
            ) {
                await new Promise(res => setTimeout(res, 100));
            }
            let contextCount = 0;
            if (this.browser.contexts && typeof this.browser.contexts === 'function') {
                contextCount = this.browser.contexts().length;
            }
            console.log('DEBUG: Number of contexts after wait:', contextCount);
            if (this.browser.contexts && typeof this.browser.contexts === 'function') {
                this.browser.contexts().forEach((ctx, i) => {
                    let pageCount = ctx.pages && typeof ctx.pages === 'function' ? ctx.pages().length : 'unknown';
                    console.log(`DEBUG: Context ${i} has ${pageCount} pages`);
                    if (ctx.pages && typeof ctx.pages === 'function') {
                        ctx.pages().forEach((page, j) => {
                            try {
                                console.log(`DEBUG:   Page ${j}: ${page.url()}`);
                            } catch (e) {
                                console.log(`DEBUG:   Page ${j}: (error getting URL)`);
                            }
                        });
                    }
                });
            }
            
            // Get existing context and pages
            if (this.browser.contexts && typeof this.browser.contexts === 'function' && this.browser.contexts().length > 0) {
                this.context = this.browser.contexts()[0];
                this.pages = this.context.pages && typeof this.context.pages === 'function' ? this.context.pages() : [];
            } else {
                this.context = await this.browser.newContext();
                this.pages = [];
            }
            
            // If no pages exist, create an initial blank page (do not navigate to Google)
            if (this.pages.length === 0) {
                console.log('📄 Creating initial blank page...');
                this.currentPage = await this.context.newPage();
                this.pages.push(this.currentPage);
            } else {
                this.currentPage = this.pages[0];
            }
            
            this.isConnected = true;
            
            // Debug: Log all contexts and their pages after connecting
            if (this.browser.contexts && typeof this.browser.contexts === 'function') {
                console.log('DEBUG: Number of contexts:', this.browser.contexts().length);
                this.browser.contexts().forEach((ctx, i) => {
                    let pageCount = ctx.pages && typeof ctx.pages === 'function' ? ctx.pages().length : 'unknown';
                    console.log(`DEBUG: Context ${i} has ${pageCount} pages`);
                    if (ctx.pages && typeof ctx.pages === 'function') {
                        ctx.pages().forEach((page, j) => {
                            try {
                                console.log(`DEBUG:   Page ${j}: ${page.url()}`);
                            } catch (e) {
                                console.log(`DEBUG:   Page ${j}: (error getting URL)`);
                            }
                        });
                    }
                });
            }
            
            return { 
                success: true, 
                message: 'Connected to browser',
                pages: this.pages.length 
            };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async navigateToUrl(url, newTab = true) {
        try {
            if (!this.isConnected || !this.context) {
                const connectResult = await this.connectToBrowser();
                if (!connectResult.success) {
                    return connectResult;
                }
            }

            if (newTab) {
                // Open a new tab in the same window using window.open
                if (!this.currentPage) {
                    // If no current page, fallback to context.newPage()
                    this.currentPage = await this.context.newPage();
                    this.pages.push(this.currentPage);
                }
                const [newPage] = await Promise.all([
                    this.context.waitForEvent('page'),
                    this.currentPage.evaluate(() => window.open('about:blank', '_blank'))
                ]);
                this.currentPage = newPage;
                this.pages.push(newPage);
            } else {
                // Use existing page if available, otherwise create new one
                if (this.pages.length > 0) {
                    this.currentPage = this.pages[0];
                } else {
                    this.currentPage = await this.context.newPage();
                    this.pages.push(this.currentPage);
                }
            }

            const response = await this.currentPage.goto(url, { 
                waitUntil: 'commit', 
                timeout: 30000 
            });

            return { 
                success: true, 
                url: url,
                finalUrl: this.currentPage.url(),
                status: response ? response.status() : null
            };

        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Add a new method to get the currently active tab from the browser
    async getCurrentActiveTab() {
        try {
            if (!this.isConnected || !this.context) {
                return { success: false, error: 'Not connected to browser' };
            }
            
            // Get all pages from the context
            const allPages = this.context.pages();
            
            // Find the page that is currently active (has focus)
            for (const page of allPages) {
                try {
                    // Check if this page is currently active by trying to get its title
                    // The active page will respond quickly, inactive ones might be slower
                    const isActive = await page.evaluate(() => {
                        return document.hasFocus() || document.visibilityState === 'visible';
                    });
                    
                    if (isActive) {
                        // Update our tracking
                        this.currentPage = page;
                        
                        // Make sure it's in our pages array
                        if (!this.pages.includes(page)) {
                            this.pages.push(page);
                        }
                        
                        return { 
                            success: true, 
                            currentPage: {
                                url: page.url(),
                                title: await page.title()
                            }
                        };
                    }
                } catch (error) {
                    // Skip pages that might be closed or inaccessible
                    continue;
                }
            }
            
            // If no active page found, use the first available page
            if (allPages.length > 0) {
                this.currentPage = allPages[0];
                if (!this.pages.includes(this.currentPage)) {
                    this.pages.push(this.currentPage);
                }
                return { 
                    success: true, 
                    currentPage: {
                        url: this.currentPage.url(),
                        title: await this.currentPage.title()
                    }
                };
            }
            
            return { success: false, error: 'No active pages found' };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async clickElement(selector, selectorType = 'css') {
        try {
            if (!this.isConnected || !this.currentPage) {
                return { success: false, error: 'No active page' };
            }
            
            if (selectorType === 'xpath') {
                await this.currentPage.click(`xpath=${selector}`);
            } else {
                await this.currentPage.click(selector);
            }
            
            return { success: true, selector };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async typeText(selector, text, selectorType = 'css') {
        try {
            if (!this.isConnected || !this.currentPage) {
                return { success: false, error: 'No active page' };
            }
            
            if (selectorType === 'xpath') {
                await this.currentPage.fill(`xpath=${selector}`, text);
            } else {
                await this.currentPage.fill(selector, text);
            }
            
            return { success: true, selector, text };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async getPageContent() {
        try {
            if (!this.isConnected || !this.currentPage) {
                return { success: false, error: 'No active page' };
            }
            
            const content = await this.currentPage.content();
            const title = await this.currentPage.title();
            const url = this.currentPage.url;
            
            return {
                success: true,
                content,
                title,
                url
            };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async getTabs() {
        try {
            if (!this.isConnected) {
                return { success: false, error: 'Not connected to browser' };
            }
            
            const tabs = [];
            for (let i = 0; i < this.pages.length; i++) {
                const page = this.pages[i];
                const title = await page.title();
                const url = page.url;
                
                tabs.push({
                    index: i,
                    title,
                    url,
                    is_active: page === this.currentPage
                });
            }
            
            return { success: true, tabs };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async switchToTab(tabIndex) {
        try {
            if (!this.isConnected) {
                return { success: false, error: 'Not connected to browser' };
            }
            
            if (tabIndex >= this.pages.length) {
                return { success: false, error: `Tab index ${tabIndex} not found` };
            }
            
            this.currentPage = this.pages[tabIndex];
            return { success: true, tab_index: tabIndex };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async closeCurrentTab() {
        try {
            if (!this.isConnected || !this.currentPage) {
                return { success: false, error: 'No active page' };
            }
            
            await this.currentPage.close();
            
            // Remove from pages list
            const index = this.pages.indexOf(this.currentPage);
            if (index > -1) {
                this.pages.splice(index, 1);
            }
            
            // Set new current page
            if (this.pages.length > 0) {
                this.currentPage = this.pages[this.pages.length - 1];
            } else {
                this.currentPage = null;
            }
            
            return { success: true };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async executeJavaScript(script) {
        try {
            if (!this.isConnected || !this.currentPage) {
                return { success: false, error: 'No active page' };
            }
            
            // Pass script as a function parameter to handle return statements properly
            const result = await this.currentPage.evaluate((scriptContent) => {
                return eval(scriptContent);
            }, script);
            
            return { success: true, result };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async takeScreenshot(screenshotPath) {
        try {
            if (!this.isConnected || !this.context) {
                return { success: false, error: 'Not connected to browser' };
            }
            
            // First, try to get the currently active tab
            const activeTabResult = await this.getCurrentActiveTab();
            if (activeTabResult.success) {
                this.currentPage = this.context.pages().find(page => page.url() === activeTabResult.currentPage.url);
            }
            
            if (!this.currentPage) {
                return { success: false, error: 'No active page found' };
            }
            
            // Capture full page screenshot as base64
            const screenshotBuffer = await this.currentPage.screenshot({ 
                fullPage: true,  // Capture entire page, not just viewport
                type: 'png'
            });
            
            // Convert buffer to base64
            const base64Data = screenshotBuffer.toString('base64');
            
            // Return base64 data only
            return { 
                success: true, 
                base64: base64Data,
                size: screenshotBuffer.length,
                format: 'png',
                url: this.currentPage.url(),
                title: await this.currentPage.title()
            };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async getFonts() {
        try {
            if (!this.isConnected || !this.currentPage) {
                return { success: false, error: 'No active page' };
            }
            
            const script = `
                () => {
                    const fonts = new Set();
                    const elements = document.querySelectorAll('*');
                    elements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const fontFamily = style.fontFamily;
                        if (fontFamily) {
                            fonts.add(fontFamily);
                        }
                    });
                    return Array.from(fonts);
                }
            `;
            
            const fonts = await this.currentPage.evaluate(script);
            return { success: true, fonts };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async fillForm(formData) {
        try {
            if (!this.isConnected || !this.currentPage) {
                return { success: false, error: 'No active page' };
            }
            
            const script = `
                (formData) => {
                    let filledFields = [];
                    
                    for (const [selector, value] of Object.entries(formData)) {
                        try {
                            const element = document.querySelector(selector);
                            if (element) {
                                element.value = value;
                                element.dispatchEvent(new Event('input', { bubbles: true }));
                                element.dispatchEvent(new Event('change', { bubbles: true }));
                                filledFields.push({ selector, value, success: true });
                            } else {
                                filledFields.push({ selector, value, success: false, error: 'Element not found' });
                            }
                        } catch (error) {
                            filledFields.push({ selector, value, success: false, error: error.message });
                        }
                    }
                    
                    return filledFields;
                }
            `;
            
            const result = await this.currentPage.evaluate(script, formData);
            return { success: true, result };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async pressKey(key) {
        try {
            if (!this.isConnected || !this.currentPage) {
                return { success: false, error: 'No active page' };
            }
            
            const keyMapping = {
                "enter": "Enter",
                "tab": "Tab",
                "escape": "Escape",
                "space": " ",
                "arrow_up": "ArrowUp",
                "arrow_down": "ArrowDown",
                "arrow_left": "ArrowLeft",
                "arrow_right": "ArrowRight",
                "backspace": "Backspace",
                "delete": "Delete",
                "home": "Home",
                "end": "End",
                "page_up": "PageUp",
                "page_down": "PageDown"
            };
            
            const playwrightKey = keyMapping[key.toLowerCase()] || key;
            
            const script = `
                (key) => {
                    document.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: key }));
                    document.activeElement.dispatchEvent(new KeyboardEvent('keyup', { key: key }));
                }
            `;
            
            await this.currentPage.evaluate(script, playwrightKey);
            return { success: true, key };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async getElementInfo(selector, selectorType = 'css') {
        try {
            if (!this.isConnected || !this.currentPage) {
                return { success: false, error: 'No active page' };
            }
            
            const script = `
                (selector, selectorType) => {
                    let element;
                    if (selectorType === 'xpath') {
                        const result = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                        element = result.singleNodeValue;
                    } else {
                        element = document.querySelector(selector);
                    }
                    
                    if (!element) {
                        return { success: false, error: 'Element not found' };
                    }
                    
                    return {
                        success: true,
                        tagName: element.tagName,
                        id: element.id,
                        className: element.className,
                        textContent: element.textContent?.substring(0, 200),
                        value: element.value,
                        href: element.href,
                        src: element.src,
                        title: element.title,
                        attributes: Array.from(element.attributes).map(attr => ({ name: attr.name, value: attr.value })),
                        boundingRect: element.getBoundingClientRect().toJSON(),
                        isVisible: element.offsetParent !== null
                    };
                }
            `;
            
            const result = await this.currentPage.evaluate(script, selector, selectorType);
            return result;
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async getAllLinks() {
        try {
            if (!this.isConnected || !this.currentPage) {
                return { success: false, error: 'No active page' };
            }
            
            const script = `
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    return links.map(link => ({
                        text: link.textContent?.trim() || '',
                        href: link.href,
                        title: link.title || '',
                        target: link.target || '_self',
                        isVisible: link.offsetParent !== null
                    })).filter(link => link.href && link.href !== 'javascript:void(0)');
                }
            `;
            
            const links = await this.currentPage.evaluate(script);
            return { success: true, links };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async getPageMetadata() {
        try {
            if (!this.isConnected || !this.currentPage) {
                return { success: false, error: 'No active page' };
            }
            
            // Use an inline arrow function so Playwright returns the metadata object
            const metadata = await this.currentPage.evaluate(() => ({
                title: document.title,
                url: window.location.href,
                description: document.querySelector('meta[name="description"]')?.content || '',
                keywords: document.querySelector('meta[name="keywords"]')?.content || '',
                author: document.querySelector('meta[name="author"]')?.content || '',
                viewport: document.querySelector('meta[name="viewport"]')?.content || '',
                robots: document.querySelector('meta[name="robots"]')?.content || '',
                ogTitle: document.querySelector('meta[property="og:title"]')?.content || '',
                ogDescription: document.querySelector('meta[property="og:description"]')?.content || '',
                ogImage: document.querySelector('meta[property="og:image"]')?.content || '',
                twitterCard: document.querySelector('meta[name="twitter:card"]')?.content || '',
                canonical: document.querySelector('link[rel="canonical"]')?.href || '',
                language: document.documentElement.lang || '',
                charset: document.characterSet || ''
            }));
            return { success: true, metadata };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async scrollPage(direction, amount = 500, selector = '') {
        try {
            if (!this.isConnected || !this.currentPage) {
                return { success: false, error: 'No active page' };
            }
            
            let script;
            if (direction === 'to' && selector) {
                script = `
                    (selector) => {
                        const element = document.querySelector(selector);
                        if (element) {
                            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            return { success: true, message: 'Scrolled to element' };
                        } else {
                            return { success: false, error: 'Element not found' };
                        }
                    }
                `;
                const result = await this.currentPage.evaluate(script, selector);
                return result;
            } else {
                const scrollMap = {
                    "up": `window.scrollBy(0, -${amount})`,
                    "down": `window.scrollBy(0, ${amount})`,
                    "left": `window.scrollBy(-${amount}, 0)`,
                    "right": `window.scrollBy(${amount}, 0)`
                };
                
                const scrollCommand = scrollMap[direction] || `window.scrollBy(0, ${amount})`;
                script = `${scrollCommand}; return { success: true, message: 'Scrolled ${direction}' };`;
                
                const result = await this.currentPage.evaluate(script);
                return result;
            }
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async highlightElement(selector, color = 'red', duration = 3000) {
        try {
            if (!this.isConnected || !this.currentPage) {
                return { success: false, error: 'No active page' };
            }
            
            const script = `
                (selector, color, duration) => {
                    const element = document.querySelector(selector);
                    if (!element) {
                        return { success: false, error: 'Element not found' };
                    }
                    
                    const originalOutline = element.style.outline;
                    const originalBackground = element.style.backgroundColor;
                    
                    element.style.outline = \`3px solid \${color}\`;
                    element.style.backgroundColor = \`\${color}20\`;
                    
                    setTimeout(() => {
                        element.style.outline = originalOutline;
                        element.style.backgroundColor = originalBackground;
                    }, duration);
                    
                    return { success: true, message: 'Element highlighted' };
                }
            `;
            
            const result = await this.currentPage.evaluate(script, selector, color, duration);
            return result;
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async waitForPageLoad(timeout = 30) {
        try {
            if (!this.isConnected || !this.currentPage) {
                return { success: false, error: 'No active page' };
            }
            
            const script = `
                (timeout) => {
                    return new Promise((resolve) => {
                        if (document.readyState === 'complete') {
                            resolve({ success: true, message: 'Page already loaded' });
                        } else {
                            window.addEventListener('load', () => {
                                resolve({ success: true, message: 'Page loaded' });
                            });
                            
                            setTimeout(() => {
                                resolve({ success: true, message: 'Timeout reached, page may still be loading' });
                            }, timeout * 1000);
                        }
                    });
                }
            `;
            
            const result = await this.currentPage.evaluate(script, timeout);
            return result;
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    start() {
        return new Promise(async (resolve, reject) => {
            try {
                // Start the server first
                this.server = this.app.listen(this.port, async () => {
                    console.log(`🌐 Browser API server running on port ${this.port}`);
                    
                    // Then automatically connect to the browser
                    console.log('🔗 Auto-connecting to browser...');
                    const connectResult = await this.connectToBrowser();
                    
                    if (connectResult.success) {
                        console.log(`✅ Auto-connected to browser with ${connectResult.pages} pages`);
                    } else {
                        console.warn(`⚠️ Auto-connection failed: ${connectResult.error}`);
                        // Don't reject - server is still running, just not connected
                    }
                    
                    resolve();
                });
                
                this.server.on('error', (error) => {
                    console.error('❌ Browser API server error:', error);
                    reject(error);
                });
                
            } catch (error) {
                console.error('❌ Failed to start Browser API server:', error);
                reject(error);
            }
        });
    }
    
    stop() {
        if (this.server) {
            this.server.close();
            console.log('🔒 Browser API server stopped');
        }
    }
}

module.exports = BrowserAPI;