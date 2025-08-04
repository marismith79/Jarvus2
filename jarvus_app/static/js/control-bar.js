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

// Control bar functionality
class ControlBar {
    constructor() {
        this.controlBar = document.getElementById('controlBar');
        this.loginButton = document.getElementById('loginButton');
        this.chatButton = document.getElementById('chatButton');
        this.feedbackButton = document.getElementById('feedbackButton');
        this.browseButton = document.getElementById('browseButton');
        this.optionsButton = document.getElementById('optionsButton');
        this.chatPopup = document.getElementById('chatPopup');
        this.chatPopupMessages = document.getElementById('chatPopupMessages');
        this.chatPopupInput = document.getElementById('chatPopupInput');
        this.chatPopupSend = document.getElementById('chatPopupSend');
        this.isDragging = false;
        this.dragStartX = null;
        this.windowStartX = null;
        this.isChatOpen = false;
        this.wasChatOpenBeforeHide = false; // Track chat state when hiding
        
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
        this.feedbackButton.addEventListener('click', this.handleFeedbackClick.bind(this));
        this.browseButton.addEventListener('click', this.handleBrowseClick.bind(this));
        this.optionsButton.addEventListener('click', this.handleOptionsClick.bind(this));
        this.chatPopupSend.addEventListener('click', this.handleSendMessage.bind(this));
        this.chatPopupInput.addEventListener('keypress', this.handleInputKeypress.bind(this));
        
        // Dragging handlers
        this.controlBar.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // Prevent context menu
        this.controlBar.addEventListener('contextmenu', (e) => e.preventDefault());
        
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
                safeLog('[CONTROL-BAR] Login modal closed, checking authentication status');
                this.handleLoginModalClosed();
            });
        }

        // Handle chat toggle shortcut from main process
        if (window.electronAPI && window.electronAPI.onToggleChat) {
            window.electronAPI.onToggleChat(() => {
                safeLog('[CONTROL-BAR] Chat toggle shortcut received from main process');
                this.handleChatClick();
            });
        }

        // Handle control bar movement shortcuts from main process
        if (window.electronAPI && window.electronAPI.onMoveControlBar) {
            window.electronAPI.onMoveControlBar((event, direction) => {
                safeLog('[CONTROL-BAR] Move control bar shortcut received:', direction);
                this.moveControlBar(direction);
            });
        }

        // Handle control bar visibility toggle shortcuts from main process
        if (window.electronAPI && window.electronAPI.onToggleControlBarVisibility) {
            window.electronAPI.onToggleControlBarVisibility(() => {
                safeLog('[CONTROL-BAR] Toggle control bar visibility shortcut received');
                this.toggleControlBarVisibility();
            });
        }

        // Handle keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
        safeLog('[DEBUG] Keyboard event listener attached');
        
        // Update hotkey display based on platform
        this.updateHotkeyDisplay();
    }
    
    async checkAuthenticationStatus() {
        try {
            safeLog('[CONTROL-BAR] Checking authentication status...');
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
                safeLog('[CONTROL-BAR] User is authenticated');
                this.updateUIForAuthenticatedUser();
            } else {
                safeLog('[CONTROL-BAR] User is not authenticated');
                this.updateUIForUnauthenticatedUser();
            }
        } catch (error) {
            safeError('[CONTROL-BAR] Error checking authentication status:', error);
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
            safeLog('[CONTROL-BAR] User is authenticated, logging out');
            // Logout by calling logout endpoint and updating UI
            this.handleLogout();
        } else {
            safeLog('[CONTROL-BAR] User is not authenticated, opening login modal');
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
            
            safeLog('[CONTROL-BAR] User logged out successfully');
        } catch (error) {
            safeError('[CONTROL-BAR] Error during logout:', error);
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
        safeLog('[DEBUG] Chat button clicked. isChatOpen:', this.isChatOpen);
        if (this.isChatOpen) {
            this.positionChatPopup();
            this.chatPopup.classList.add('open');
            // Focus the input with a small delay to ensure the popup is fully rendered
            setTimeout(() => {
                this.chatPopupInput.focus();
                safeLog('[DEBUG] Input focused');
            }, 50);
            safeLog('[DEBUG] chatPopup after open:', this.chatPopup, this.chatPopup.getBoundingClientRect(), window.getComputedStyle(this.chatPopup));
        } else {
            this.chatPopup.classList.remove('open');
            safeLog('[DEBUG] chatPopup after close:', this.chatPopup, this.chatPopup.getBoundingClientRect(), window.getComputedStyle(this.chatPopup));
        }
    }
    
    handleFeedbackClick() {
        safeLog('feedback button clicked');
    }
    
    handleBrowseClick() {
        safeLog('browse button clicked');
        // Toggle highlighted state
        this.browseButton.classList.toggle('highlighted');
    }
    
    handleOptionsClick() {
        safeLog('Options button clicked');
        window.electronAPI.optionsClick();
    }
    
    async handleSendMessage() {
        const message = this.chatPopupInput.value.trim();
        if (message) {
            this.addMessage('You', message, 'user');
            this.chatPopupInput.value = '';
            // Focus back to input for continued typing
            this.chatPopupInput.focus();
            // Ensure we have the most recent agent
            if (!this.mostRecentAgentId) {
                await this.fetchMostRecentAgent();
            }
            const agentId = this.mostRecentAgentId;
            safeLog('[OVERLAY] Sending message:', message, 'agentId:', agentId);
            // Show thinking message
            const thinkingDiv = this.addMessage('Assistant', '…', 'assistant');
            try {
                if (!agentId) {
                    this.addMessage('Assistant', '⚠️ No agent available. Please create an agent first.', 'assistant');
                    if (thinkingDiv) thinkingDiv.remove();
                    return;
                }
                const res = await fetch('/chatbot/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        agent_id: agentId,
                        web_search_enabled: true
                    })
                });
                // Handle 401 authentication error
                if (res.status === 401) {
                    if (thinkingDiv) thinkingDiv.remove();
                    this.addMessage('Assistant', '🔐 Authentication required. Please log in to continue.', 'assistant');
                    if (window.electronAPI && window.electronAPI.openLoginModal) {
                        const baseUrl = window.location.origin;
                        window.electronAPI.openLoginModal(`${baseUrl}/signin`);
                    }
                    return;
                }
                const data = await res.json();
                safeLog('[OVERLAY] Received response:', data);
                if (thinkingDiv) thinkingDiv.remove();
                if (data.error) {
                    this.addMessage('Assistant', `⚠️ Error: ${data.error}`, 'assistant');
                    return;
                }
                if (data.response) {
                    safeLog('[OVERLAY] Displaying assistant response:', data.response);
                    this.addMessage('Assistant', data.response, 'assistant');
                } else if (Array.isArray(data.new_messages)) {
                    data.new_messages.forEach(msg => {
                        if (typeof msg === 'string') {
                            this.addMessage('Assistant', msg, 'assistant');
                        } else if (msg.role && msg.content) {
                            const sender = msg.role === 'user' ? 'You' : 'Assistant';
                            const type = msg.role === 'user' ? 'user' : 'assistant';
                            this.addMessage(sender, msg.content, type);
                        }
                    });
                }
            } catch (err) {
                if (thinkingDiv) thinkingDiv.remove();
                this.addMessage('Assistant', '⚠️ Error: Failed to get response from the assistant.', 'assistant');
            }
        }
    }
    
    handleInputKeypress(event) {
        if (event.key === 'Enter') {
            this.handleSendMessage();
            // Also trigger the send button click for visual feedback
            this.chatPopupSend.click();
        }
    }
    
    addMessage(sender, text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        // Render markdown for assistant replies, plain text for user
        if (type === 'assistant' && window.marked) {
            messageDiv.innerHTML = window.marked.parse(text);
        } else {
            messageDiv.textContent = text;
        }
        this.chatPopupMessages.appendChild(messageDiv);
        this.chatPopupMessages.scrollTop = this.chatPopupMessages.scrollHeight;
        return messageDiv;
    }
    
    handleMouseDown(event) {
        // Only left mouse button
        if (event.button !== 0) return;
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
        if (this.dragStartX !== null) {
            const deltaX = event.screenX - this.dragStartX;
            // Only start dragging if moved more than 5 pixels
            if (!this.isDragging && Math.abs(deltaX) > 5) {
                this.isDragging = true;
            }
            if (this.isDragging) {
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
    }
    
    handleMouseUp() {
        if (this.isDragging) {
            this.isDragging = false;
            document.body.style.userSelect = '';
            window.electronAPI.endDrag();
        }
        this.dragStartX = null;
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
        safeLog('[DEBUG] positionChatPopup:', {
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
                safeLog('[CONTROL-BAR] ✅ Found stored tokens, attempting auto-login');
                await this.attemptAutoLogin(tokens);
            }
        } catch (error) {
            safeError('[CONTROL-BAR] ❌ Error checking stored credentials:', error);
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
                    safeLog('[CONTROL-BAR] ✅ Auto-login successful');
                    return;
                }
            }
            
            // If we get here, auto-login failed
            await window.electronAPI?.clearAuthTokens();
            safeLog('[CONTROL-BAR] ❌ Auto-login failed');
        } catch (error) {
            safeError('[CONTROL-BAR] ❌ Auto-login error:', error);
            await window.electronAPI?.clearAuthTokens();
        }
    }

    async fetchMostRecentAgent() {
        try {
            const res = await fetch('/chatbot/agents/most-recent', { credentials: 'include' });
            if (res.ok) {
                const data = await res.json();
                this.mostRecentAgentId = data.id;
                this.mostRecentAgentName = data.name;
            } else {
                this.mostRecentAgentId = null;
                this.mostRecentAgentName = null;
            }
        } catch (err) {
            this.mostRecentAgentId = null;
            this.mostRecentAgentName = null;
        }
    }

    updateHotkeyDisplay() {
        const hotkeyDisplay = document.querySelector('.hotkey-display');
        if (hotkeyDisplay) {
            // Use Command on macOS, Ctrl on other platforms
            const modifier = window.electronAPI?.platform === 'darwin' ? '⌘' : 'Ctrl';
            hotkeyDisplay.textContent = `${modifier}↵`;
        }
    }
    
    handleKeyDown(event) {
        safeLog('[DEBUG] Key pressed:', event.key, 'metaKey:', event.metaKey, 'ctrlKey:', event.ctrlKey);
        
        // Command+Enter (macOS) or Ctrl+Enter (other platforms) to toggle chat
        if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
            safeLog('[DEBUG] Command+Enter detected, toggling chat');
            event.preventDefault();
            this.handleChatClick();
        }
        
        // Escape to close chat popup if open
        if (event.key === 'Escape' && this.isChatOpen) {
            safeLog('[DEBUG] Escape detected, closing chat');
            event.preventDefault();
            this.handleChatClick();
        }
    }

    moveControlBar(direction) {
        const moveAmount = 50; // pixels to move each time
        const controlBarWidth = 500; // control bar width
        
        window.electronAPI.getWindowBounds().then(bounds => {
            let newX = bounds.x;
            
            if (direction === 'left') {
                newX = Math.max(0, bounds.x - moveAmount);
            } else if (direction === 'right') {
                const maxX = window.screen.width - controlBarWidth;
                newX = Math.min(maxX, bounds.x + moveAmount);
            }
            
            window.electronAPI.setWindowPosition(newX, bounds.y);
            safeLog(`[CONTROL-BAR] Moved control bar ${direction} to x=${newX}`);
            
            // Reposition chat popup if open
            if (this.isChatOpen) {
                this.positionChatPopup();
            }
        });
    }

    toggleControlBarVisibility() {
        // Close chat popup if open when hiding the control bar
        if (this.isChatOpen) {
            this.wasChatOpenBeforeHide = true;
            this.handleChatClick();
        }
        
        // Toggle window visibility using Electron API
        window.electronAPI.isWindowVisible().then(isVisible => {
            if (isVisible) {
                // Window is visible, hide it
                window.electronAPI.hideWindow();
                safeLog('[CONTROL-BAR] Control bar hidden');
            } else {
                // Window is hidden, show it
                window.electronAPI.showWindow();
                safeLog('[CONTROL-BAR] Control bar shown');
                
                // Restore chat state if it was open before hiding
                if (this.wasChatOpenBeforeHide) {
                    setTimeout(() => {
                        this.handleChatClick();
                        this.wasChatOpenBeforeHide = false;
                    }, 100); // Small delay to ensure window is fully shown
                }
            }
        });
    }
}

// Initialize the control bar when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ControlBar();
}); 