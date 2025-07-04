// Control bar functionality
class ControlBar {
    constructor() {
        this.controlBar = document.getElementById('controlBar');
        this.loginButton = document.getElementById('loginButton');
        this.chatButton = document.getElementById('chatButton');
        this.optionsButton = document.getElementById('optionsButton');
        this.chatPopup = document.getElementById('chatPopup');
        this.chatPopupMessages = document.getElementById('chatPopupMessages');
        this.chatPopupInput = document.getElementById('chatPopupInput');
        this.chatPopupSend = document.getElementById('chatPopupSend');
        this.isDragging = false;
        this.dragStartX = 0;
        this.windowStartX = 0;
        this.isChatOpen = false;
        
        // Authentication state
        this.isAuthenticated = false;
        this.jwtToken = null;
        
        this.initializeEventListeners();
        this.checkAuthenticationStatus();
        this.checkForStoredCredentials();
    }
    
    initializeEventListeners() {
        // Button click handlers
        this.loginButton.addEventListener('click', this.handleLoginClick.bind(this));
        this.chatButton.addEventListener('click', this.handleChatClick.bind(this));
        this.optionsButton.addEventListener('click', this.handleOptionsClick.bind(this));
        this.chatPopupSend.addEventListener('click', this.handleSendMessage.bind(this));
        this.chatPopupInput.addEventListener('keypress', this.handleInputKeypress.bind(this));
        
        // Dragging handlers
        this.controlBar.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // Prevent context menu
        this.controlBar.addEventListener('contextmenu', (e) => e.preventDefault());
        
        // Handle window resize
        window.addEventListener('resize', this.handleWindowResize.bind(this));
        
        // Mouse enter/leave for click-through logic
        this.controlBar.addEventListener('mouseenter', () => {
            window.electronAPI.setIgnoreMouseEvents(false);
        });
        this.controlBar.addEventListener('mouseleave', (e) => {
            // Only re-enable click-through if not hovering popup
            if (!this.chatPopup.matches(':hover')) {
                window.electronAPI.setIgnoreMouseEvents(true);
            }
        });
        this.chatPopup.addEventListener('mouseenter', () => {
            window.electronAPI.setIgnoreMouseEvents(false);
        });
        this.chatPopup.addEventListener('mouseleave', (e) => {
            // Only re-enable click-through if not hovering bar
            if (!this.controlBar.matches(':hover')) {
                window.electronAPI.setIgnoreMouseEvents(true);
            }
        });

        // Handle login modal closed event
        if (window.electronAPI && window.electronAPI.onLoginModalClosed) {
            window.electronAPI.onLoginModalClosed(() => {
                console.log('[CONTROL-BAR] Login modal closed, checking authentication status');
                this.handleLoginModalClosed();
            });
        }
    }
    
