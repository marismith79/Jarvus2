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
            // Map tab name to section ID
            let sectionId = '';
            switch (targetTab) {
                case 'all-workflows':
                    sectionId = 'all-workflows';
                    break;
                case 'running':
                    sectionId = 'running-workflows';
                    break;
                case 'requires-review':
                    sectionId = 'requires-review-workflows';
                    break;
                case 'recently-ran':
                    sectionId = 'recently-ran-workflows';
                    break;
                default:
                    sectionId = 'all-workflows';
            }
            const section = document.getElementById(sectionId);
            if (section) section.classList.add('active');
            // Load appropriate workflows for the selected tab
            loadWorkflowsForTab(targetTab);
        });
    });
}

// Load workflows for specific tab
async function loadWorkflowsForTab(tabName) {
    try {
        const response = await fetch('/api/workflows/status-summary');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Failed to load workflow summary');
        }
        
        const summary = data.summary;
        let workflows = [];
        
        switch (tabName) {
            case 'all-workflows':
                workflows = summary.all_workflows;
                break;
            case 'running':
                workflows = summary.running_workflows;
                break;
            case 'requires-review':
                workflows = summary.requires_review_workflows;
                break;
            case 'recently-ran':
                workflows = summary.recently_ran_workflows;
                break;
            default:
                workflows = summary.all_workflows;
        }
        
        // Display workflows in the appropriate container
        const containerId = tabName + '-workflow-list';
        const container = document.getElementById(containerId);
        if (container) {
            displayWorkflowsInContainer(workflows, container, tabName);
        }
        
    } catch (error) {
        safeError('Failed to load workflows for tab:', error);
        // Show error message in the container
        const containerId = tabName + '-workflow-list';
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '<div class="workflow-item"><div class="workflow-details"><div class="workflow-name">Error loading workflows</div><div class="workflow-desc">Please try again</div></div></div>';
        }
    }
}

// Display workflows in a specific container
function displayWorkflowsInContainer(workflows, container, tabName) {
    if (!container) return;
    
    container.innerHTML = '';
    
    if (workflows.length === 0) {
        let emptyMessage = '';
        switch (tabName) {
            case 'all-workflows':
                emptyMessage = 'No workflows yet';
                break;
            case 'running':
                emptyMessage = 'No workflows running';
                break;
            case 'requires-review':
                emptyMessage = 'No workflows require review';
                break;
            case 'recently-ran':
                emptyMessage = 'No recent workflow executions';
                break;
            default:
                emptyMessage = 'No workflows found';
        }
        
        container.innerHTML = `<div class="workflow-item"><div class="workflow-details"><div class="workflow-name">${emptyMessage}</div><div class="workflow-desc">Create your first workflow</div></div></div>`;
        return;
    }
    
    workflows.forEach(workflow => {
        const workflowItem = document.createElement('div');
        workflowItem.classList.add('workflow-item');
        workflowItem.dataset.workflowId = workflow.id;
        
        // Add status-specific styling
        if (tabName === 'running') {
            workflowItem.classList.add('running');
        } else if (tabName === 'requires-review') {
            workflowItem.classList.add('requires-review');
        }
        
        // Get tool icons for display
        const toolIcons = (workflow.required_tools || []).map(toolId => {
            const tool = AVAILABLE_TOOLS.find(t => t.id === toolId);
            return tool ? tool.icon : '🔧';
        }).join(' ');
        
        // Get trigger display text
        const triggerText = getTriggerDisplayText(workflow.trigger_type, workflow.trigger_config);
        
        // Add status indicator for running and review workflows
        let statusIndicator = '';
        if (tabName === 'running') {
            statusIndicator = '<div class="workflow-status">🔄 Running...</div>';
        } else if (tabName === 'requires-review') {
            statusIndicator = '<div class="workflow-status">⚠️ Requires Review</div>';
        }
        
        // Add click handler for viewing execution details
        workflowItem.addEventListener('click', (e) => {
            // Don't trigger if clicking on action buttons
            if (e.target.closest('.workflow-actions')) {
                return;
            }
            viewWorkflowExecutions(workflow.id, workflow.name);
        });
        
        workflowItem.innerHTML = `
            <div class="workflow-icon">⚙️</div>
            <div class="workflow-details">
                <div class="workflow-name">${workflow.name}</div>
                <div class="workflow-desc">${workflow.description || 'No description'}</div>
                <div class="workflow-meta">
                    <span class="workflow-tools">${toolIcons}</span>
                    <span class="workflow-trigger">${triggerText}</span>
                </div>
                ${statusIndicator}
            </div>
            <div class="workflow-actions">
                <button class="workflow-action-btn execute" onclick="executeWorkflow(${workflow.id})" title="Execute workflow">▶️</button>
                <button class="workflow-action-btn edit" onclick="editWorkflow(${workflow.id})" title="Edit workflow">✏️</button>
                <button class="workflow-action-btn delete" onclick="deleteWorkflow(${workflow.id})" title="Delete workflow">🗑️</button>
            </div>
        `;
        
        container.appendChild(workflowItem);
    });
}

