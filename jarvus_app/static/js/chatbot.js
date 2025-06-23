let selectedTools = [];
let currentAgentId = null;

// Store connection status
const connectedTools = {
  gmail: window.gmailConnected || false,
  docs: window.docsConnected || false,
  slides: window.slidesConnected || false,
  sheets: window.sheetsConnected || false,
  drive: window.driveConnected || false,
  calendar: window.calendarConnected || false,
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
    p.innerHTML = text.replace(/\n/g, '<br>');
    wrapper.appendChild(p);
  
    history.appendChild(wrapper);
    history.scrollTop = history.scrollHeight;
  
    return wrapper;
}

// --- NEW: Agent and History Management Functions ---

async function createAgent(name, tools = [], description = '') {
    try {
        const res = await fetch('/chatbot/agents', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                name: name,
                tools: tools,
                description: description
            })
        });
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.error || `Status ${res.status}`);
        }
        const newAgent = await res.json();
        
        // Add the new agent to the top of the list
        const chatList = document.querySelector('.chat-list');
        const newChatItem = document.createElement('div');
        newChatItem.classList.add('chat-item');
        newChatItem.dataset.agentId = newAgent.id;
        newChatItem.textContent = newAgent.name;
        chatList.prepend(newChatItem);
        
        // Automatically select the new agent
        await loadAgentHistory(newAgent.id, newAgent.name);

    } catch (err) {
        console.error('Failed to create agent:', err);
        alert(`Error creating agent: ${err.message}`);
    }
}

async function loadAgentHistory(agentId, agentName = null) {
    if (!agentId) {
        document.getElementById('chat-history').innerHTML = '';
        // Reset greeting to default
        document.getElementById('agent-greeting').textContent = 'Select an agent to start chatting';
        document.getElementById('agent-subtitle').textContent = 'Choose an agent from the sidebar or create a new one';
        return;
    }
    currentAgentId = agentId;

    // Visually highlight the active agent
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.toggle('active', item.dataset.agentId == agentId);
    });

    // Update greeting with agent name
    if (agentName) {
        document.getElementById('agent-greeting').textContent = agentName;
        document.getElementById('agent-subtitle').textContent = 'How can I help you today?';
    }

    try {
        const res = await fetch(`/chatbot/agents/${agentId}/history`);
        if (!res.ok) throw new Error(`Status ${res.status}`);
        
        const data = await res.json();
        const history = data.history || [];
        
        const chatHistoryEl = document.getElementById('chat-history');
        chatHistoryEl.innerHTML = '';
  
        history.forEach(msg => {
            const cssRole = msg.role === 'user' ? 'user' : 'bot';
            appendMessage(cssRole, msg.content);
        });
    } catch (err) {
        console.error(`Failed to load history for agent ${agentId}:`, err);
    }
}

// Load available tools into the agent creation view
function loadAvailableTools() {
    const toolListContainer = document.getElementById('agent-creation-tool-list');
    if (!toolListContainer) return; 
    
    toolListContainer.innerHTML = '';
    let hasConnected = false;
  
    for (const [tool, ok] of Object.entries(connectedTools)) {
        if (ok) {
            hasConnected = true;
            const item = document.createElement('div');
            item.classList.add('tool-item');
            item.innerHTML = `
              <span>${tool[0].toUpperCase() + tool.slice(1)}</span>
              <span class="checkmark" style="display:none">✓</span>
            `;
            toolListContainer.appendChild(item);
        }
    }
  
    if (!hasConnected) {
        const msg = document.createElement('div');
        msg.classList.add('tool-item');
        msg.textContent = 'No tools connected';
        toolListContainer.appendChild(msg);
    }
}
  
