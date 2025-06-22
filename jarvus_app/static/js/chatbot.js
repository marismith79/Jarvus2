let selectedTools = [];

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
  
  // Load existing conversation history from backend
  async function loadHistory() {
    try {
      const res = await fetch('/chatbot/send');
      if (!res.ok) throw new Error(`Status ${res.status}`);
      const data = await res.json();
      const history = data.history || [];
  
      // clear out any old messages
      document.getElementById('chat-history').innerHTML = '';
  
      history.forEach(msg => {
        const cssRole = msg.role === 'user' ? 'user' : 'bot';
        appendMessage(cssRole, msg.content);
      });
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  }
  
  // Load available tools into the agent creation view
  function loadAvailableTools() {
    const toolListContainer = document.getElementById('agent-creation-tool-list');
    if (!toolListContainer) return; // Exit if the container isn't on the page
    
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
        // NOTE: onclick logic is now handled by event delegation in DOMContentLoaded
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
  
    // Append the user's message locally
    appendMessage('user', raw);
    inputEl.value = '';
    inputEl.focus();
  
    // Show interim "thinking…" bubble
    const thinkingMsg = appendMessage('bot', '…');
  
    const options = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: raw })
    };
  
    try {
      const res = await fetch('/chatbot/send', options);
      const data = await res.json();
      thinkingMsg.remove();
  
      if (data.error) {
        appendMessage('bot', `⚠️ Error: ${data.error}`);
        return;
      }
  
      // Re-render the entire conversation from the returned history
      if (Array.isArray(data.history)) {
        document.getElementById('chat-history').innerHTML = '';
        data.history
            .filter(msg => msg.role === 'user' || msg.role === 'assistant')  // filter by role
            .forEach(msg => {
                const cls = msg.role === 'user' ? 'user' : 'bot';
                appendMessage(cls, msg.content);
            });
      } else {
        // Fallback: just show assistant or tool responses
        if (data.assistant) appendMessage('bot', data.assistant);
      }
    } catch (err) {
      console.error('Fetch error:', err);
      thinkingMsg.remove();
      appendMessage('bot', '⚠️ Error: Failed to get response from the assistant.');
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    loadAvailableTools();
    loadHistory(); // render the stored history on page load
  
    const inputEl = document.getElementById('chat-input');
    document.getElementById('send-btn').addEventListener('click', sendCommand);
    inputEl.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        sendCommand();
      }
    });

    // Agent Creation Flow
    const newAgentBtn = document.querySelector('.new-agent-btn');
    const chatbotCard = document.querySelector('.chatbot-card');
    const agentCreationView = document.getElementById('agent-creation-view');
    const steps = agentCreationView.querySelectorAll('.creation-step');
    const nextStepBtns = agentCreationView.querySelectorAll('.next-step-btn');
    const toolListContainer = document.getElementById('agent-creation-tool-list');
    const finishCreationBtn = document.getElementById('finish-creation-btn');
    let currentStep = 0;

    newAgentBtn.addEventListener('click', () => {
        chatbotCard.style.display = 'none';
        agentCreationView.style.display = 'flex';
        steps[currentStep].classList.add('active');
    });

    nextStepBtns.forEach((btn, index) => {
        btn.addEventListener('click', () => {
            // If on the first step, add the new agent name to the dashboard list
            if (index === 0) {
                const agentNameInput = document.getElementById('agent-name');
                const agentName = agentNameInput.value.trim();
                if (agentName) {
                    const chatList = document.querySelector('.chat-list');
                    const newChatItem = document.createElement('div');
                    newChatItem.classList.add('chat-item');
                    newChatItem.textContent = agentName;
                    chatList.prepend(newChatItem);
                }
            }

            if (currentStep < steps.length - 1) {
                steps[currentStep].classList.remove('active');
                currentStep++;
                steps[currentStep].classList.add('active');
            }
        });
    });

    // Use event delegation for dynamically created tool items
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

    finishCreationBtn.addEventListener('click', () => {
        // Here you would typically send the data to the backend
        const agentName = document.getElementById('agent-name').value.trim();
        const agentDescription = document.getElementById('agent-description').value.trim();
        console.log('Creating agent:', { name: agentName, tools: selectedTools, description: agentDescription });

        // Switch back to the chatbot view
        agentCreationView.style.display = 'none';
        chatbotCard.style.display = 'flex';

        // --- Reset the creation form for next time ---
        steps.forEach(step => step.classList.remove('active'));
        currentStep = 0;
        document.getElementById('agent-name').value = '';
        document.getElementById('agent-description').value = '';
        toolListContainer.querySelectorAll('.checkmark').forEach(cm => cm.style.display = 'none');
        selectedTools = [];
    });
  });
  