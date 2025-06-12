// Store connection status
const connectedTools = {
    gmail: window.gmailConnected || false,
    notion: window.notionConnected || false,
    slack: window.slackConnected || false,
    zoom: window.zoomConnected || false
};

// Helper to append a message bubble into #chat-history
function appendMessage(who, text) {
    const history = document.getElementById('chat-history');
    const wrapper = document.createElement('div');
    wrapper.classList.add('message', who);
    
    const p = document.createElement('p');
    p.textContent = text;
    wrapper.appendChild(p);

    history.appendChild(wrapper);
    history.scrollTop = history.scrollHeight;
    
    return wrapper;
}

// Load available tools
function loadAvailableTools() {
    const toolDropdown = document.getElementById('toolDropdown');
    // Clear existing tools
    toolDropdown.innerHTML = '';
    
    // Add connected tools to dropdown
    let hasConnectedTools = false;
    
    for (const [toolName, isConnected] of Object.entries(connectedTools)) {
        if (isConnected) {
            hasConnectedTools = true;
            const toolItem = document.createElement('div');
            toolItem.classList.add('tool-item');
            toolItem.innerHTML = `
                <span>${toolName.charAt(0).toUpperCase() + toolName.slice(1)}</span>
                <span class="checkmark" style="display: none;">✓</span>
            `;
            toolItem.onclick = (e) => {
                e.stopPropagation(); // Prevent dropdown from closing
                const checkmark = toolItem.querySelector('.checkmark');
                // Toggle the checkmark visibility
                checkmark.style.display = checkmark.style.display === 'none' ? 'inline-block' : 'none';
            };
            toolDropdown.appendChild(toolItem);
        }
    }

    // If no tools are connected, show a message
    if (!hasConnectedTools) {
        const noToolsMessage = document.createElement('div');
        noToolsMessage.classList.add('tool-item');
        noToolsMessage.innerHTML = '<span>No tools connected</span>';
        toolDropdown.appendChild(noToolsMessage);
    }
}

// When user clicks "send" or presses Enter
function sendCommand() {
    const inputEl = document.getElementById('chat-input');
    const raw = inputEl.value.trim();
    if (!raw) return;

    // Hide suggestions after first message
    const suggestionsWrapper = document.getElementById('suggestions-wrapper');
    const dropdownBtn = document.querySelector('.dropdown-btn');
    suggestionsWrapper.style.display = 'none';
    dropdownBtn.style.transform = 'rotate(90deg)';

    // Append the user's message immediately
    appendMessage('user', raw);
    inputEl.value = '';
    inputEl.focus();

    // Show "thinking" message
    const thinkingMsg = appendMessage('bot', '...');

    // Use EventSource for streaming
    const eventSource = new EventSource(`/chatbot/send?message=${encodeURIComponent(raw)}`);
    let assistantResponse = '';

    eventSource.onmessage = function(event) {
        let raw = event.data;
        if (raw.startsWith('data: ')) {
            raw = raw.slice(6);
        }
        let data;
        try {
            data = JSON.parse(raw);
        } catch (e) {
            console.error('Error parsing SSE JSON:', e, raw);
            thinkingMsg.remove();
            appendMessage('bot', '⚠️ Error: Invalid response from server.');
            eventSource.close();
            return;
        }
        if (data.error) {
            console.error('Error:', data.error);
            thinkingMsg.remove();
            appendMessage('bot', `⚠️ Error: ${data.error}`);
            eventSource.close();
            return;
        }
        if (data.content) {
            assistantResponse += data.content;
            thinkingMsg.innerHTML = assistantResponse;
        }
    };

    eventSource.onerror = function(error) {
        console.error('EventSource error:', error);
        eventSource.close();
        if (!assistantResponse) {
            thinkingMsg.remove();
            appendMessage('bot', '⚠️ Error: Failed to get response from the assistant.');
        }
    };
}

// Toggle suggestions visibility
function toggleSuggestions() {
    const suggestionsWrapper = document.getElementById('suggestions-wrapper');
    const dropdownBtn = document.querySelector('.dropdown-btn');
    const isVisible = suggestionsWrapper.style.display !== 'none';
    suggestionsWrapper.style.display = isVisible ? 'none' : 'block';
    dropdownBtn.style.transform = isVisible ? 'rotate(90deg)' : 'rotate(0deg)';
}

// Insert suggestion into input
function insertSuggestion(text) {
    const input = document.getElementById('chat-input');
    input.value = text;
    input.focus();
}

// Initialize the chatbot
document.addEventListener('DOMContentLoaded', function() {
    // Load tools when page loads
    loadAvailableTools();

    // Grab DOM nodes
    const inputEl = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const toolDropdown = document.getElementById('toolDropdown');
    const atButton = document.getElementById('atButton');
    const dropdownBtn = document.querySelector('.dropdown-btn');

    // Tool selection handling
    atButton.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const dropdown = document.getElementById('toolDropdown');
        dropdown.classList.remove('hiding');
        dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        const dropdown = document.getElementById('toolDropdown');
        const toolSelector = document.querySelector('.tool-selector');
        if (!toolSelector.contains(e.target)) {
            dropdown.classList.add('hiding');
            setTimeout(() => {
                dropdown.style.display = 'none';
                dropdown.classList.remove('hiding');
            }, 150); // Match the transition duration
        }
    });

    // Event listeners
    sendBtn.addEventListener('click', sendCommand);
    inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendCommand();
        }
    });

    // Add click handler to the dropdown button
    dropdownBtn.addEventListener('click', toggleSuggestions);
});

function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat('user', message);
    messageInput.value = '';
    
    // Create and add assistant message container
    const assistantMessageId = 'msg-' + Date.now();
    const assistantMessageDiv = document.createElement('div');
    assistantMessageDiv.id = assistantMessageId;
    assistantMessageDiv.className = 'message assistant-message';
    assistantMessageDiv.innerHTML = '<div class="message-content"></div>';
    document.querySelector('.chat-messages').appendChild(assistantMessageDiv);
    
    // Create EventSource for streaming
    const eventSource = new EventSource(`/chatbot/send?message=${encodeURIComponent(message)}`);
    let assistantResponse = '';
    
    eventSource.onmessage = function(event) {
        let raw = event.data;
        // Remove 'data: ' prefix if present
        if (raw.startsWith('data: ')) {
            raw = raw.slice(6);
        }
        let data;
        try {
            data = JSON.parse(raw);
        } catch (e) {
            console.error('Error parsing SSE JSON:', e, raw);
            document.querySelector(`#${assistantMessageId} .message-content`).innerHTML = 
                `<div class="error-message">Error: Invalid response from server.</div>`;
            eventSource.close();
            return;
        }
        if (data.error) {
            console.error('Error:', data.error);
            document.querySelector(`#${assistantMessageId} .message-content`).innerHTML = 
                `<div class="error-message">Error: ${data.error}</div>`;
            eventSource.close();
            return;
        }
        if (data.content) {
            assistantResponse += data.content;
            document.querySelector(`#${assistantMessageId} .message-content`).innerHTML = 
                marked.parse(assistantResponse);
        }
    };
    
    eventSource.onerror = function(error) {
        console.error('EventSource error:', error);
        eventSource.close();
        if (!assistantResponse) {
            document.querySelector(`#${assistantMessageId} .message-content`).innerHTML = 
                '<div class="error-message">Error: Failed to get response from the assistant.</div>';
        }
    };
    
    // Scroll to bottom
    scrollToBottom();
} 