// Send user message and update UI
async function sendCommand() {
    const inputEl = document.getElementById('chat-input');
    const raw = inputEl.value.trim();
    if (!raw) return;
    if (!currentAgentId) {
        alert('Please select an agent before starting a chat.');
        return;
    }
  
    appendMessage('user', raw);
    inputEl.value = '';
    inputEl.focus();
  
    const thinkingMsg = appendMessage('bot', '…');
  
    const options = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            message: raw,
            agent_id: currentAgentId 
        })
    };
  
    try {
        const res = await fetch('/chatbot/send', options);
        console.log('Raw response:', res);
        const data = await res.json();
        console.log('Parsed data:', data);
        thinkingMsg.remove();
  
        if (data.error) {
            appendMessage('bot', `⚠️ Error: ${data.error}`);
            return;
        }
  
        if (Array.isArray(data.new_messages)) {
            data.new_messages.forEach(msg => {
                const cls = msg.role === 'user' ? 'user' : 'bot';
                appendMessage(cls, msg.content);
            });
        }
    } catch (err) {
        console.error('Fetch error:', err);
        thinkingMsg.remove();
        appendMessage('bot', '⚠️ Error: Failed to get response from the assistant.');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadAvailableTools();
  
    const inputEl = document.getElementById('chat-input');
    document.getElementById('send-btn').addEventListener('click', sendCommand);
    inputEl.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        sendCommand();
      }
    });

    // --- Agent Creation and Selection Flow ---
    const newAgentBtn = document.querySelector('.new-agent-btn');
    const chatbotCard = document.querySelector('.chatbot-card');
    const agentCreationView = document.getElementById('agent-creation-view');
    const steps = agentCreationView.querySelectorAll('.creation-step');
    const nextStepBtns = agentCreationView.querySelectorAll('.next-step-btn');
    const toolListContainer = document.getElementById('agent-creation-tool-list');
    const finishCreationBtn = document.getElementById('finish-creation-btn');
    const chatList = document.querySelector('.chat-list');
    let currentStep = 0;

    newAgentBtn.addEventListener('click', () => {
        chatbotCard.style.display = 'none';
        agentCreationView.style.display = 'flex';
        steps[currentStep].classList.add('active');
    });

    nextStepBtns.forEach((btn, index) => {
        btn.addEventListener('click', async () => {
            if (index === 0) {
                const agentNameInput = document.getElementById('agent-name');
                const agentName = agentNameInput.value.trim();
                if (!agentName) {
                    alert('Please enter a name for the agent.');
                    return;
                }
                // Don't create agent yet - just move to next step
            }

            if (currentStep < steps.length - 1) {
                steps[currentStep].classList.remove('active');
                currentStep++;
                steps[currentStep].classList.add('active');
            }
        });
    });

    chatList.addEventListener('click', e => {
        const item = e.target.closest('.chat-item');
        if (item) {
            const agentId = item.dataset.agentId;
            const agentName = item.textContent.trim();
            loadAgentHistory(agentId, agentName);
        }
    });
    
    toolListContainer.addEventListener('click', e => {
        const item = e.target.closest('.tool-item');
        if (!item || item.textContent === 'No tools connected') return;

        e.stopPropagation();
        const cm = item.querySelector('.checkmark');
        cm.style.display = cm.style.display === 'none' ? 'inline-block' : 'none';
        const name = item.querySelector('span').textContent.toLowerCase();
        if (selectedTools.includes(name)) {
            selectedTools = selectedTools.filter(x => x !== name);
        } else {
            selectedTools.push(name);
        }
    });

    finishCreationBtn.addEventListener('click', async () => {
        const agentName = document.getElementById('agent-name').value.trim();
        const agentDescription = document.getElementById('agent-description').value.trim();
        
        if (agentName) {
            await createAgent(agentName, selectedTools, agentDescription);
            
            // Switch back to chat view
            agentCreationView.style.display = 'none';
            chatbotCard.style.display = 'flex';
            
            // Reset form
            steps.forEach(step => step.classList.remove('active'));
            currentStep = 0;
            document.getElementById('agent-name').value = '';
            document.getElementById('agent-description').value = '';
            toolListContainer.querySelectorAll('.checkmark').forEach(cm => cm.style.display = 'none');
            selectedTools = [];
        } else {
            alert('Please enter a name for the agent.');
        }
    });
});
