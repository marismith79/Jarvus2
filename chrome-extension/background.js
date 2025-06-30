// Background service worker for Web Action Recorder
// This handles global recording state and tab management

let globalRecordingState = {
  isRecording: false,
  startTime: null,
  recordedActions: []
};

chrome.runtime.onInstalled.addListener(() => {
  console.log('Web Action Recorder extension installed');
});

// Handle tab updates (page navigation, new tabs, etc.)
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && globalRecordingState.isRecording) {
    // Page finished loading and we're recording - inject content script
    try {
      if (canInjectContentScript(tab.url)) {
        await chrome.scripting.executeScript({
          target: { tabId: tabId },
          files: ['html2canvas.min.js', 'content.js']
        });
        
        // Wait for script to initialize, then start recording
        setTimeout(async () => {
          try {
            await chrome.tabs.sendMessage(tabId, { 
              action: 'startRecording',
              globalState: globalRecordingState
            });
          } catch (error) {
            console.log('Could not start recording on new page:', error);
          }
        }, 500);
      }
    } catch (error) {
      console.log('Could not inject content script on new page:', error);
    }
  }
});

// Handle tab activation (when user switches tabs)
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  if (globalRecordingState.isRecording) {
    try {
      const tab = await chrome.tabs.get(activeInfo.tabId);
      if (canInjectContentScript(tab.url)) {
        await chrome.scripting.executeScript({
          target: { tabId: activeInfo.tabId },
          files: ['html2canvas.min.js', 'content.js']
        });
        
        setTimeout(async () => {
          try {
            await chrome.tabs.sendMessage(activeInfo.tabId, { 
              action: 'startRecording',
              globalState: globalRecordingState
            });
          } catch (error) {
            console.log('Could not start recording on activated tab:', error);
          }
        }, 500);
      }
    } catch (error) {
      console.log('Could not inject content script on activated tab:', error);
    }
  }
});

// Handle messages from popup and content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background received message:', request.action);
  
  if (request.action === 'startGlobalRecording') {
    globalRecordingState.isRecording = true;
    globalRecordingState.startTime = Date.now();
    globalRecordingState.recordedActions = [];
    
    // Start recording on all current tabs
    startRecordingOnAllTabs();
    
    // Update all tabs with recording status
    updateAllTabsWithRecordingStatus();
    
    sendResponse({ success: true });
    return true;
  }
  
  if (request.action === 'stopGlobalRecording') {
    globalRecordingState.isRecording = false;
    
    // Stop recording on all tabs
    stopRecordingOnAllTabs();
    
    // Update all tabs with recording status
    updateAllTabsWithRecordingStatus();
    
    sendResponse({ success: true });
    return true;
  }
  
  if (request.action === 'getGlobalRecordingState') {
    sendResponse(globalRecordingState);
    return true;
  }
  
  if (request.action === 'addRecordedAction') {
    if (globalRecordingState.isRecording) {
      globalRecordingState.recordedActions.push(request.recordedAction);
      console.log('Added action to global state:', request.recordedAction.type, 'on URL:', request.recordedAction.url);
    }
    sendResponse({ success: true });
    return true;
  }
  
  if (request.action === 'exportGlobalData') {
    const data = {
      recordingSession: {
        startTime: globalRecordingState.startTime,
        endTime: Date.now(),
        duration: Date.now() - globalRecordingState.startTime,
        totalActions: globalRecordingState.recordedActions.length
      },
      actions: globalRecordingState.recordedActions,
      summary: generateGlobalSummary()
    };
    sendResponse({ data: data });
    return true;
  }
  
  return true;
});

async function startRecordingOnAllTabs() {
  try {
    const tabs = await chrome.tabs.query({});
    
    for (const tab of tabs) {
      if (canInjectContentScript(tab.url)) {
        try {
          await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['html2canvas.min.js', 'content.js']
          });
          
          setTimeout(async () => {
            try {
              await chrome.tabs.sendMessage(tab.id, { 
                action: 'startRecording',
                globalState: globalRecordingState
              });
            } catch (error) {
              console.log(`Could not start recording on tab ${tab.id}:`, error);
            }
          }, 500);
        } catch (error) {
          console.log(`Could not inject content script on tab ${tab.id}:`, error);
        }
      }
    }
  } catch (error) {
    console.error('Error starting recording on all tabs:', error);
  }
}

async function stopRecordingOnAllTabs() {
  try {
    const tabs = await chrome.tabs.query({});
    
    for (const tab of tabs) {
      if (canInjectContentScript(tab.url)) {
        try {
          await chrome.tabs.sendMessage(tab.id, { action: 'stopRecording' });
        } catch (error) {
          console.log(`Could not stop recording on tab ${tab.id}:`, error);
        }
      }
    }
  } catch (error) {
    console.error('Error stopping recording on all tabs:', error);
  }
}

function canInjectContentScript(url) {
  if (!url) return false;
  
  const restrictedSchemes = ['chrome://', 'chrome-extension://', 'chrome-devtools://', 'moz-extension://'];
  return !restrictedSchemes.some(scheme => url.startsWith(scheme));
}

function generateGlobalSummary() {
  const actions = globalRecordingState.recordedActions;
  const clickCount = actions.filter(a => a.type === 'click').length;
  const inputCount = actions.filter(a => a.type === 'input').length;
  const changeCount = actions.filter(a => a.type === 'change').length;
  const submitCount = actions.filter(a => a.type === 'submit').length;
  
  return {
    totalActions: actions.length,
    clicks: clickCount,
    inputs: inputCount,
    changes: changeCount,
    submits: submitCount,
    pagesVisited: [...new Set(actions.map(a => a.url))].length
  };
}

// Add this function to update all tabs with recording status
async function updateAllTabsWithRecordingStatus() {
  try {
    const tabs = await chrome.tabs.query({});
    
    for (const tab of tabs) {
      if (canInjectContentScript(tab.url)) {
        try {
          await chrome.tabs.sendMessage(tab.id, { 
            action: 'updateRecordingStatus',
            isRecording: globalRecordingState.isRecording
          });
        } catch (error) {
          console.log(`Could not update recording status on tab ${tab.id}:`, error);
        }
      }
    }
  } catch (error) {
    console.error('Error updating tabs with recording status:', error);
  }
} 