    async checkAuthenticationStatus() {
        try {
            console.log('[CONTROL-BAR] Checking authentication status...');
            const response = await fetch('/api/jwt', {
                credentials: 'include',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.jwtToken = data.jwt;
                this.isAuthenticated = true;
                console.log('[CONTROL-BAR] User is authenticated');
                this.updateUIForAuthenticatedUser();
            } else {
                console.log('[CONTROL-BAR] User is not authenticated');
                this.updateUIForUnauthenticatedUser();
            }
        } catch (error) {
            console.error('[CONTROL-BAR] Error checking authentication status:', error);
            this.updateUIForUnauthenticatedUser();
        }
    }

    updateUIForAuthenticatedUser() {
        this.loginButton.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16,17 21,12 16,7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            <span>Logout</span>
        `;
        this.loginButton.classList.add('authenticated');
    }

    updateUIForUnauthenticatedUser() {
        this.loginButton.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                <polyline points="10,17 15,12 10,7"/>
                <line x1="15" y1="12" x2="3" y2="12"/>
            </svg>
            <span>Login</span>
        `;
        this.loginButton.classList.remove('authenticated');
    }

    handleLoginClick() {
        if (this.isAuthenticated) {
            console.log('[CONTROL-BAR] User is authenticated, logging out');
            // Logout by calling logout endpoint and updating UI
            this.handleLogout();
        } else {
            console.log('[CONTROL-BAR] User is not authenticated, opening login modal');
            // Open login modal with full URL
            if (window.electronAPI && window.electronAPI.openLoginModal) {
                const baseUrl = window.location.origin;
                window.electronAPI.openLoginModal(`${baseUrl}/signin`);
            }
        }
    }

    async handleLogout() {
        try {
            // Call logout endpoint to clear server-side session
            const response = await fetch('/logout', {
                method: 'GET',
                credentials: 'include'
            });
            
            // Update local state regardless of response
            this.isAuthenticated = false;
            this.jwtToken = null;
            this.updateUIForUnauthenticatedUser();
            
            console.log('[CONTROL-BAR] User logged out successfully');
        } catch (error) {
            console.error('[CONTROL-BAR] Error during logout:', error);
            // Still update UI even if server call fails
            this.isAuthenticated = false;
            this.jwtToken = null;
            this.updateUIForUnauthenticatedUser();
        }
    }

    async handleLoginModalClosed() {
        // Simple retry after 1 second
        setTimeout(async () => {
            await this.checkAuthenticationStatus();
        }, 1000);
    }
    
    handleChatClick() {
        this.isChatOpen = !this.isChatOpen;
        console.log('[DEBUG] Chat button clicked. isChatOpen:', this.isChatOpen);
        if (this.isChatOpen) {
            this.positionChatPopup();
            this.chatPopup.classList.add('open');
            this.chatPopupInput.focus();
            console.log('[DEBUG] chatPopup after open:', this.chatPopup, this.chatPopup.getBoundingClientRect(), window.getComputedStyle(this.chatPopup));
        } else {
            this.chatPopup.classList.remove('open');
            console.log('[DEBUG] chatPopup after close:', this.chatPopup, this.chatPopup.getBoundingClientRect(), window.getComputedStyle(this.chatPopup));
        }
    }
    
    handleOptionsClick() {
        console.log('Options button clicked');
        window.electronAPI.optionsClick();
    }
    
    handleSendMessage() {
        const message = this.chatPopupInput.value.trim();
        if (message) {
            this.addMessage('You', message, 'user');
            this.chatPopupInput.value = '';
            // Simulate assistant response
            setTimeout(() => {
                this.addMessage('Assistant', 'This is a placeholder response.', 'assistant');
            }, 1000);
        }
    }
    
    handleInputKeypress(event) {
        if (event.key === 'Enter') {
            this.handleSendMessage();
        }
    }
    
    addMessage(sender, text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        messageDiv.textContent = text;
        this.chatPopupMessages.appendChild(messageDiv);
        this.chatPopupMessages.scrollTop = this.chatPopupMessages.scrollHeight;
    }
    
    handleMouseDown(event) {
        // Only left mouse button
        if (event.button !== 0) return;
        this.isDragging = true;
        this.dragStartX = event.screenX;
        this.windowStartX = 0;
        // Get current window position from main process
        window.electronAPI.getWindowBounds().then(bounds => {
            this.windowStartX = bounds.x;
        });
        // Prevent text selection
        document.body.style.userSelect = 'none';
    }
    
    handleMouseMove(event) {
        if (this.isDragging) {
            const deltaX = event.screenX - this.dragStartX;
            const newX = this.windowStartX + deltaX;
            // Constrain to screen bounds
            const maxX = window.screen.width - 300; // control bar width
            const constrainedX = Math.max(0, Math.min(newX, maxX));
            window.electronAPI.setWindowPosition(constrainedX, 20);
            // Reposition chat popup if open
            if (this.isChatOpen) {
                this.positionChatPopup();
            }
        }
    }
    
    handleMouseUp() {
        if (this.isDragging) {
            this.isDragging = false;
            document.body.style.userSelect = '';
            window.electronAPI.endDrag();
        }
    }
    
    handleWindowResize() {
        // Reposition control bar if needed
        const controlBarRect = this.controlBar.getBoundingClientRect();
        const maxX = window.innerWidth - controlBarRect.width;
        if (controlBarRect.left > maxX) {
            this.controlBar.style.left = `${maxX}px`;
            this.controlBar.style.transform = 'none';
        }
        // Reposition chat popup if open
        if (this.isChatOpen) {
            this.positionChatPopup();
        }
    }

    positionChatPopup() {
        // Get the bounding rect of the control bar
        const barRect = this.controlBar.getBoundingClientRect();
        // Set the popup width to match the control bar
        this.chatPopup.style.width = `${barRect.width}px`;
        // Calculate vertical position
        const gap = 6;
        let top = barRect.bottom + gap;
        // If popup would overflow window, show above the bar
        const popupHeight = this.chatPopup.offsetHeight || 180; // fallback height
        if (top + popupHeight > window.innerHeight) {
            top = barRect.top - popupHeight - gap;
        }
        this.chatPopup.style.left = `${barRect.left}px`;
        this.chatPopup.style.top = `${top}px`;
        console.log('[DEBUG] positionChatPopup:', {
            left: this.chatPopup.style.left,
            top: this.chatPopup.style.top,
            width: this.chatPopup.style.width,
            barRect,
            popupRect: this.chatPopup.getBoundingClientRect(),
            computed: window.getComputedStyle(this.chatPopup)
        });
    }

    async checkForStoredCredentials() {
        try {
            if (!window.electronAPI?.getAuthTokens) return;
            
            const tokens = await window.electronAPI.getAuthTokens();
            if (tokens?.refresh_token) {
                console.log('[CONTROL-BAR] ✅ Found stored tokens, attempting auto-login');
                await this.attemptAutoLogin(tokens);
            }
        } catch (error) {
            console.error('[CONTROL-BAR] ❌ Error checking stored credentials:', error);
        }
    }
    
    async attemptAutoLogin(tokens) {
        try {
            const response = await fetch('/refresh-token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: tokens.refresh_token }),
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    await window.electronAPI?.storeAuthTokens(data.tokens);
                    this.isAuthenticated = true;
                    this.jwtToken = data.tokens.id_token;
                    this.updateUIForAuthenticatedUser();
                    console.log('[CONTROL-BAR] ✅ Auto-login successful');
                    return;
                }
            }
            
            // If we get here, auto-login failed
            await window.electronAPI?.clearAuthTokens();
            console.log('[CONTROL-BAR] ❌ Auto-login failed');
        } catch (error) {
            console.error('[CONTROL-BAR] ❌ Auto-login error:', error);
            await window.electronAPI?.clearAuthTokens();
        }
    }
}

// Initialize the control bar when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ControlBar();
});

// Handle keyboard shortcuts
document.addEventListener('keydown', (event) => {
    // Cmd/Ctrl + Shift + C to toggle chat
    if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key === 'C') {
        event.preventDefault();
        const controlBar = document.querySelector('.control-bar')?.__controlBar;
        if (controlBar) {
            controlBar.toggleChat();
        }
    }
    
    // Escape to close chat
    if (event.key === 'Escape') {
        const chatArea = document.getElementById('chatArea');
        if (chatArea && chatArea.style.display === 'block') {
            const controlBar = document.querySelector('.control-bar')?.__controlBar;
            if (controlBar) {
                controlBar.toggleChat();
            }
        }
    }
}); 