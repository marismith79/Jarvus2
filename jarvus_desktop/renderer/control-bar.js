// Control bar functionality
class ControlBar {
    constructor() {
        this.controlBar = document.getElementById('controlBar');
        this.chatArea = document.getElementById('chatArea');
        this.chatButton = document.getElementById('chatButton');
        this.loginButton = document.getElementById('loginButton');
        this.optionsButton = document.getElementById('optionsButton');
        this.chatInput = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        
        this.isDragging = false;
        this.dragStartX = 0;
        this.windowStartX = 0;
        this.isChatOpen = false;
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Button click handlers
        this.loginButton.addEventListener('click', this.handleLoginClick.bind(this));
        this.chatButton.addEventListener('click', this.handleChatClick.bind(this));
        this.optionsButton.addEventListener('click', this.handleOptionsClick.bind(this));
        this.sendButton.addEventListener('click', this.handleSendMessage.bind(this));
        
        // Chat input handlers
        this.chatInput.addEventListener('keypress', this.handleChatInputKeypress.bind(this));
        
        // Dragging handlers
        this.controlBar.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // Prevent context menu
        this.controlBar.addEventListener('contextmenu', (e) => e.preventDefault());
        
        // Handle window resize
        window.addEventListener('resize', this.handleWindowResize.bind(this));
    }
    
    handleLoginClick() {
        console.log('Login button clicked');
        window.electronAPI.loginClick().then(() => {
            // Handle login response
            this.addMessage('System', 'Login functionality will be implemented soon.', 'assistant');
        });
    }
    
    handleChatClick() {
        this.toggleChat();
    }
    
    handleOptionsClick() {
        console.log('Options button clicked');
        window.electronAPI.optionsClick().then(() => {
            // Handle options response
            this.addMessage('System', 'Options menu will be implemented soon.', 'assistant');
        });
    }
    
    toggleChat() {
        this.isChatOpen = !this.isChatOpen;
        
        if (this.isChatOpen) {
            this.chatArea.style.display = 'block';
            this.chatArea.classList.add('show');
            this.chatInput.focus();
        } else {
            this.chatArea.classList.remove('show');
            setTimeout(() => {
                this.chatArea.style.display = 'none';
            }, 300);
        }
    }
    
    handleSendMessage() {
        const message = this.chatInput.value.trim();
        if (message) {
            this.addMessage('You', message, 'user');
            this.chatInput.value = '';
            
            // Simulate AI response (replace with actual API call)
            setTimeout(() => {
                this.addMessage('Assistant', 'This is a placeholder response. Chat functionality will be integrated with your Flask backend soon.', 'assistant');
            }, 1000);
        }
    }
    
    handleChatInputKeypress(event) {
        if (event.key === 'Enter') {
            this.handleSendMessage();
        }
    }
    
    addMessage(sender, text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        messageDiv.textContent = text;
        
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
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
    }
}

// Initialize the control bar when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ControlBar();
    
    // Add a welcome message
    setTimeout(() => {
        const controlBar = new ControlBar();
        controlBar.addMessage('System', 'Welcome to Jarvus Desktop! Click the chat button to start a conversation.', 'assistant');
    }, 500);
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
        if (chatArea.style.display === 'block') {
            const controlBar = document.querySelector('.control-bar')?.__controlBar;
            if (controlBar) {
                controlBar.toggleChat();
            }
        }
    }
}); 