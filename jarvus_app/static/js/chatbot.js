let selectedTools = [];
let currentAgentId = null;
let currentTask = null;

// Store connection status dynamically from window.toolSlugs
const connectedTools = {};
if (window.toolSlugs) {
  window.toolSlugs.forEach(slug => {
    const varName = slug + 'Connected';
    connectedTools[slug] = window[varName] || false;
  });
}
  
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

// Helper to append a message bubble into #chat-history
function appendMessage(who, text) {
    safeLog(`appendMessage called - who: ${who}, text length: ${text ? text.length : 0}`);
    const history = document.getElementById('chat-history');
    const wrapper = document.createElement('div');
    wrapper.classList.add('message', who);
  
    const p = document.createElement('p');
    if (who === 'bot' && window.marked) {
        // Render markdown for bot replies
        p.innerHTML = window.marked.parse(text);
    } else {
        // Render plain text with line breaks for user
        p.innerHTML = text.replace(/\n/g, '<br>');
    }
    wrapper.appendChild(p);
  
    history.appendChild(wrapper);
    history.scrollTop = history.scrollHeight;
    
    safeLog(`Message appended successfully - wrapper:`, wrapper);
  
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
        
        // Create the agent name span
        const agentName = document.createElement('span');
        agentName.classList.add('agent-name');
        agentName.textContent = newAgent.name;
        
        // Create the delete button
        const deleteBtn = document.createElement('button');
        deleteBtn.classList.add('delete-agent-btn');
        deleteBtn.title = 'Delete agent';
        deleteBtn.onclick = () => deleteAgent(newAgent.id);
        deleteBtn.innerHTML = `
            <svg class="trash-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `;
        
        // Append elements to the chat item
        newChatItem.appendChild(agentName);
        newChatItem.appendChild(deleteBtn);
        
        chatList.prepend(newChatItem);
        
        // Automatically select the new agent
        await loadAgentHistory(newAgent.id, newAgent.name);

    } catch (err) {
        safeError('Failed to create agent:', err);
        alert(`Error creating agent: ${err.message}`);
    }
}

async function loadAgentHistory(agentId, agentName = null) {
    if (!agentId) {
        document.getElementById('chat-history').innerHTML = '';
        // Reset greeting to default
        updateGreeting('Select an agent to start chatting', 'Choose an agent from the sidebar or create a new one');
        return;
    }
    currentAgentId = agentId;

    // Visually highlight the active agent
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.toggle('active', item.dataset.agentId == agentId);
    });

    // Update greeting with agent name
    if (agentName) {
        updateGreeting(`${agentName}`, `Ready to help you with your tasks`);
    } else {
        // If no agent name provided, try to get it from the DOM
        const activeItem = document.querySelector(`.chat-item[data-agent-id="${agentId}"]`);
        if (activeItem) {
            const nameElement = activeItem.querySelector('.agent-name');
            if (nameElement) {
                updateGreeting(`Chat with ${nameElement.textContent}`, `Ready to help you with your tasks`);
            }
        }
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
        safeError(`Failed to load history for agent ${agentId}:`, err);
    }
}

