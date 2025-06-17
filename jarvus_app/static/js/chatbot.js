let selectedTools = [];


function toggleSuggestions() {
    const wrap = document.getElementById('suggestions-wrapper');
    wrap.classList.toggle('hidden');  // or toggle display style
  }

  function insertSuggestion(text) {
    const input = document.getElementById('chat-input');
    input.value = text;
    input.focus();
  }

  document.getElementById('atButton').addEventListener('click', e => {
    e.stopPropagation();
    const dd = document.getElementById('toolDropdown');
    dd.style.display = dd.style.display === 'block' ? 'none' : 'block';
  });
  // And maybe a document‐click handler to close it when clicking elsewhere
  document.addEventListener('click', () => {
    document.getElementById('toolDropdown').style.display = 'none';
  });

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
  
  // Load available tools
  function loadAvailableTools() {
    const toolDropdown = document.getElementById('toolDropdown');
    toolDropdown.innerHTML = '';
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
        item.onclick = e => {
          e.stopPropagation();
          const cm = item.querySelector('.checkmark');
          cm.style.display = cm.style.display === 'none' ? 'inline-block' : 'none';
          const name = item.querySelector('span').textContent.toLowerCase();
            if (selectedTools.includes(name)) {
                selectedTools = selectedTools.filter(x=>x!==name);
            } else {
                selectedTools.push(name);
            }
            // persist to server:
            fetch('/chatbot/selected_tools', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({tools: selectedTools})
            });
        };
        toolDropdown.appendChild(item);
      }
    }
  
    if (!hasConnected) {
      const msg = document.createElement('div');
      msg.classList.add('tool-item');
      msg.textContent = 'No tools connected';
      toolDropdown.appendChild(msg);
    }
  }
  
  function getSelectedTool() {
    const sel = document.querySelector('#toolDropdown .checkmark[style*="inline-block"]');
    return sel ? sel.parentElement.querySelector('span').textContent.toLowerCase() : null;
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
  
    // const tool = getSelectedTool();
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
        // if (Array.isArray(data.tool_responses)) {
        //   data.tool_responses.forEach(tr => appendMessage('bot', tr.content));
        // }
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
    document.querySelector('.dropdown-btn').addEventListener('click', toggleSuggestions);
    /* tool-dropdown open/close logic unchanged */
  });
  