// View workflow executions
async function viewWorkflowExecutions(workflowId, workflowName) {
    try {
        const response = await fetch(`/api/workflows/${workflowId}/executions`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Failed to load workflow executions');
        }
        
        showExecutionModal(workflowName, data.executions);
        
    } catch (error) {
        safeError('Failed to load workflow executions:', error);
        alert(`Error loading workflow executions: ${error.message}`);
    }
}

// Show execution details modal
function showExecutionModal(workflowName, executions) {
    const modal = document.getElementById('workflow-execution-modal');
    const title = document.getElementById('execution-modal-title');
    const detailsContainer = document.getElementById('execution-details');
    
    title.textContent = `Workflow Executions: ${workflowName}`;
    
    if (executions.length === 0) {
        detailsContainer.innerHTML = '<p>No executions found for this workflow.</p>';
    } else {
        // Show the most recent execution by default
        const latestExecution = executions[0];
        displayExecutionDetails(latestExecution);
        
        // If there are multiple executions, show a list
        if (executions.length > 1) {
            const executionList = document.createElement('div');
            executionList.innerHTML = '<h3>All Executions</h3>';
            
            executions.forEach((execution, index) => {
                const executionItem = document.createElement('div');
                executionItem.className = 'execution-item';
                executionItem.innerHTML = `
                    <div class="execution-item-header">
                        <span class="execution-item-title">Execution ${index + 1}</span>
                        <span class="execution-item-status ${execution.status}">${execution.status}</span>
                        <span class="execution-item-time">${formatExecutionTime(execution.start_time)}</span>
                    </div>
                `;
                executionItem.addEventListener('click', () => displayExecutionDetails(execution));
                executionList.appendChild(executionItem);
            });
            
            detailsContainer.appendChild(executionList);
        }
    }
    
    modal.style.display = 'flex';
}

// Display execution details
function displayExecutionDetails(execution) {
    const detailsContainer = document.getElementById('execution-details');
    const progressSection = document.getElementById('progress-steps-section');
    const feedbackSection = document.getElementById('feedback-section');
    
    // Set current execution ID for feedback
    currentExecutionId = execution.execution_id;
    
    // Clear previous content
    detailsContainer.innerHTML = '';
    
    // Create execution details
    const detailsHtml = `
        <div class="execution-status ${execution.status}">${execution.status.toUpperCase()}</div>
        <div class="execution-info">
            <div class="execution-info-item">
                <div class="execution-info-label">Execution ID</div>
                <div class="execution-info-value">${execution.execution_id}</div>
            </div>
            <div class="execution-info-item">
                <div class="execution-info-label">Start Time</div>
                <div class="execution-info-value">${formatExecutionTime(execution.start_time)}</div>
            </div>
            <div class="execution-info-item">
                <div class="execution-info-label">End Time</div>
                <div class="execution-info-value">${execution.end_time ? formatExecutionTime(execution.end_time) : 'N/A'}</div>
            </div>
            <div class="execution-info-item">
                <div class="execution-info-label">Duration</div>
                <div class="execution-info-value">${calculateDuration(execution.start_time, execution.end_time)}</div>
            </div>
        </div>
    `;
    
    detailsContainer.innerHTML = detailsHtml;
    
    // Show progress steps if available
    if (execution.progress_steps && execution.progress_steps.length > 0) {
        displayProgressSteps(execution.progress_steps);
        progressSection.style.display = 'block';
    } else {
        progressSection.style.display = 'none';
    }
    
    // Show feedback section for completed executions
    if (execution.status === 'completed' || execution.status === 'failed') {
        displayFeedbackSection(execution);
        feedbackSection.style.display = 'block';
    } else {
        feedbackSection.style.display = 'none';
    }
}