function updateGreeting(title, subtitle) {
    const greetingTitle = document.getElementById('agent-greeting');
    const greetingSubtitle = document.getElementById('agent-subtitle');
    
    if (greetingTitle) {
        greetingTitle.textContent = title;
    }
    if (greetingSubtitle) {
        greetingSubtitle.textContent = subtitle;
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
  
    // Get the web search toggle state
    const webSearchToggle = document.getElementById('web-search-toggle');
    const webSearchEnabled = webSearchToggle ? webSearchToggle.checked : true;

    const options = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            message: raw,
            agent_id: currentAgentId,
            web_search_enabled: webSearchEnabled
        })
    };
  
    try {
        const res = await fetch('/chatbot/send', options);
        safeLog('Raw response:', res);
        const data = await res.json();
        safeLog('Parsed data:', data);
        safeLog('Response content:', data.response);
        safeLog('Response length:', data.response ? data.response.length : 0);
        thinkingMsg.remove();

        if (data.error) {
            safeLog('Error in response:', data.error);
            appendMessage('bot', `⚠️ Error: ${data.error}`);
            return;
        }

        // Updated: handle new response format
        if (data.response) {
            safeLog('Appending bot message:', data.response.substring(0, 100) + '...');
            appendMessage('bot', data.response);
        } else if (Array.isArray(data.new_messages)) {
            safeLog('Processing new_messages array:', data.new_messages);
            data.new_messages.forEach(msg => {
                if (typeof msg === 'string') {
                    appendMessage('bot', msg);
                } else if (msg.role && msg.content) {
                    const cls = msg.role === 'user' ? 'user' : 'bot';
                    appendMessage(cls, msg.content);
                }
            });
        } else {
            safeLog('No response or new_messages found in data:', data);
        }
    } catch (err) {
        safeError('Fetch error:', err);
        thinkingMsg.remove();
        appendMessage('bot', '⚠️ Error: Failed to get response from the assistant.');
    }
}

