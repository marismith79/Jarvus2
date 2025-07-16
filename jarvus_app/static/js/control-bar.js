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
        this.taskButton = document.getElementById('taskButton');
        this.browseButton = document.getElementById('browseButton');
        this.optionsButton = document.getElementById('optionsButton');
        this.chatPopup = document.getElementById('chatPopup');
        this.chatPopupMessages = document.getElementById('chatPopupMessages');
        this.chatPopupInput = document.getElementById('chatPopupInput');
        this.chatPopupSend = document.getElementById('chatPopupSend');
        this.optionsDropdown = document.getElementById('optionsDropdown');
        this.quitAppButton = document.getElementById('quitAppButton');
        this.statusDropdown = document.getElementById('statusDropdown');
        this.workflowList = document.getElementById('workflowList');
        this.taskDropdown = document.getElementById('taskDropdown');
        this.taskList = document.getElementById('taskList');
        this.isDragging = false;
        this.dragStartX = null;
        this.windowStartX = null;
        this.isChatOpen = false;
        this.wasChatOpenBeforeHide = false; // Track chat state when hiding
        this.isOptionsDropdownOpen = false;
        this.isStatusDropdownOpen = false;
        this.isTaskDropdownOpen = false;
        
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
        this.taskButton.addEventListener('click', this.handleTaskClick.bind(this));
        
        this.optionsButton.addEventListener('click', this.handleOptionsClick.bind(this));
        this.chatPopupSend.addEventListener('click', this.handleSendMessage.bind(this));
        this.chatPopupInput.addEventListener('keypress', this.handleInputKeypress.bind(this));
        this.quitAppButton.addEventListener('click', this.handleQuitApp.bind(this));
        
        // Work/Status button click handler
        this.browseButton.addEventListener('click', this.handleStatusClick.bind(this));
        
        // Close dropdown when clicking outside
        document.addEventListener('click', this.handleDocumentClick.bind(this));
        
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
        this.optionsDropdown.addEventListener('mouseenter', () => {
            window.electronAPI.setIgnoreMouseEvents(false);
        });
        this.optionsDropdown.addEventListener('mouseleave', (e) => {
            // Only re-enable click-through if not hovering bar or chatPopup
            if (!this.controlBar.matches(':hover') && !this.chatPopup.matches(':hover')) {
                window.electronAPI.setIgnoreMouseEvents(true);
            }
        });
        
        // Status dropdown mouse enter/leave handlers
        this.statusDropdown.addEventListener('mouseenter', () => {
            window.electronAPI.setIgnoreMouseEvents(false);
        });
        this.statusDropdown.addEventListener('mouseleave', (e) => {
            // Only re-enable click-through if not hovering bar, chatPopup, or optionsDropdown
            if (!this.controlBar.matches(':hover') && !this.chatPopup.matches(':hover') && !this.optionsDropdown.matches(':hover')) {
                window.electronAPI.setIgnoreMouseEvents(true);
            }
        });
        
        // Task dropdown mouse enter/leave handlers
        this.taskDropdown.addEventListener('mouseenter', () => {
            window.electronAPI.setIgnoreMouseEvents(false);
        });
        this.taskDropdown.addEventListener('mouseleave', (e) => {
            // Only re-enable click-through if not hovering bar, chatPopup, optionsDropdown, or statusDropdown
            if (!this.controlBar.matches(':hover') && !this.chatPopup.matches(':hover') && !this.optionsDropdown.matches(':hover') && !this.statusDropdown.matches(':hover')) {
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
        
        // Close status dropdown if open
        if (this.isStatusDropdownOpen) {
            this.toggleStatusDropdown();
        }
        
        // Close task dropdown if open
        if (this.isTaskDropdownOpen) {
            this.toggleTaskDropdown();
        }
        
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
    
    handleTaskClick(event) {
        event.stopPropagation(); // Prevent document click from immediately closing
        safeLog('Task button clicked');
        this.toggleTaskDropdown();
    }
    

    
    handleStatusClick(event) {
        event.stopPropagation(); // Prevent document click from immediately closing
        safeLog('Status button clicked');
        this.toggleStatusDropdown();
    }
    
    handleOptionsClick(event) {
        event.stopPropagation(); // Prevent document click from immediately closing
        safeLog('Options button clicked');
        this.toggleOptionsDropdown();
    }
    
    toggleOptionsDropdown() {
        this.isOptionsDropdownOpen = !this.isOptionsDropdownOpen;
        if (this.isOptionsDropdownOpen) {
            this.optionsDropdown.classList.add('open');
            // Close chat popup if open
            if (this.isChatOpen) {
                this.handleChatClick();
            }
            // Close status dropdown if open
            if (this.isStatusDropdownOpen) {
                this.toggleStatusDropdown();
            }
            // Close task dropdown if open
            if (this.isTaskDropdownOpen) {
                this.toggleTaskDropdown();
            }
        } else {
            this.optionsDropdown.classList.remove('open');
        }
    }
    
    toggleStatusDropdown() {
        this.isStatusDropdownOpen = !this.isStatusDropdownOpen;
        if (this.isStatusDropdownOpen) {
            this.statusDropdown.classList.add('open');
            this.browseButton.classList.add('highlighted');
            // Close chat popup if open
            if (this.isChatOpen) {
                this.handleChatClick();
            }
            // Close options dropdown if open
            if (this.isOptionsDropdownOpen) {
                this.toggleOptionsDropdown();
            }
            // Close task dropdown if open
            if (this.isTaskDropdownOpen) {
                this.toggleTaskDropdown();
            }
            // Load workflows
            this.loadWorkflows();
        } else {
            this.statusDropdown.classList.remove('open');
            this.browseButton.classList.remove('highlighted');
        }
    }
    
    toggleTaskDropdown() {
        this.isTaskDropdownOpen = !this.isTaskDropdownOpen;
        if (this.isTaskDropdownOpen) {
            this.taskDropdown.classList.add('open');
            this.taskButton.classList.add('highlighted');
            // Close chat popup if open
            if (this.isChatOpen) {
                this.handleChatClick();
            }
            // Close options dropdown if open
            if (this.isOptionsDropdownOpen) {
                this.toggleOptionsDropdown();
            }
            // Close status dropdown if open
            if (this.isStatusDropdownOpen) {
                this.toggleStatusDropdown();
            }
            // Load tasks
            this.loadTasks();
        } else {
            this.taskDropdown.classList.remove('open');
            this.taskButton.classList.remove('highlighted');
        }
    }
    
    handleDocumentClick(event) {
        // Close options dropdown if clicking outside
        if (this.isOptionsDropdownOpen && 
            !this.optionsButton.contains(event.target) && 
            !this.optionsDropdown.contains(event.target)) {
            this.toggleOptionsDropdown();
        }
        
        // Close status dropdown if clicking outside
        if (this.isStatusDropdownOpen && 
            !this.browseButton.contains(event.target) && 
            !this.statusDropdown.contains(event.target)) {
            this.toggleStatusDropdown();
        }
        
        // Close task dropdown if clicking outside
        if (this.isTaskDropdownOpen && 
            !this.taskButton.contains(event.target) && 
            !this.taskDropdown.contains(event.target)) {
            this.toggleTaskDropdown();
        }
    }
    
    handleQuitApp() {
        safeLog('Quit app button clicked');
        if (window.electronAPI && window.electronAPI.quitApp) {
            window.electronAPI.quitApp();
        } else {
            safeLog('Quit app API not available');
        }
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
        
        // Copy assistant messages to clipboard
        if (type === 'assistant' && window.electronAPI && window.electronAPI.copyToClipboard) {
            // Extract plain text from the message (remove HTML tags if present)
            const plainText = messageDiv.textContent || messageDiv.innerText || text;
            window.electronAPI.copyToClipboard(plainText).then(result => {
                if (result.success) {
                    safeLog('[CONTROL-BAR] ✅ Assistant message copied to clipboard');
                } else {
                    safeError('[CONTROL-BAR] ❌ Failed to copy to clipboard:', result.error);
                }
            }).catch(error => {
                safeError('[CONTROL-BAR] ❌ Error copying to clipboard:', error);
            });
        }
        
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

    async loadWorkflows() {
        try {
            safeLog('[STATUS] Loading workflows...');
            
            // Load workflows and their status
            const [workflowsResponse, statusResponse] = await Promise.all([
                fetch('/workflows', {
                    credentials: 'include',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                }),
                fetch('/workflows/status-summary', {
                    credentials: 'include',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                })
            ]);
            
            if (workflowsResponse.ok && statusResponse.ok) {
                const workflowsData = await workflowsResponse.json();
                const statusData = await statusResponse.json();
                
                safeLog('[STATUS] Raw workflows data:', workflowsData);
                safeLog('[STATUS] Raw status data:', statusData);
                
                const workflows = workflowsData.workflows || [];
                const statusSummary = statusData.summary || {};
                
                // Merge workflow data with status information
                const workflowsWithStatus = this.mergeWorkflowStatus(workflows, statusSummary);
                safeLog('[STATUS] Workflows with status:', workflowsWithStatus);
                
                this.displayWorkflows(workflowsWithStatus);
            } else {
                safeError('[STATUS] Failed to load workflows or status:', workflowsResponse.status, statusResponse.status);
                this.displayWorkflows([]);
            }
        } catch (error) {
            safeError('[STATUS] Error loading workflows:', error);
            this.displayWorkflows([]);
        }
    }
    
    mergeWorkflowStatus(workflows, statusSummary) {
        const runningWorkflowIds = (statusSummary.running_workflows || []).map(w => w.id);
        const recentWorkflowIds = (statusSummary.recently_ran_workflows || []).map(w => w.id);
        
        return workflows.map(workflow => {
            let status = 'idle';
            if (runningWorkflowIds.includes(workflow.id)) {
                status = 'running';
            } else if (recentWorkflowIds.includes(workflow.id)) {
                status = 'completed';
            }
            
            return {
                ...workflow,
                status: status
            };
        });
    }
    
    displayWorkflows(workflows) {
        // Clear existing workflows
        this.workflowList.innerHTML = '';
        
        if (!workflows || workflows.length === 0) {
            const noWorkflowsItem = document.createElement('div');
            noWorkflowsItem.className = 'workflow-item';
            noWorkflowsItem.textContent = 'No workflows found';
            noWorkflowsItem.style.color = '#6b7280';
            noWorkflowsItem.style.fontStyle = 'italic';
            this.workflowList.appendChild(noWorkflowsItem);
            return;
        }
        
        // Add each workflow
        workflows.forEach(workflow => {
            const workflowItem = document.createElement('div');
            workflowItem.className = 'workflow-item';
            
            // Create workflow content
            const workflowContent = document.createElement('div');
            workflowContent.className = 'workflow-content';
            
            // Create status indicator
            const statusIndicator = document.createElement('div');
            statusIndicator.className = 'workflow-status-indicator';
            if (workflow.status === 'running') {
                statusIndicator.classList.add('running');
            } else if (workflow.status === 'completed') {
                statusIndicator.classList.add('completed');
            }
            
            // Create workflow name
            const workflowName = document.createElement('div');
            workflowName.className = 'workflow-name';
            workflowName.textContent = workflow.name || 'Unnamed Workflow';
            workflowName.title = workflow.description || workflow.name || 'No description';
            
            // Create actions container
            const actionsContainer = document.createElement('div');
            actionsContainer.className = 'workflow-actions';
            
            // Create start/stop button
            const actionButton = document.createElement('button');
            actionButton.className = 'workflow-action-btn';
            
            if (workflow.status === 'running') {
                actionButton.classList.add('stop');
                actionButton.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="6" width="12" height="12"></rect></svg>';
                actionButton.title = 'Stop workflow';
                actionButton.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.stopWorkflow(workflow.id, workflow.name);
                });
            } else {
                actionButton.classList.add('start');
                actionButton.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5,3 19,12 5,21"></polygon></svg>';
                actionButton.title = 'Start workflow';
                actionButton.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.startWorkflow(workflow.id, workflow.name);
                });
            }
            
            // Assemble the workflow item
            workflowContent.appendChild(statusIndicator);
            workflowContent.appendChild(workflowName);
            actionsContainer.appendChild(actionButton);
            
            workflowItem.appendChild(workflowContent);
            workflowItem.appendChild(actionsContainer);
            
            // Add click handler for the entire item (for future functionality)
            workflowItem.addEventListener('click', () => {
                safeLog('[STATUS] Workflow clicked:', workflow.name);
                // TODO: Add workflow details view functionality
            });
            
            this.workflowList.appendChild(workflowItem);
        });
    }
    
    async startWorkflow(workflowId, workflowName) {
        try {
            safeLog('[STATUS] Starting workflow:', workflowId, workflowName);
            
            const response = await fetch(`/workflows/${workflowId}/execute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({})
            });
            
            if (response.ok) {
                const data = await response.json();
                safeLog('[STATUS] Workflow started successfully:', data);
                
                // Show success message in chat popup
                this.addMessage('System', `🚀 Started workflow: ${workflowName}`, 'system');
                
                // Refresh the workflow list to update status
                setTimeout(() => {
                    this.loadWorkflows();
                }, 1000);
            } else {
                const errorData = await response.json();
                safeError('[STATUS] Failed to start workflow:', errorData);
                this.addMessage('System', `❌ Failed to start workflow: ${errorData.error || 'Unknown error'}`, 'system');
            }
        } catch (error) {
            safeError('[STATUS] Error starting workflow:', error);
            this.addMessage('System', `❌ Error starting workflow: ${error.message}`, 'system');
        }
    }
    
    async stopWorkflow(workflowId, workflowName) {
        try {
            safeLog('[STATUS] Stopping workflow:', workflowId, workflowName);
            
            // First, we need to find the execution ID for this workflow
            const executionsResponse = await fetch('/workflows/executions', {
                credentials: 'include',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });
            
            if (executionsResponse.ok) {
                const executionsData = await executionsResponse.json();
                const runningExecution = executionsData.executions?.find(ex => 
                    ex.workflow_id === workflowId && ex.status === 'running'
                );
                
                if (runningExecution) {
                    const cancelResponse = await fetch(`/workflows/executions/${runningExecution.execution_id}/cancel`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        credentials: 'include'
                    });
                    
                    if (cancelResponse.ok) {
                        safeLog('[STATUS] Workflow stopped successfully');
                        this.addMessage('System', `⏹️ Stopped workflow: ${workflowName}`, 'system');
                        
                        // Refresh the workflow list to update status
                        setTimeout(() => {
                            this.loadWorkflows();
                        }, 1000);
                    } else {
                        safeError('[STATUS] Failed to stop workflow');
                        this.addMessage('System', `❌ Failed to stop workflow: ${workflowName}`, 'system');
                    }
                } else {
                    safeError('[STATUS] No running execution found for workflow');
                    this.addMessage('System', `❌ No running execution found for workflow: ${workflowName}`, 'system');
                }
            } else {
                safeError('[STATUS] Failed to get executions');
                this.addMessage('System', `❌ Failed to get workflow executions`, 'system');
            }
        } catch (error) {
            safeError('[STATUS] Error stopping workflow:', error);
            this.addMessage('System', `❌ Error stopping workflow: ${error.message}`, 'system');
        }
    }
    
    async loadTasks() {
        try {
            const response = await fetch('/chatbot/todos', { credentials: 'include' });
            const data = await response.json();
            this.displayTasks(data.todos || []);
        } catch (error) {
            this.displayTasks([]);
        }
    }
    
    displayTasks(tasks) {
        this.taskList.innerHTML = '';
        
        if (!tasks.length) {
            this.taskList.innerHTML = '<div class="task-item" style="color:#6b7280;font-style:italic">No tasks found</div>';
            return;
        }
        
        tasks.forEach((task, index) => {
            const taskItem = document.createElement('div');
            taskItem.className = 'task-item';
            taskItem.dataset.taskId = task.id;
            taskItem.dataset.taskIndex = index;
            if (task.completed) taskItem.classList.add('completed');
            
            taskItem.innerHTML = `
                <div class="task-content">
                    <div class="task-drag-handle" title="Drag to reorder">⋮⋮</div>
                    <input type="checkbox" class="task-checkbox" ${task.completed ? 'checked' : ''}>
                    <div class="task-text" title="${task.text}">${task.text}</div>
                </div>
                <div class="task-actions">
                    <button class="task-action-btn" title="Delete task" onclick="this.closest('.task-item').remove()">🗑️</button>
                </div>
            `;
            
            // Add event listeners
            taskItem.querySelector('.task-checkbox').addEventListener('change', (e) => {
                e.stopPropagation();
                this.toggleTaskCompletion(task.id, task.text, e.target.checked);
            });
            
            this.setupDragAndDrop(taskItem, task.id);
            this.taskList.appendChild(taskItem);
        });
    }
    
    async toggleTaskCompletion(taskId, taskText, completed) {
        try {
            await fetch(`/chatbot/todos/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ completed })
            });
            this.addMessage('System', `✅ Task ${completed ? 'completed' : 'uncompleted'}: ${taskText}`, 'system');
        } catch (error) {
            this.addMessage('System', `❌ Error updating task`, 'system');
        }
    }
    
    setupDragAndDrop(taskItem, taskId) {
        const dragHandle = taskItem.querySelector('.task-drag-handle');
        let isDragging = false;
        let originalIndex = parseInt(taskItem.dataset.taskIndex);
        
        dragHandle.addEventListener('mousedown', (e) => {
            e.preventDefault();
            isDragging = true;
            taskItem.classList.add('dragging');
            
            const clone = taskItem.cloneNode(true);
            clone.style.cssText = `position:fixed;top:${e.clientY-10}px;left:${e.clientX-10}px;width:${taskItem.offsetWidth}px;z-index:10000;pointer-events:none`;
            document.body.appendChild(clone);
            
            const handleMouseMove = (e) => {
                if (!isDragging) return;
                clone.style.top = `${e.clientY-10}px`;
                clone.style.left = `${e.clientX-10}px`;
            };
            
            const handleMouseUp = (e) => {
                if (!isDragging) return;
                isDragging = false;
                taskItem.classList.remove('dragging');
                document.body.removeChild(clone);
                
                const taskItems = Array.from(this.taskList.querySelectorAll('.task-item:not(.dragging)'));
                let newIndex = taskItems.findIndex(item => {
                    const rect = item.getBoundingClientRect();
                    return e.clientY < rect.top + rect.height / 2;
                });
                if (newIndex === -1) newIndex = taskItems.length;
                
                if (newIndex !== originalIndex) {
                    taskItem.remove();
                    if (newIndex >= taskItems.length) {
                        this.taskList.appendChild(taskItem);
                    } else {
                        this.taskList.insertBefore(taskItem, taskItems[newIndex]);
                    }
                    this.updateTaskIndices();
                    this.addMessage('System', `🔄 Task reordered`, 'system');
                }
                
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            };
            
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
        });
    }
    
    updateTaskIndices() {
        this.taskList.querySelectorAll('.task-item').forEach((item, index) => {
            item.dataset.taskIndex = index;
        });
    }
    
    updateHotkeyDisplay() {
        // Get all hotkey displays
        const hotkeyDisplays = document.querySelectorAll('.hotkey-display');
        
        hotkeyDisplays.forEach(display => {
            // Check if this is the chat button hotkey (Command+Enter)
            if (display.closest('#chatButton')) {
                const modifier = window.electronAPI?.platform === 'darwin' ? '⌘' : 'Ctrl';
                display.textContent = `${modifier}↵`;
            }
            // Check if this is the task button hotkey (Command+Option+T)
            else if (display.closest('#taskButton')) {
                const modifier = window.electronAPI?.platform === 'darwin' ? '⌘' : 'Ctrl';
                const optionKey = window.electronAPI?.platform === 'darwin' ? '⌥' : 'Alt';
                display.textContent = `${modifier}${optionKey}t`;
            }
        });
    }
    
    handleKeyDown(event) {
        safeLog('[DEBUG] Key pressed:', event.key, 'metaKey:', event.metaKey, 'ctrlKey:', event.ctrlKey);
        
        // Command+Enter (macOS) or Ctrl+Enter (other platforms) to toggle chat
        if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
            safeLog('[DEBUG] Command+Enter detected, toggling chat');
            event.preventDefault();
            this.handleChatClick();
        }
        
        // Escape to close chat popup or dropdowns if open
        if (event.key === 'Escape') {
            if (this.isChatOpen) {
                safeLog('[DEBUG] Escape detected, closing chat');
                event.preventDefault();
                this.handleChatClick();
            } else if (this.isOptionsDropdownOpen) {
                safeLog('[DEBUG] Escape detected, closing options dropdown');
                event.preventDefault();
                this.toggleOptionsDropdown();
            } else if (this.isStatusDropdownOpen) {
                safeLog('[DEBUG] Escape detected, closing status dropdown');
                event.preventDefault();
                this.toggleStatusDropdown();
            } else if (this.isTaskDropdownOpen) {
                safeLog('[DEBUG] Escape detected, closing task dropdown');
                event.preventDefault();
                this.toggleTaskDropdown();
            }
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
                // Unregister shortcuts when hiding
                if (window.electronAPI.unregisterShortcuts) {
                    window.electronAPI.unregisterShortcuts();
                }
                safeLog('[CONTROL-BAR] Control bar hidden, shortcuts unregistered');
            } else {
                // Window is hidden, show it
                window.electronAPI.showWindow();
                // Register shortcuts when showing
                if (window.electronAPI.registerShortcuts) {
                    window.electronAPI.registerShortcuts();
                }
                safeLog('[CONTROL-BAR] Control bar shown, shortcuts registered');
                
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