// Display progress steps
function displayProgressSteps(progressSteps) {
    const progressList = document.getElementById('progress-steps-list');
    
    progressList.innerHTML = '';
    
    progressSteps.forEach((step, index) => {
        const stepElement = document.createElement('div');
        stepElement.className = 'progress-step';
        stepElement.innerHTML = `
            <div class="progress-step-header">
                <span class="progress-step-number">Step ${step.step_number}</span>
                <span class="progress-step-action">${step.action}</span>
                <span class="progress-step-status ${step.status}">${step.status}</span>
            </div>
            <div class="progress-step-content">
                <div class="progress-step-input">
                    <div class="progress-step-label">Input:</div>
                    <div class="progress-step-text">${step.input}</div>
                </div>
                <div class="progress-step-output">
                    <div class="progress-step-label">Output:</div>
                    <div class="progress-step-text">${step.output}</div>
                </div>
            </div>
        `;
        progressList.appendChild(stepElement);
    });
}

// Display feedback section
function displayFeedbackSection(execution) {
    const currentFeedback = document.getElementById('current-feedback');
    const feedbackForm = document.getElementById('feedback-form');
    
    if (execution.user_feedback) {
        // Show existing feedback
        currentFeedback.innerHTML = `
            <div class="current-feedback">
                <div class="feedback-status ${execution.feedback_status}">${execution.feedback_status}</div>
                <div class="feedback-text">${execution.user_feedback}</div>
                <div class="feedback-time">${formatExecutionTime(execution.feedback_timestamp)}</div>
            </div>
        `;
        feedbackForm.style.display = 'none';
    } else {
        // Show feedback form
        currentFeedback.innerHTML = '';
        feedbackForm.style.display = 'block';
    }
}