async function deleteAgent(agentId) {
    if (!confirm('Are you sure you want to delete this agent? This action cannot be undone.')) {
        return;
    }
    
    try {
        const res = await fetch(`/chatbot/agents/${agentId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.error || `Status ${res.status}`);
        }
        
        // Remove from UI
        const chatItem = document.querySelector(`.chat-item[data-agent-id="${agentId}"]`);
        if (chatItem) {
            chatItem.remove();
        }
        
        // If this was the currently selected agent, clear the chat
        if (currentAgentId == agentId) {
            await loadAgentHistory(null);
        }
        
        // Show success message
        alert('Agent deleted successfully');
        
    } catch (err) {
        safeError('Failed to delete agent:', err);
        alert(`Error deleting agent: ${err.message}`);
    }
}

// Auto-resize textarea function
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// --- NEW: Workflow Tab Management ---
function initWorkflowTabs() {
    const tabs = document.querySelectorAll('.workflow-tab');
    const sections = document.querySelectorAll('.workflow-section');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;
            
            // Remove active class from all tabs and sections
            tabs.forEach(t => t.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding section
            tab.classList.add('active');
            document.getElementById(`${targetTab}-workflows`).classList.add('active');
        });
    });
}

// --- NEW: Todo List Management ---
async function addTodoItem() {
    try {
        const response = await fetch('/chatbot/todos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: 'New task',
                completed: false
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        await loadTodos(); // Reload todos from database
        
    } catch (error) {
        safeError('Failed to add todo:', error);
        alert('Error adding todo. Please try again.');
    }
}

async function toggleTodo(checkbox) {
    const todoItem = checkbox.closest('.todo-item');
    const todoId = todoItem.dataset.todoId;
    
    try {
        const response = await fetch(`/chatbot/todos/${todoId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                completed: checkbox.checked
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Update UI
        if (checkbox.checked) {
            todoItem.classList.add('completed');
            // If completing a current task, clear it
            if (todoItem.classList.contains('current-task')) {
                await setCurrentTask(null);
            }
        } else {
            todoItem.classList.remove('completed');
        }
        
    } catch (error) {
        safeError('Failed to update todo:', error);
        // Revert checkbox state
        checkbox.checked = !checkbox.checked;
        alert('Error updating todo. Please try again.');
    }
}

async function setCurrentTask(todoId) {
    try {
        // If clicking on the same task that's already current, deselect it
        if (todoId && currentTask && currentTask.id == todoId) {
            todoId = null; // Deselect current task
        }
        
        if (todoId) {
            const response = await fetch(`/chatbot/todos/${todoId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    current_task: true
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            currentTask = data.todo;
        } else {
            // Clear all current tasks
            const response = await fetch('/chatbot/todos/clear-current', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            currentTask = null;
        }
        
        // Update UI to reflect current task
        updateCurrentTaskDisplay();
        updateTodoListCurrentTask();
        
    } catch (error) {
        safeError('Failed to set current task:', error);
        alert('Error setting current task. Please try again.');
    }
}

function updateCurrentTaskDisplay() {
    const currentTaskDisplay = document.getElementById('current-task-display');
    if (!currentTaskDisplay) return;
    
    if (currentTask) {
        currentTaskDisplay.innerHTML = `
            <div class="current-task-banner">
                <span class="current-task-icon">🎯</span>
                <span class="current-task-text">Currently working on: ${currentTask.text}</span>
                <button class="clear-current-task-btn" onclick="setCurrentTask(null)">×</button>
            </div>
        `;
        currentTaskDisplay.style.display = 'block';
    } else {
        // Show general task when no specific task is selected
        currentTaskDisplay.innerHTML = `
            <div class="current-task-banner general-task">
                <span class="current-task-icon">📋</span>
                <span class="current-task-text">Currently working on: General tasks and conversation</span>
            </div>
        `;
        currentTaskDisplay.style.display = 'block';
    }
}

function updateTodoListCurrentTask() {
    // Remove current-task class from all todos
    document.querySelectorAll('.todo-item').forEach(item => {
        item.classList.remove('current-task');
        const currentTaskBtn = item.querySelector('.current-task-btn');
        if (currentTaskBtn) {
            currentTaskBtn.classList.remove('active');
        }
    });
    
    // Add current-task class to the current task
    if (currentTask) {
        const currentTaskItem = document.querySelector(`[data-todo-id="${currentTask.id}"]`);
        if (currentTaskItem) {
            currentTaskItem.classList.add('current-task');
            const currentTaskBtn = currentTaskItem.querySelector('.current-task-btn');
            if (currentTaskBtn) {
                currentTaskBtn.classList.add('active');
            }
        }
    }
}

async function editTodo(button) {
    const todoText = button.previousElementSibling;
    const todoId = button.closest('.todo-item').dataset.todoId;
    
    todoText.contentEditable = true;
    todoText.focus();
    
    // Select all text for easy editing
    const range = document.createRange();
    range.selectNodeContents(todoText);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    
    // Save on blur
    todoText.addEventListener('blur', async function saveOnBlur() {
        todoText.removeEventListener('blur', saveOnBlur);
        await saveTodoText(todoText, todoId);
    }, { once: true });
}

async function saveTodoText(todoText, todoId) {
    todoText.contentEditable = false;
    
    try {
        const response = await fetch(`/chatbot/todos/${todoId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: todoText.textContent
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
    } catch (error) {
        safeError('Failed to save todo:', error);
        alert('Error saving todo. Please try again.');
    }
}

async function loadTodos() {
    try {
        const response = await fetch('/chatbot/todos');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const todoList = document.getElementById('todo-list');
        todoList.innerHTML = '';
        
        data.todos.forEach(todo => {
            const todoItem = document.createElement('div');
            todoItem.className = 'todo-item';
            todoItem.dataset.todoId = todo.id;
            
            if (todo.completed) todoItem.classList.add('completed');
            if (todo.current_task) {
                todoItem.classList.add('current-task');
                currentTask = todo;
            }
            
            todoItem.innerHTML = `
                <input type="checkbox" class="todo-checkbox" ${todo.completed ? 'checked' : ''} onchange="toggleTodo(this)">
                <span class="todo-text" contenteditable="true" onblur="saveTodoText(this, ${todo.id})">${todo.text}</span>
                <button class="current-task-btn ${todo.current_task ? 'active' : ''}" onclick="setCurrentTask(${todo.id})" title="Set as current task">🎯</button>
                <button class="todo-edit-btn" onclick="editTodo(this)">✏️</button>
                <button class="todo-delete-btn" onclick="deleteTodo(${todo.id})">🗑️</button>
            `;
            
            todoList.appendChild(todoItem);
        });
        
        // Update current task display after loading todos
        updateCurrentTaskDisplay();
        
    } catch (error) {
        safeError('Failed to load todos:', error);
        // Show fallback message
        const todoList = document.getElementById('todo-list');
        todoList.innerHTML = '<div class="todo-loading">Failed to load todos</div>';
    }
}

async function deleteTodo(todoId) {
    if (!confirm('Are you sure you want to delete this todo?')) {
        return;
    }
    
    try {
        const response = await fetch(`/chatbot/todos/${todoId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Remove from UI
        const todoItem = document.querySelector(`[data-todo-id="${todoId}"]`);
        if (todoItem) {
            todoItem.remove();
        }
        
    } catch (error) {
        safeError('Failed to delete todo:', error);
        alert('Error deleting todo. Please try again.');
    }
}

// --- NEW: Calendar Integration ---
async function refreshCalendar() {
    const calendarContent = document.getElementById('calendar-content');
    calendarContent.innerHTML = '<div class="calendar-loading">Loading calendar...</div>';
    
    try {
        // Hardcoded request to pull Google Calendar data using Pipedream MCP
        const response = await fetch('/chatbot/calendar', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            calendarContent.innerHTML = `<div class="calendar-loading">Error: ${data.error}</div>`;
            safeError('Calendar error:', data.error);
            return;
        }
        
        displayCalendarEvents(data.events || []);
        
    } catch (error) {
        safeError('Failed to load calendar:', error);
        calendarContent.innerHTML = '<div class="calendar-loading">Failed to load calendar</div>';
    }
}

async function debugCalendar() {
    const calendarContent = document.getElementById('calendar-content');
    calendarContent.innerHTML = '<div class="calendar-loading">Debugging calendar...</div>';
    
    try {
        const response = await fetch('/chatbot/calendar/debug', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            calendarContent.innerHTML = `<div class="calendar-loading">Debug Error: ${data.error}</div>`;
            return;
        }
        
        // Display debug information
        let debugHtml = '<div class="calendar-debug">';
        debugHtml += `<h4>Calendar Debug Info</h4>`;
        debugHtml += `<p><strong>User ID:</strong> ${data.user_id}</p>`;
        debugHtml += `<p><strong>App:</strong> ${data.app_slug}</p>`;
        debugHtml += `<p><strong>Timestamp:</strong> ${data.timestamp}</p>`;
        
        if (data.available_tools) {
            debugHtml += `<p><strong>Available Tools (${data.tool_count}):</strong></p>`;
            debugHtml += '<ul>';
            data.available_tools.forEach(tool => {
                debugHtml += `<li>${tool}</li>`;
            });
            debugHtml += '</ul>';
            
            if (data.event_tools && data.event_tools.length > 0) {
                debugHtml += `<p><strong>Event Tools:</strong> ${data.event_tools.join(', ')}</p>`;
            }
            
            if (data.list_tools && data.list_tools.length > 0) {
                debugHtml += `<p><strong>List Tools:</strong> ${data.list_tools.join(', ')}</p>`;
            }
        } else {
            debugHtml += `<p><strong>Error:</strong> ${data.error || 'No tools available'}</p>`;
        }
        
        if (data.auth_headers_available !== undefined) {
            debugHtml += `<p><strong>Auth Headers:</strong> ${data.auth_headers_available ? 'Available' : 'Not available'}</p>`;
            if (data.auth_keys) {
                debugHtml += `<p><strong>Auth Keys:</strong> ${data.auth_keys.join(', ')}</p>`;
            }
        }
        
        if (data.auth_error) {
            debugHtml += `<p><strong>Auth Error:</strong> ${data.auth_error}</p>`;
        }
        
        debugHtml += '</div>';
        calendarContent.innerHTML = debugHtml;
        
    } catch (error) {
        safeError('Failed to debug calendar:', error);
        calendarContent.innerHTML = '<div class="calendar-loading">Failed to debug calendar</div>';
    }
}

function displayCalendarEvents(events) {
    const calendarContent = document.getElementById('calendar-content');
    
    if (events.length === 0) {
        calendarContent.innerHTML = '<div class="calendar-loading">No events today</div>';
        return;
    }
    
    // Create Google Calendar-style layout
    const calendarHtml = createTimeGridCalendar(events);
    calendarContent.innerHTML = calendarHtml;
    
    // Add click handlers to event blocks
    const eventBlocks = calendarContent.querySelectorAll('.calendar-event-block');
    eventBlocks.forEach(block => {
        const eventData = JSON.parse(block.dataset.event);
        block.addEventListener('click', () => editCalendarEvent(eventData));
    });
}

function createTimeGridCalendar(events) {
    const hours = [];
    for (let i = 0; i < 24; i++) {
        hours.push(i);
    }
    
    // Parse and sort events by start time
    const parsedEvents = events.map(event => {
        // Use local time if available, otherwise fall back to original time
        const start = new Date(event.start_local || event.start);
        const end = new Date(event.end_local || event.end);
        const startHour = start.getHours();
        const startMinute = start.getMinutes();
        const endHour = end.getHours();
        const endMinute = end.getMinutes();
        
        // Calculate position and height
        const startPosition = (startHour + startMinute / 60) * 60; // 60px per hour
        const duration = (endHour + endMinute / 60) - (startHour + startMinute / 60);
        const height = Math.max(duration * 60, 30); // Minimum 30px height
        
        return {
            ...event,
            startTime: start,
            endTime: end,
            startPosition,
            height,
            startHour,
            startMinute,
            endHour,
            endMinute
        };
    }).sort((a, b) => a.startPosition - b.startPosition);
    
    let html = '<div class="calendar-grid">';
    
    // Create time column
    html += '<div class="time-column">';
    hours.forEach(hour => {
        const timeLabel = hour === 0 ? '12 AM' : hour === 12 ? '12 PM' : hour > 12 ? `${hour - 12} PM` : `${hour} AM`;
        html += `<div class="time-slot" style="height: 60px;">${timeLabel}</div>`;
    });
    html += '</div>';
    
    // Create events column
    html += '<div class="events-column">';
    
    // Create time grid lines
    hours.forEach(hour => {
        html += `<div class="time-grid-line" style="height: 60px;"></div>`;
    });
    
    // Add current time indicator
    const now = new Date();
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();
    const currentPosition = (currentHour + currentMinute / 60) * 60;
    
    html += `
        <div class="current-time-indicator" style="top: ${currentPosition}px;">
            <div class="current-time-dot"></div>
            <div class="current-time-line"></div>
        </div>
    `;
    
    // Add event blocks
    parsedEvents.forEach(event => {
        const startTime = event.startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const endTime = event.endTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        html += `
            <div class="calendar-event-block" 
                 style="top: ${event.startPosition}px; height: ${event.height}px;"
                 data-event='${JSON.stringify(event)}'>
                <div class="event-title">${event.title}</div>
                <div class="event-time">${startTime} - ${endTime}</div>
                ${event.location ? `<div class="event-location">📍 ${event.location}</div>` : ''}
            </div>
        `;
    });
    
    html += '</div></div>';
    
    return html;
}

function editCalendarEvent(event) {
    // This would open a modal or form to edit the calendar event
    // For now, just show an alert
    alert(`Edit event: ${event.title}\nThis would open an edit form in a real implementation.`);
}

// --- NEW: Morning Todo Generation ---
async function generateMorningTodos() {
    if (!currentAgentId) {
        safeWarn('No agent selected for morning todo generation');
        alert('Please select an agent before generating todos.');
        return;
    }
    
    // Show loading state
    const todoList = document.getElementById('todo-list');
    const originalContent = todoList.innerHTML;
    todoList.innerHTML = '<div class="todo-loading">Generating todos...</div>';
    
    try {
        const response = await fetch('/chatbot/generate-todos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                agent_id: currentAgentId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.todos && data.todos.length > 0) {
            // Reload todos from database (they're already saved there)
            await loadTodos();
            safeLog(`Generated ${data.todos.length} todos successfully`);
        } else {
            // Restore original content if no todos generated
            todoList.innerHTML = originalContent;
            safeWarn('No todos were generated');
        }
        
    } catch (error) {
        safeError('Failed to generate morning todos:', error);
        // Restore original content on error
        todoList.innerHTML = originalContent;
        alert('Error generating todos. Please try again.');
    }
}

// Check if it's morning and generate todos
function checkAndGenerateMorningTodos() {
    const now = new Date();
    const hour = now.getHours();
    
    // Generate todos between 6 AM and 10 AM if not already done today
    if (hour >= 6 && hour <= 10) {
        const lastGenerated = localStorage.getItem('jarvus_last_todo_generation');
        const today = now.toDateString();
        
        if (lastGenerated !== today) {
            generateMorningTodos();
            localStorage.setItem('jarvus_last_todo_generation', today);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadAvailableTools();
    initWorkflowTabs();
    loadTodos();
    refreshCalendar();
    // Removed automatic morning generation - now uses manual button
  
    const inputEl = document.getElementById('chat-input');
    
    // Add auto-resize functionality
    inputEl.addEventListener('input', function() {
        autoResizeTextarea(this);
    });
    
    // Handle Enter key for sending (but allow Shift+Enter for new line)
    inputEl.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendCommand();
        }
    });
    
    document.getElementById('send-btn').addEventListener('click', sendCommand);

    // --- Agent Creation and Selection Flow ---
    const newAgentBtn = document.querySelectorAll('.new-agent-btn');
    const chatbotCard = document.getElementById('main-chat-area');
    const agentCreationView = document.getElementById('agent-creation-view');
    const steps = agentCreationView.querySelectorAll('.creation-step');
    const nextStepBtns = agentCreationView.querySelectorAll('.next-step-btn');
    const toolListContainer = document.getElementById('agent-creation-tool-list');
    const finishCreationBtn = document.getElementById('finish-creation-btn');
    const chatList = document.querySelector('.chat-list');
    let currentStep = 0;

    // Show most recent agent if present
    if (window.mostRecentAgentId && window.mostRecentAgentId !== 'null') {
        if (chatbotCard) chatbotCard.style.display = 'flex';
        const emptyState = document.getElementById('empty-state');
        if (emptyState) emptyState.style.display = 'none';
        loadAgentHistory(window.mostRecentAgentId, window.mostRecentAgentName);
    } else {
        if (chatbotCard) chatbotCard.style.display = 'none';
        const emptyState = document.getElementById('empty-state');
        if (emptyState) emptyState.style.display = 'flex';
    }

    newAgentBtn.forEach(btn => btn.addEventListener('click', () => {
        if (chatbotCard) chatbotCard.style.display = 'none';
        if (document.getElementById('empty-state')) document.getElementById('empty-state').style.display = 'none';
        agentCreationView.style.display = 'flex';
        steps[currentStep].classList.add('active');
    }));

    // Add Enter key support - just trigger the appropriate button
    document.addEventListener('keydown', (e) => {
        if (agentCreationView.style.display === 'flex' && e.key === 'Enter') {
            e.preventDefault();
            
            // If we're on the last step, click the finish button
            if (currentStep === steps.length - 1) {
                finishCreationBtn.click();
            } else {
                // Otherwise, click the next step button
                nextStepBtns[currentStep].click();
            }
        }
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
            const agentName = item.querySelector('.agent-name').textContent.trim();
            if (chatbotCard) chatbotCard.style.display = 'flex';
            if (document.getElementById('empty-state')) document.getElementById('empty-state').style.display = 'none';
            agentCreationView.style.display = 'none';
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
            if (chatbotCard) chatbotCard.style.display = 'flex';
            if (document.getElementById('empty-state')) document.getElementById('empty-state').style.display = 'none';
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