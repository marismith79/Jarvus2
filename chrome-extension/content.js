// Check if content script is already initialized
if (window.webActionRecorderInitialized) {
  console.log('Content script already initialized, skipping...');
  // Still handle messages even if already initialized
} else {
  window.webActionRecorderInitialized = true;
  
  let isRecording = false;
  let recordedActions = [];
  let currentUrl = '';
  let screenshotIndex = 0;
  let recordingIndicator = null;

  // Add ping handler at the beginning
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Content script received message:', request.action);
    
    if (request.action === 'ping') {
      sendResponse({ status: 'ready' });
      return true;
    }
    
    if (request.action === 'startRecording') {
      startRecording(request.globalState);
      sendResponse({ success: true });
      return true;
    } else if (request.action === 'stopRecording') {
      stopRecording();
      sendResponse({ success: true });
      return true;
    } else if (request.action === 'exportData') {
      const data = exportRecordedData();
      sendResponse({ data: data });
      return true;
    } else if (request.action === 'getRecordingState') {
      sendResponse({ isRecording: isRecording });
      return true;
    }
    
    return true;
  });

  function startRecording(globalState) {
    isRecording = true;
    currentUrl = window.location.href;
    
    // If this is part of global recording, don't reset actions
    if (!globalState) {
      recordedActions = [];
      screenshotIndex = 0;
    }
    
    // Add event listeners
    document.addEventListener('click', handleClick, true);
    document.addEventListener('input', handleInput, true);
    document.addEventListener('change', handleChange, true);
    document.addEventListener('submit', handleSubmit, true);
    
    // Add visual recording indicator
    addRecordingIndicator();
    
    // Add global recording indicator if this is global recording
    if (globalState && globalState.isRecording) {
      addGlobalRecordingIndicator();
    }
    
    console.log('🎬 Recording started on:', currentUrl);
    console.log('📊 Event listeners added for: click, input, change, submit');
    console.log('🔍 Recording indicator should be visible');
  }

  function stopRecording() {
    isRecording = false;
    
    // Remove event listeners
    document.removeEventListener('click', handleClick, true);
    document.removeEventListener('input', handleInput, true);
    document.removeEventListener('change', handleChange, true);
    document.removeEventListener('submit', handleSubmit, true);
    
    // Remove indicators
    removeRecordingIndicator();
    removeGlobalRecordingIndicator();
    
    console.log('⏹️ Recording stopped on:', currentUrl);
  }

  function addRecordingIndicator() {
    // Remove existing indicator if any
    removeRecordingIndicator();
    
    // Create recording indicator
    recordingIndicator = document.createElement('div');
    recordingIndicator.id = 'web-action-recorder-indicator';
    recordingIndicator.innerHTML = `
      <div style="
        position: fixed;
        top: 10px;
        right: 10px;
        background: #ff4444;
        color: white;
        padding: 8px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        z-index: 999999;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        gap: 6px;
      ">
        <div style="
          width: 8px;
          height: 8px;
          background: white;
          border-radius: 50%;
          animation: pulse 1s infinite;
        "></div>
        RECORDING
      </div>
      <style>
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
      </style>
    `;
    
    document.body.appendChild(recordingIndicator);
  }

  function removeRecordingIndicator() {
    if (recordingIndicator) {
      recordingIndicator.remove();
      recordingIndicator = null;
    }
  }

  function handleClick(event) {
    if (!isRecording) return;
    
    console.log('🎯 Click detected on:', event.target.tagName, event.target.id || event.target.className);
    
    const action = createEnhancedAction('click', event);
    
    // Take before screenshot
    takeScreenshot(action, 'beforeAction');
    
    recordedActions.push(action);
    
    // Send to background script for global tracking
    chrome.runtime.sendMessage({ 
      action: 'addRecordedAction', 
      recordedAction: action 
    }).catch(error => console.log('Could not send action to background:', error));
    
    // Take after screenshot and update action
    setTimeout(async () => {
      await takeScreenshot(action, 'afterAction');
      await takeElementScreenshot(action, event.target);
      
      // Update page state after action
      action.pageState.afterAction = {
        url: window.location.href,
        title: document.title,
        newElements: detectNewElements(),
        errors: captureErrors()
      };
      
      // Re-send updated action with screenshots
      chrome.runtime.sendMessage({ 
        action: 'addRecordedAction', 
        recordedAction: action 
      }).catch(error => console.log('Could not send updated action to background:', error));
    }, 200);
  }

  function handleInput(event) {
    if (!isRecording) return;
    
    console.log('⌨️ Input detected on:', event.target.tagName, event.target.id || event.target.className);
    
    const action = createEnhancedAction('input', event);
    
    // Take before screenshot
    takeScreenshot(action, 'beforeAction');
    
    recordedActions.push(action);
    
    // Send to background script for global tracking
    chrome.runtime.sendMessage({ 
      action: 'addRecordedAction', 
      recordedAction: action 
    }).catch(error => console.log('Could not send action to background:', error));
    
    // Take after screenshot and update action
    setTimeout(async () => {
      await takeScreenshot(action, 'afterAction');
      await takeElementScreenshot(action, event.target);
      
      // Update page state after action
      action.pageState.afterAction = {
        url: window.location.href,
        title: document.title,
        newElements: detectNewElements(),
        errors: captureErrors()
      };
      
      // Re-send updated action with screenshots
      chrome.runtime.sendMessage({ 
        action: 'addRecordedAction', 
        recordedAction: action 
      }).catch(error => console.log('Could not send updated action to background:', error));
    }, 200);
  }

  function handleChange(event) {
    if (!isRecording) return;
    
    const action = createEnhancedAction('change', event);
    
    // Take before screenshot
    takeScreenshot(action, 'beforeAction');
    
    recordedActions.push(action);
    
    // Send to background script for global tracking
    chrome.runtime.sendMessage({ 
      action: 'addRecordedAction', 
      recordedAction: action 
    }).catch(error => console.log('Could not send action to background:', error));
    
    // Take after screenshot and update action
    setTimeout(async () => {
      await takeScreenshot(action, 'afterAction');
      await takeElementScreenshot(action, event.target);
      
      // Update page state after action
      action.pageState.afterAction = {
        url: window.location.href,
        title: document.title,
        newElements: detectNewElements(),
        errors: captureErrors()
      };
      
      // Re-send updated action with screenshots
      chrome.runtime.sendMessage({ 
        action: 'addRecordedAction', 
        recordedAction: action 
      }).catch(error => console.log('Could not send updated action to background:', error));
    }, 200);
  }

  function handleSubmit(event) {
    if (!isRecording) return;
    
    const action = createEnhancedAction('submit', event);
    
    // Take before screenshot
    takeScreenshot(action, 'beforeAction');
    
    recordedActions.push(action);
    
    // Send to background script for global tracking
    chrome.runtime.sendMessage({ 
      action: 'addRecordedAction', 
      recordedAction: action 
    }).catch(error => console.log('Could not send action to background:', error));
    
    // Take after screenshot and update action
    setTimeout(async () => {
      await takeScreenshot(action, 'afterAction');
      await takeElementScreenshot(action, event.target);
      
      // Update page state after action
      action.pageState.afterAction = {
        url: window.location.href,
        title: document.title,
        newElements: detectNewElements(),
        errors: captureErrors()
      };
      
      // Re-send updated action with screenshots
      chrome.runtime.sendMessage({ 
        action: 'addRecordedAction', 
        recordedAction: action 
      }).catch(error => console.log('Could not send updated action to background:', error));
    }, 200);
  }

  async function takeScreenshot(action, type) {
    try {
      // Use html2canvas if available (loaded as local script)
      if (typeof html2canvas !== 'undefined') {
        const screenshot = await html2canvas(document.body, {
          width: window.innerWidth,
          height: window.innerHeight,
          scrollX: window.scrollX,
          scrollY: window.scrollY,
          useCORS: true,
          allowTaint: true
        });
        
        // Convert to base64
        const screenshotData = screenshot.toDataURL('image/png');
        
        // Add screenshot to action
        action.screenshots[type] = {
          data: screenshotData,
          filename: `screenshot_${type}_${screenshotIndex}.png`,
          timestamp: Date.now(),
          windowSize: {
            width: window.innerWidth,
            height: window.innerHeight
          }
        };
        
        screenshotIndex++;
        
        console.log(`📸 Screenshot taken: ${action.screenshots[type].filename}`);
        console.log(`📸 Screenshot data length: ${screenshotData.length} characters`);
        console.log(`📸 Screenshot data preview: ${screenshotData.substring(0, 100)}...`);
      } else {
        // Fallback to element position data
        console.log('📸 html2canvas not available, using fallback');
        takeFallbackScreenshot(action, type);
      }
      
    } catch (error) {
      console.error('Failed to take screenshot:', error);
      // Fallback to element position data
      takeFallbackScreenshot(action, type);
    }
  }

  async function takeElementScreenshot(action, element) {
    try {
      if (typeof html2canvas !== 'undefined') {
        const screenshot = await html2canvas(element, {
          useCORS: true,
          allowTaint: true
        });
        
        const screenshotData = screenshot.toDataURL('image/png');
        
        action.screenshots.elementScreenshot = {
          data: screenshotData,
          filename: `element_screenshot_${screenshotIndex}.png`,
          timestamp: Date.now(),
          elementSize: {
            width: element.offsetWidth,
            height: element.offsetHeight
          }
        };
        
        console.log(`📸 Element screenshot taken: ${action.screenshots.elementScreenshot.filename}`);
      }
    } catch (error) {
      console.error('Failed to take element screenshot:', error);
    }
  }

  function takeFallbackScreenshot(action, type) {
    const element = action.element;
    const domElement = document.evaluate(
      element.xpath, 
      document, 
      null, 
      XPathResult.FIRST_ORDERED_NODE_TYPE, 
      null
    ).singleNodeValue;
    
    if (domElement) {
      const rect = domElement.getBoundingClientRect();
      action.screenshots[type] = {
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height,
        elementVisible: rect.width > 0 && rect.height > 0,
        fallback: true
      };
    }
  }

  function getXPath(element) {
    if (element.id) {
      return `//*[@id="${element.id}"]`;
    }
    
    if (element === document.body) {
      return '/html/body';
    }
    
    let path = '';
    while (element.parentNode) {
      let index = 1;
      for (let sibling = element.previousSibling; sibling; sibling = sibling.previousSibling) {
        if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === element.tagName) {
          index++;
        }
      }
      
      const tagName = element.tagName.toLowerCase();
      path = `/${tagName}[${index}]${path}`;
      element = element.parentNode;
    }
    
    return path;
  }

  function getElementAttributes(element) {
    const attributes = {};
    for (let attr of element.attributes) {
      attributes[attr.name] = attr.value;
    }
    return attributes;
  }

  // Enhanced helper functions for better browser automation
  function getSurroundingText(element, maxLength = 50) {
    const text = element.textContent || '';
    const parentText = element.parentElement?.textContent || '';
    return {
      elementText: text.substring(0, maxLength),
      parentText: parentText.substring(0, maxLength),
      fullContext: (element.previousSibling?.textContent || '') + 
                   text + 
                   (element.nextSibling?.textContent || '')
    };
  }

  function isElementVisible(element) {
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);
    return rect.width > 0 && 
           rect.height > 0 && 
           style.visibility !== 'hidden' && 
           style.display !== 'none' &&
           rect.top >= 0 && 
           rect.left >= 0 &&
           rect.bottom <= window.innerHeight &&
           rect.right <= window.innerWidth;
  }

  function isElementClickable(element) {
    const style = window.getComputedStyle(element);
    const isDisabled = element.disabled || element.getAttribute('disabled');
    const hasPointerEvents = style.pointerEvents !== 'none';
    const isVisible = isElementVisible(element);
    return !isDisabled && hasPointerEvents && isVisible;
  }

  function getParentContext(element) {
    const parent = element.parentElement;
    if (!parent) return null;
    
    return {
      tagName: parent.tagName,
      id: parent.id,
      className: parent.className,
      role: parent.getAttribute('role'),
      ariaLabel: parent.getAttribute('aria-label')
    };
  }

  function captureFormData() {
    const forms = document.querySelectorAll('form');
    const formData = {};
    
    forms.forEach((form, index) => {
      const inputs = form.querySelectorAll('input, select, textarea');
      const data = {};
      
      inputs.forEach(input => {
        if (input.type !== 'password') { // Don't capture passwords
          data[input.name || input.id || input.className] = input.value;
        }
      });
      
      formData[`form_${index}`] = data;
    });
    
    return formData;
  }

  function detectNewElements() {
    // This would need to be implemented with a mutation observer
    // For now, return basic page structure
    return {
      totalElements: document.querySelectorAll('*').length,
      forms: document.querySelectorAll('form').length,
      buttons: document.querySelectorAll('button').length,
      inputs: document.querySelectorAll('input').length
    };
  }

  function captureErrors() {
    const errors = {
      consoleErrors: [], // Would need to capture console errors
      validationErrors: [],
      networkErrors: [],
      pageErrors: []
    };
    
    // Capture validation errors
    const invalidInputs = document.querySelectorAll(':invalid');
    invalidInputs.forEach(input => {
      errors.validationErrors.push({
        element: input.name || input.id,
        message: input.validationMessage,
        type: input.type
      });
    });
    
    // Capture visible error messages
    const errorElements = document.querySelectorAll('.error, .alert, [role="alert"]');
    errorElements.forEach(error => {
      errors.pageErrors.push({
        text: error.textContent,
        type: error.className,
        visible: isElementVisible(error)
      });
    });
    
    return errors;
  }

  function captureErrorMessages() {
    const errorMessages = [];
    const errorSelectors = [
      '.error', '.alert', '.warning', '.danger',
      '[role="alert"]', '[aria-invalid="true"]',
      '.error-message', '.validation-error'
    ];
    
    errorSelectors.forEach(selector => {
      const elements = document.querySelectorAll(selector);
      elements.forEach(element => {
        if (isElementVisible(element)) {
          errorMessages.push({
            text: element.textContent?.trim(),
            type: selector,
            element: element.tagName
          });
        }
      });
    });
    
    return errorMessages;
  }

  function captureValidationErrors() {
    const validationErrors = [];
    const invalidInputs = document.querySelectorAll(':invalid');
    
    invalidInputs.forEach(input => {
      validationErrors.push({
        element: input.name || input.id || input.className,
        message: input.validationMessage,
        type: input.type,
        value: input.type === 'password' ? '[HIDDEN]' : input.value
      });
    });
    
    return validationErrors;
  }

  function captureNetworkErrors() {
    // This would need to be implemented with a service worker or network monitoring
    // For now, return empty array
    return [];
  }

  function capturePageErrors() {
    const pageErrors = [];
    const errorElements = document.querySelectorAll('.error, .alert, .warning, [role="alert"]');
    
    errorElements.forEach(element => {
      if (isElementVisible(element)) {
        pageErrors.push({
          text: element.textContent?.trim(),
          type: element.className,
          element: element.tagName,
          visible: true
        });
      }
    });
    
    return pageErrors;
  }

  function trackLoadingStates() {
    const loadingStates = {
      spinners: document.querySelectorAll('.spinner, .loading, [aria-busy="true"]').length,
      progressBars: document.querySelectorAll('progress, .progress').length,
      skeletonLoaders: document.querySelectorAll('.skeleton, .shimmer').length,
      disabledElements: document.querySelectorAll('[disabled], .disabled').length
    };
    
    return loadingStates;
  }

  function createEnhancedAction(type, event) {
    const action = {
      type: type,
      timestamp: Date.now(),
      sequence: recordedActions.length + 1,
      url: window.location.href,
      
      // Enhanced element data
      element: {
        tagName: event.target.tagName,
        id: event.target.id,
        className: event.target.className,
        value: event.target.value,
        xpath: getXPath(event.target),
        attributes: getElementAttributes(event.target),
        surroundingText: getSurroundingText(event.target, 50),
        ariaLabel: event.target.getAttribute('aria-label'),
        role: event.target.getAttribute('role'),
        isVisible: isElementVisible(event.target),
        isClickable: isElementClickable(event.target),
        parentContext: getParentContext(event.target),
        tabIndex: event.target.getAttribute('tabindex'),
        disabled: event.target.disabled || event.target.getAttribute('disabled')
      },
      
      // Page state
      pageState: {
        beforeAction: {
          url: window.location.href,
          title: document.title,
          formData: captureFormData(),
          scrollPosition: { x: window.scrollX, y: window.scrollY },
          viewport: { width: window.innerWidth, height: window.innerHeight }
        }
      },
      
      // Error context
      errorContext: {
        errorMessages: captureErrorMessages(),
        validationErrors: captureValidationErrors(),
        networkErrors: captureNetworkErrors(),
        pageErrors: capturePageErrors()
      },
      
      // Timing data
      timing: {
        pageLoadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
        actionDelay: 100, // Default delay
        responseTime: 0, // Will be calculated after action
        loadingStates: trackLoadingStates()
      },
      
      // Screenshots (will be added after capture)
      screenshots: {
        beforeAction: null,
        afterAction: null,
        elementScreenshot: null
      }
    };
    
    // Add position data for clicks
    if (type === 'click') {
      action.position = {
        x: event.clientX,
        y: event.clientY
      };
    }
    
    return action;
  }

  function exportRecordedData() {
    return {
      url: currentUrl,
      title: document.title,
      recordedAt: new Date().toISOString(),
      actions: recordedActions,
      summary: generateSummary()
    };
  }

  function generateSummary() {
    const clickCount = recordedActions.filter(a => a.type === 'click').length;
    const inputCount = recordedActions.filter(a => a.type === 'input').length;
    const changeCount = recordedActions.filter(a => a.type === 'change').length;
    const submitCount = recordedActions.filter(a => a.type === 'submit').length;
    
    return {
      totalActions: recordedActions.length,
      clicks: clickCount,
      inputs: inputCount,
      changes: changeCount,
      submits: submitCount,
      duration: recordedActions.length > 0 ? 
        recordedActions[recordedActions.length - 1].timestamp - recordedActions[0].timestamp : 0
    };
  }

  // Add this function to show global recording status
  function addGlobalRecordingIndicator() {
    // Remove existing indicator if any
    const existingIndicator = document.getElementById('global-recording-indicator');
    if (existingIndicator) {
      existingIndicator.remove();
    }

    // Create prominent global recording indicator
    const indicator = document.createElement('div');
    indicator.id = 'global-recording-indicator';
    indicator.style.cssText = `
      position: fixed;
      top: 10px;
      right: 10px;
      background: #ff4444;
      color: white;
      padding: 8px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: bold;
      z-index: 999999;
      box-shadow: 0 2px 10px rgba(0,0,0,0.3);
      animation: pulse 2s infinite;
      cursor: pointer;
      user-select: none;
      transition: all 0.2s ease;
    `;
    
    // Add hover effect
    indicator.addEventListener('mouseenter', () => {
      indicator.style.background = '#ff6666';
      indicator.style.transform = 'scale(1.05)';
    });
    
    indicator.addEventListener('mouseleave', () => {
      indicator.style.background = '#ff4444';
      indicator.style.transform = 'scale(1)';
    });
    
    // Add click handler to stop recording
    indicator.addEventListener('click', async (event) => {
      event.preventDefault();
      event.stopPropagation();
      
      // Show stopping feedback
      indicator.innerHTML = '⏹️ STOPPING...';
      indicator.style.background = '#ffaa00';
      indicator.style.animation = 'none';
      
      try {
        // Stop global recording
        await chrome.runtime.sendMessage({ action: 'stopGlobalRecording' });
        
        // Show success feedback
        indicator.innerHTML = '✅ STOPPED';
        indicator.style.background = '#44aa44';
        
        // Remove indicator after 2 seconds
        setTimeout(() => {
          removeGlobalRecordingIndicator();
        }, 2000);
        
        console.log('🎬 Global recording stopped by clicking indicator');
      } catch (error) {
        console.error('Error stopping global recording:', error);
        
        // Show error feedback
        indicator.innerHTML = '❌ ERROR';
        indicator.style.background = '#ff0000';
        
        // Reset to recording state after 2 seconds
        setTimeout(() => {
          indicator.innerHTML = '🔴 RECORDING';
          indicator.style.background = '#ff4444';
          indicator.style.animation = 'pulse 2s infinite';
        }, 2000);
      }
    });
    
    // Add pulse animation
    const style = document.createElement('style');
    style.textContent = `
      @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
      }
    `;
    document.head.appendChild(style);
    
    indicator.innerHTML = '🔴 RECORDING';
    document.body.appendChild(indicator);
    
    console.log('🌐 Global recording indicator added to:', window.location.href);
  }

  function removeGlobalRecordingIndicator() {
    const indicator = document.getElementById('global-recording-indicator');
    if (indicator) {
      indicator.remove();
    }
  }

  // Add this to check global recording state when page loads
  async function checkGlobalRecordingState() {
    try {
      const response = await chrome.runtime.sendMessage({ action: 'getGlobalRecordingState' });
      if (response && response.isRecording) {
        console.log('🌐 Global recording is active, starting recording on this page');
        startRecording(response);
      }
    } catch (error) {
      console.log('Could not check global recording state:', error);
    }
  }

  // Call this when content script loads
  checkGlobalRecordingState();
} 