// Submit feedback
async function submitFeedback(status) {
    const feedbackText = document.getElementById('feedback-text').value.trim();
    const executionId = currentExecutionId; // This will be set when viewing execution details
    
    if (!feedbackText) {
        alert('Please provide feedback before submitting.');
        return;
    }
    
    try {
        const response = await fetch(`/api/executions/${executionId}/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                feedback: feedbackText,
                status: status
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        if (data.success) {
            alert('Feedback submitted successfully!');
            closeExecutionModal();
            // Refresh the current tab
            const activeTab = document.querySelector('.workflow-tab.active');
            if (activeTab) {
                await loadWorkflowsForTab(activeTab.dataset.tab);
            }
        }
        
    } catch (error) {
        safeError('Failed to submit feedback:', error);
        alert(`Error submitting feedback: ${error.message}`);
    }
}

// Close execution modal
function closeExecutionModal() {
    const modal = document.getElementById('workflow-execution-modal');
    modal.style.display = 'none';
}

// Utility functions
function formatExecutionTime(timestamp) {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString();
}

function calculateDuration(startTime, endTime) {
    if (!startTime) return 'N/A';
    if (!endTime) return 'Running...';
    
    const start = new Date(startTime);
    const end = new Date(endTime);
    const duration = end - start;
    
    const minutes = Math.floor(duration / 60000);
    const seconds = Math.floor((duration % 60000) / 1000);
    
    return `${minutes}m ${seconds}s`;
}

// Global variable to track current execution ID
let currentExecutionId = null;

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
            // Ensure agentId is always an integer
            const agentId = parseInt(item.dataset.agentId, 10);
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

//─────────────────────────────────────────────────────────────────────────────
// Workflow Management Functions
//─────────────────────────────────────────────────────────────────────────────

let currentWorkflowId = null;

// Show workflow creation interface
function showWorkflowCreation(workflowId = null) {
    const workflowView = document.getElementById('workflow-creation-view');
    const title = document.getElementById('workflow-creation-title');
    const form = document.getElementById('workflow-form');
    
    currentWorkflowId = workflowId;
    
    if (workflowId) {
        // Edit mode
        title.textContent = 'Edit Workflow';
        loadWorkflowForEditing(workflowId);
    } else {
        // Create mode
        title.textContent = 'Create New Workflow';
        form.reset();
    }
    
    workflowView.style.display = 'flex';
    
    // Hide main chat area and right sidebar
    const mainChatArea = document.getElementById('main-chat-area');
    const rightSidebar = document.querySelector('.right-sidebar');
    if (mainChatArea) mainChatArea.style.display = 'none';
    if (rightSidebar) rightSidebar.style.display = 'none';
}

// Hide workflow creation interface
function hideWorkflowCreation() {
    const workflowView = document.getElementById('workflow-creation-view');
    workflowView.style.display = 'none';
    
    // Show main chat area and right sidebar
    const mainChatArea = document.getElementById('main-chat-area');
    const rightSidebar = document.querySelector('.right-sidebar');
    if (mainChatArea) mainChatArea.style.display = 'flex';
    if (rightSidebar) rightSidebar.style.display = 'flex';
    
    currentWorkflowId = null;
}

// Load workflow data for editing
async function loadWorkflowForEditing(workflowId) {
    try {
        const response = await fetch(`/api/workflows/${workflowId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const workflow = data.workflow;
        
        // Populate form fields
        document.getElementById('workflow-name').value = workflow.name || '';
        document.getElementById('workflow-description').value = workflow.description || '';
        document.getElementById('workflow-goal').value = workflow.goal || '';
        document.getElementById('workflow-instructions').value = workflow.instructions || '';
        document.getElementById('workflow-notes').value = workflow.notes || '';
        
        // Populate tool selection
        populateToolSelection(workflow.required_tools || []);
        
        // Populate trigger configuration
        document.getElementById('workflow-trigger').value = workflow.trigger_type || 'manual';
        updateTriggerConfig(workflow.trigger_type || 'manual', workflow.trigger_config || {});
        
    } catch (error) {
        safeError('Failed to load workflow for editing:', error);
        alert('Error loading workflow. Please try again.');
        hideWorkflowCreation();
    }
}

// Save workflow (create or update)
async function saveWorkflow(formData) {
    try {
        const url = currentWorkflowId 
            ? `/api/workflows/${currentWorkflowId}`
            : '/api/workflows';
        
        const method = currentWorkflowId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        safeLog('Workflow saved successfully:', data);
        
        // Reload the current active tab
        const activeTab = document.querySelector('.workflow-tab.active');
        if (activeTab) {
            await loadWorkflowsForTab(activeTab.dataset.tab);
        } else {
            await loadWorkflowsForTab('all-workflows');
        }
        
        // Hide creation view
        hideWorkflowCreation();
        
        // Show success message
        alert(currentWorkflowId ? 'Workflow updated successfully!' : 'Workflow created successfully!');
        
    } catch (error) {
        safeError('Failed to save workflow:', error);
        alert(`Error saving workflow: ${error.message}`);
    }
}

// Load workflows from the server
async function loadWorkflows() {
    try {
        // Load the initial "All Workflows" tab
        await loadWorkflowsForTab('all-workflows');
        
    } catch (error) {
        safeError('Failed to load workflows:', error);
        const container = document.getElementById('all-workflow-list');
        if (container) {
            container.innerHTML = '<div class="workflow-item"><div class="workflow-details"><div class="workflow-name">Error loading workflows</div><div class="workflow-desc">Please try again</div></div></div>';
        }
    }
}

// Display workflows in the sidebar
function displayWorkflows(workflows) {
    const workflowList = document.getElementById('workflow-list');
    if (!workflowList) return;
    
    workflowList.innerHTML = '';
    
    if (workflows.length === 0) {
        workflowList.innerHTML = '<div class="workflow-item"><div class="workflow-details"><div class="workflow-name">No workflows yet</div><div class="workflow-desc">Create your first workflow</div></div></div>';
        return;
    }
    
    workflows.forEach(workflow => {
        const workflowItem = document.createElement('div');
        workflowItem.classList.add('workflow-item');
        workflowItem.dataset.workflowId = workflow.id;
        
        // Get tool icons for display
        const toolIcons = (workflow.required_tools || []).map(toolId => {
            const tool = AVAILABLE_TOOLS.find(t => t.id === toolId);
            return tool ? tool.icon : '🔧';
        }).join(' ');
        
        // Get trigger display text
        const triggerText = getTriggerDisplayText(workflow.trigger_type, workflow.trigger_config);
        
        workflowItem.innerHTML = `
            <div class="workflow-icon">⚙️</div>
            <div class="workflow-details">
                <div class="workflow-name">${workflow.name}</div>
                <div class="workflow-desc">${workflow.description || 'No description'}</div>
                <div class="workflow-meta">
                    <span class="workflow-tools">${toolIcons}</span>
                    <span class="workflow-trigger">${triggerText}</span>
                </div>
            </div>
            <div class="workflow-actions">
                <button class="workflow-action-btn execute" onclick="executeWorkflow(${workflow.id})" title="Execute workflow">▶️</button>
                <button class="workflow-action-btn edit" onclick="editWorkflow(${workflow.id})" title="Edit workflow">✏️</button>
                <button class="workflow-action-btn delete" onclick="deleteWorkflow(${workflow.id})" title="Delete workflow">🗑️</button>
            </div>
        `;
        
        workflowList.appendChild(workflowItem);
    });
}

// Edit workflow
function editWorkflow(workflowId) {
    showWorkflowCreation(workflowId);
}

// Execute workflow
async function executeWorkflow(workflowId) {
    if (!confirm('Execute this workflow? This will use the current agent to run the workflow steps.')) {
        return;
    }
    
    try {
        // Find the active workflow tab and its container
        const activeTab = document.querySelector('.workflow-tab.active');
        let containerId = 'all-workflows-workflow-list'; // default
        if (activeTab) {
            switch (activeTab.dataset.tab) {
                case 'all-workflows':
                    containerId = 'all-workflows-workflow-list';
                    break;
                case 'running':
                    containerId = 'running-workflows-workflow-list';
                    break;
                case 'requires-review':
                    containerId = 'requires-review-workflows-workflow-list';
                    break;
                case 'recently-ran':
                    containerId = 'recently-ran-workflows-workflow-list';
                    break;
            }
        }
        const workflowList = document.getElementById(containerId);
        const workflowItem = workflowList ? workflowList.querySelector(`[data-workflow-id="${workflowId}"]`) : null;
        let originalContent = null;
        if (workflowItem) {
            originalContent = workflowItem.innerHTML;
            workflowItem.innerHTML = `
                <div class="workflow-icon">🔄</div>
                <div class="workflow-details">
                    <div class="workflow-name">Executing workflow...</div>
                    <div class="workflow-desc">Please wait</div>
                </div>
            `;
        }
        
        // Execute the workflow
        const response = await fetch(`/api/workflows/${workflowId}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                agent_id: currentAgentId  // Use current agent if available
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        safeLog('Workflow execution started:', data);
        
        // Show success message
        alert('Workflow execution started! Check the chat for progress updates.');
        
        // Switch to chat view to see the execution
        const mainChatArea = document.getElementById('main-chat-area');
        const rightSidebar = document.querySelector('.right-sidebar');
        if (mainChatArea) mainChatArea.style.display = 'flex';
        if (rightSidebar) rightSidebar.style.display = 'flex';
        
        // Hide workflow creation view if it's open
        const workflowView = document.getElementById('workflow-creation-view');
        if (workflowView) workflowView.style.display = 'none';
        
        // Add a message to the chat showing the workflow execution
        const execution = data.execution;
        const workflowName = execution.workflow_name;
        
        // Add user message showing workflow execution
        appendMessage('user', `Execute workflow: ${workflowName}`);
        
        // Add system message showing execution started
        appendMessage('bot', `🚀 **Workflow Execution Started**\n\n**Workflow:** ${workflowName}\n**Execution ID:** ${execution.execution_id}\n**Status:** ${execution.status}\n\nI'm now executing the workflow steps. You'll see the progress in the chat as I work through each step.`);
        
    } catch (error) {
        safeError('Failed to execute workflow:', error);
        alert(`Error executing workflow: ${error.message}`);
        
        // Restore original content on error
        // Only restore if workflowItem and originalContent exist
        if (typeof workflowItem !== 'undefined' && workflowItem && originalContent) {
            workflowItem.innerHTML = originalContent;
        }
    }
}

// Delete workflow
async function deleteWorkflow(workflowId) {
    if (!confirm('Are you sure you want to delete this workflow?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/workflows/${workflowId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        safeLog('Workflow deleted successfully');
        
        // Reload the current active tab
        const activeTab = document.querySelector('.workflow-tab.active');
        if (activeTab) {
            await loadWorkflowsForTab(activeTab.dataset.tab);
        } else {
            await loadWorkflowsForTab('all-workflows');
        }
        
        // Show success message
        alert('Workflow deleted successfully!');
        
    } catch (error) {
        safeError('Failed to delete workflow:', error);
        alert(`Error deleting workflow: ${error.message}`);
    }
}

// Handle workflow form submission
document.addEventListener('DOMContentLoaded', () => {
    const workflowForm = document.getElementById('workflow-form');
    if (workflowForm) {
        workflowForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = {
                name: document.getElementById('workflow-name').value.trim(),
                description: document.getElementById('workflow-description').value.trim(),
                goal: document.getElementById('workflow-goal').value.trim(),
                instructions: document.getElementById('workflow-instructions').value.trim(),
                notes: document.getElementById('workflow-notes').value.trim(),
                required_tools: getSelectedTools(),
                trigger_type: document.getElementById('workflow-trigger').value,
                trigger_config: getTriggerConfig()
            };
            
            // Validate required fields
            if (!formData.name || !formData.goal || !formData.instructions) {
                alert('Please fill in all required fields (Name, Goal, and Instructions).');
                return;
            }
            
            // Validate tool selection
            if (formData.required_tools.length === 0) {
                alert('Please select at least one tool for this workflow.');
                return;
            }
            
            await saveWorkflow(formData);
        });
    }
    
    // Initialize tool selection and trigger configuration
    initializeWorkflowForm();
    
    // Load workflows on page load
    loadWorkflows();
});

//─────────────────────────────────────────────────────────────────────────────
// Tool Selection and Trigger Configuration Functions
//─────────────────────────────────────────────────────────────────────────────

// Available tools configuration - will be populated from API
let AVAILABLE_TOOLS = [];

// Tool icons mapping
const TOOL_ICONS = {
    'web': '🌐',
    'gmail': '📧',
    'google_calendar': '📅',
    'google_docs': '📄',
    'google_sheets': '📊',
    'google_drive': '📁',
    'slack': '💬',
    'notion': '📝',
    'zoom': '📹',
    'google_slides': '📽️'
};

// Fetch available tools from API
async function fetchAvailableTools() {
    try {
        const response = await fetch('/api/workflows/available-tools');
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.available_apps) {
                // Transform the API response to match our expected format
                AVAILABLE_TOOLS = data.available_apps.map(app => ({
                    id: app.id,
                    name: app.name,
                    icon: TOOL_ICONS[app.id] || '🔧',
                    description: `${app.name} tools`,
                    tools: app.tools,
                    connected: app.connected // <-- add this line!
                }));
                return true;
            }
        }
        console.error('Failed to fetch available tools');
        return false;
    } catch (error) {
        console.error('Error fetching available tools:', error);
        return false;
    }
}

// Initialize workflow form
async function initializeWorkflowForm() {
    // Fetch available tools first
    await fetchAvailableTools();
    populateToolSelection();
    setupTriggerConfiguration();
}

// Populate tool selection grid
function populateToolSelection(selectedTools = []) {
    const toolGrid = document.getElementById('tool-selection-grid');
    if (!toolGrid) return;
    
    toolGrid.innerHTML = '';
    
    AVAILABLE_TOOLS.forEach(tool => {
        const toolItem = document.createElement('div');
        toolItem.classList.add('tool-selection-item');
        if (selectedTools.includes(tool.id)) {
            toolItem.classList.add('selected');
        }
        // Add connected/not-connected class
        if (tool.connected) {
            toolItem.classList.add('connected');
        } else {
            toolItem.classList.add('not-connected');
        }
        // Create tool details with available tools count
        const toolsCount = tool.tools ? tool.tools.length : 0;
        const toolsText = toolsCount > 0 ? ` (${toolsCount} tools available)` : '';
        
        toolItem.innerHTML = `
            <input type="checkbox" id="tool-${tool.id}" value="${tool.id}" 
                   ${selectedTools.includes(tool.id) ? 'checked' : ''} ${tool.connected ? '' : 'disabled'}>
            <div class="tool-icon">${tool.icon}</div>
            <div>
                <div class="tool-name">${tool.name}</div>
                <div class="tool-description">${tool.description}${toolsText}</div>
                ${!tool.connected ? '<div class="connect-warning">Not connected</div>' : ''}
            </div>
        `;
        // Add click handler for the entire item
        toolItem.addEventListener('click', (e) => {
            if (!tool.connected) {
                e.preventDefault();
                showConnectToolModal(tool.id, tool.name);
                return;
            }
            if (e.target.type !== 'checkbox') {
                const checkbox = toolItem.querySelector('input[type="checkbox"]');
                checkbox.checked = !checkbox.checked;
                toolItem.classList.toggle('selected', checkbox.checked);
            } else {
                toolItem.classList.toggle('selected', e.target.checked);
            }
        });
        toolGrid.appendChild(toolItem);
    });
}

// Show a modal to connect a tool
function showConnectToolModal(toolId, toolName) {
    // Remove any existing modal
    let modal = document.getElementById('connect-tool-modal');
    if (modal) modal.remove();
    modal = document.createElement('div');
    modal.id = 'connect-tool-modal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Connect ${toolName}</h2>
                <button class="close-modal-btn" onclick="document.getElementById('connect-tool-modal').remove()">×</button>
            </div>
            <div class="modal-body">
                <p>You need to connect <b>${toolName}</b> before using it in a workflow.</p>
                <button class="btn btn-primary" id="connect-tool-btn">Connect Now</button>
                <button class="btn btn-secondary" onclick="document.getElementById('connect-tool-modal').remove()">Cancel</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    document.getElementById('connect-tool-btn').onclick = function() {
        // Redirect to Pipedream connection flow (customize as needed)
        window.location.href = `/auth/connect/${toolId}`;
    };
}

// Get selected tools
function getSelectedTools() {
    const checkboxes = document.querySelectorAll('#tool-selection-grid input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

// Setup trigger configuration
function setupTriggerConfiguration() {
    const triggerSelect = document.getElementById('workflow-trigger');
    if (!triggerSelect) return;
    
    triggerSelect.addEventListener('change', (e) => {
        updateTriggerConfig(e.target.value);
    });
    
    // Initialize with manual trigger
    updateTriggerConfig('manual');
}

// Update trigger configuration based on type
function updateTriggerConfig(triggerType, existingConfig = {}) {
    const configGroup = document.getElementById('trigger-config-group');
    const configContent = document.getElementById('trigger-config-content');
    
    if (!configGroup || !configContent) return;
    
    let configHtml = '';
    
    switch (triggerType) {
        case 'scheduled':
            configHtml = `
                <div class="trigger-config-section">
                    <h4>Schedule Configuration</h4>
                    <div class="form-group">
                        <label for="schedule-frequency">Frequency</label>
                        <select id="schedule-frequency" name="frequency">
                            <option value="daily" ${existingConfig.frequency === 'daily' ? 'selected' : ''}>Daily</option>
                            <option value="weekly" ${existingConfig.frequency === 'weekly' ? 'selected' : ''}>Weekly</option>
                            <option value="monthly" ${existingConfig.frequency === 'monthly' ? 'selected' : ''}>Monthly</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="schedule-time">Time</label>
                        <input type="time" id="schedule-time" name="time" 
                               value="${existingConfig.time || '09:00'}">
                    </div>
                    <div class="form-group" id="weekly-day-group" style="display: none;">
                        <label for="schedule-day">Day of Week</label>
                        <select id="schedule-day" name="day">
                            <option value="monday" ${existingConfig.day === 'monday' ? 'selected' : ''}>Monday</option>
                            <option value="tuesday" ${existingConfig.day === 'tuesday' ? 'selected' : ''}>Tuesday</option>
                            <option value="wednesday" ${existingConfig.day === 'wednesday' ? 'selected' : ''}>Wednesday</option>
                            <option value="thursday" ${existingConfig.day === 'thursday' ? 'selected' : ''}>Thursday</option>
                            <option value="friday" ${existingConfig.day === 'friday' ? 'selected' : ''}>Friday</option>
                            <option value="saturday" ${existingConfig.day === 'saturday' ? 'selected' : ''}>Saturday</option>
                            <option value="sunday" ${existingConfig.day === 'sunday' ? 'selected' : ''}>Sunday</option>
                        </select>
                    </div>
                </div>
            `;
            break;
            
        case 'event':
            configHtml = `
                <div class="trigger-config-section">
                    <h4>Event Configuration</h4>
                    <div class="form-group">
                        <label for="event-type">Event Type</label>
                        <select id="event-type" name="event_type">
                            <option value="email_received" ${existingConfig.event_type === 'email_received' ? 'selected' : ''}>Email Received</option>
                            <option value="calendar_event" ${existingConfig.event_type === 'calendar_event' ? 'selected' : ''}>Calendar Event</option>
                            <option value="file_uploaded" ${existingConfig.event_type === 'file_uploaded' ? 'selected' : ''}>File Uploaded</option>
                            <option value="webhook" ${existingConfig.event_type === 'webhook' ? 'selected' : ''}>Webhook</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="event-filter">Event Filter (optional)</label>
                        <input type="text" id="event-filter" name="event_filter" 
                               placeholder="e.g., from:specific@email.com" 
                               value="${existingConfig.event_filter || ''}">
                    </div>
                </div>
            `;
            break;
            
        default: // manual
            configHtml = `
                <div class="trigger-config-section">
                    <h4>Manual Trigger</h4>
                    <p>This workflow will only run when you manually execute it.</p>
                </div>
            `;
    }
    
    configContent.innerHTML = configHtml;
    configGroup.style.display = 'block';
    
    // Setup additional event listeners for dynamic fields
    setupDynamicTriggerFields(triggerType);
}

// Setup dynamic trigger fields
function setupDynamicTriggerFields(triggerType) {
    if (triggerType === 'scheduled') {
        const frequencySelect = document.getElementById('schedule-frequency');
        const weeklyDayGroup = document.getElementById('weekly-day-group');
        
        if (frequencySelect && weeklyDayGroup) {
            frequencySelect.addEventListener('change', (e) => {
                weeklyDayGroup.style.display = e.target.value === 'weekly' ? 'block' : 'none';
            });
            
            // Initialize visibility
            weeklyDayGroup.style.display = frequencySelect.value === 'weekly' ? 'block' : 'none';
        }
    }
}

// Get trigger configuration
function getTriggerConfig() {
    const triggerType = document.getElementById('workflow-trigger').value;
    const config = {};
    
    switch (triggerType) {
        case 'scheduled':
            config.frequency = document.getElementById('schedule-frequency')?.value || 'daily';
            config.time = document.getElementById('schedule-time')?.value || '09:00';
            if (config.frequency === 'weekly') {
                config.day = document.getElementById('schedule-day')?.value || 'monday';
            }
            break;
            
        case 'event':
            config.event_type = document.getElementById('event-type')?.value || 'email_received';
            config.event_filter = document.getElementById('event-filter')?.value || '';
            break;
            
        default:
            // Manual trigger - no additional config needed
            break;
    }
    
    return config;
}

// Get trigger display text
function getTriggerDisplayText(triggerType, triggerConfig) {
    switch (triggerType) {
        case 'scheduled':
            const frequency = triggerConfig.frequency || 'daily';
            const time = triggerConfig.time || '09:00';
            if (frequency === 'weekly') {
                const day = triggerConfig.day || 'monday';
                return `📅 ${day} at ${time}`;
            }
            return `📅 ${frequency} at ${time}`;
            
        case 'event':
            const eventType = triggerConfig.event_type || 'email_received';
            const eventLabels = {
                'email_received': '📧 Email',
                'calendar_event': '📅 Calendar',
                'file_uploaded': '📁 File',
                'webhook': '🔗 Webhook'
            };
            return eventLabels[eventType] || '🔗 Event';
            
        default:
            return '👆 Manual';
    }
}

(function addConnectModalStyles() {
    if (document.getElementById('connect-modal-style')) return;
    const style = document.createElement('style');
    style.id = 'connect-modal-style';
    style.innerHTML = `
    .modal { position: fixed; z-index: 2000; left: 0; top: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
    .modal-content { background: #fff; border-radius: 12px; box-shadow: 0 4px 32px rgba(0,0,0,0.18); padding: 0; max-width: 400px; width: 100%; overflow: hidden; }
    .modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px; border-bottom: 1px solid #e5e7eb; background: #f9fafb; border-top-left-radius: 12px; border-top-right-radius: 12px; }
    .modal-header h2 { margin: 0; font-size: 1.2rem; color: #1f2937; }
    .close-modal-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #6b7280; padding: 0; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border-radius: 4px; }
    .close-modal-btn:hover { background-color: #f3f4f6; color: #374151; }
    .modal-body { padding: 20px; }
    .btn-primary { background: #2563eb; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 500; margin-right: 8px; cursor: pointer; }
    .btn-secondary { background: #6b7280; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 500; cursor: pointer; }
    .btn-primary:hover { background: #1d4ed8; }
    .btn-secondary:hover { background: #4b5563; }
    .tool-selection-item.not-connected { opacity: 0.6; pointer-events: auto; border: 1px dashed #f59e0b; }
    .tool-selection-item .connect-warning { color: #dc2626; font-size: 0.8em; margin-top: 4px; font-weight: 500; }
    `;
    document.head.appendChild(style);
})();