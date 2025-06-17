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
    p.textContent = text;
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
  async function loadAvailableTools() {
    const toolDropdown = document.getElementById('toolDropdown');
    // clear out any old entries
    toolDropdown.innerHTML = '';
  
    // (optional) load previously‐saved selection from server
    try {
      const res = await fetch('/chatbot/selected_tools');
      if (res.ok) {
        const data = await res.json();
        selectedTools = data.tools || [];
      }
    } catch (_) {}
  
    for (const [tool, ok] of Object.entries(connectedTools)) {
      if (!ok) continue;
      const name = tool.toLowerCase();
      const item = document.createElement('div');
      item.classList.add('tool-item');
  
      // show checkmark if already in selectedTools
      const checked = selectedTools.includes(name);
      item.innerHTML = `
        <span>${tool[0].toUpperCase() + tool.slice(1)}</span>
        <span class="checkmark" style="display:${checked ? 'inline-block' : 'none'}">✓</span>
      `;
  
      item.onclick = async e => {
        e.stopPropagation();
        const cm = item.querySelector('.checkmark');
        const nowOn = cm.style.display === 'none';
        cm.style.display = nowOn ? 'inline-block' : 'none';
  
        if (nowOn) {
          selectedTools.push(name);
        } else {
          selectedTools = selectedTools.filter(x => x !== name);
        }
  
        // persist new selection back to server
        await fetch('/chatbot/selected_tools', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tools: selectedTools })
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
  
    const tool = selectedTools;  // either "gmail" or null

    const options = {
      method: 'POST',
      headers: { 'Content-Type':'application/json' },
      body: JSON.stringify({
        message: raw,
        tool_choice: tool   // this now matches what the backend expects
      })
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
        data.history.forEach(msg => {
          const cls = msg.role === 'user' ? 'user' : 'bot';
          appendMessage(cls, msg.content);
        });
      } else {
        // Fallback: just show assistant or tool responses
        if (data.assistant) appendMessage('bot', data.assistant);
        if (Array.isArray(data.tool_responses)) {
          data.tool_responses.forEach(tr => appendMessage('bot', tr.content));
        }
      }
    } catch (err) {
      console.error('Fetch error:', err);
      thinkingMsg.remove();
      appendMessage('bot', '⚠️ Error: Failed to get response from the assistant.');
    }
  }
  
  // Toggle suggestions visibility
  function toggleSuggestions() { /* unchanged */ }
  
  // Insert suggestion into input
  function insertSuggestion(text) { /* unchanged */ }
  
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
  