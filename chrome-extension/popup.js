document.addEventListener('DOMContentLoaded', function() {
  console.log('Popup loaded, checking recording state...');
  
  const startBtn = document.getElementById('startRecord');
  const stopBtn = document.getElementById('stopRecord');
  const exportBtn = document.getElementById('exportData');
  const status = document.getElementById('status');

  // Check current recording state when popup opens
  checkGlobalRecordingState();

  startBtn.addEventListener('click', async () => {
    try {
      await chrome.runtime.sendMessage({ action: 'startGlobalRecording' });
      startBtn.classList.add('recording');
      status.textContent = 'Recording across all tabs... Click outside to close popup.';
    } catch (error) {
      console.error('Error starting global recording:', error);
      status.textContent = 'Error: Cannot start recording';
    }
  });

  stopBtn.addEventListener('click', async () => {
    try {
      await chrome.runtime.sendMessage({ action: 'stopGlobalRecording' });
      startBtn.classList.remove('recording');
      status.textContent = 'Recording stopped across all tabs';
    } catch (error) {
      console.error('Error stopping global recording:', error);
      status.textContent = 'Error: Cannot stop recording';
    }
  });

  exportBtn.addEventListener('click', async () => {
    try {
      const response = await chrome.runtime.sendMessage({ action: 'exportGlobalData' });
      
      if (response && response.data) {
        // Copy to clipboard
        navigator.clipboard.writeText(JSON.stringify(response.data, null, 2));
        status.textContent = 'Global context copied to clipboard!';
        
        // Also download as file
        const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'global-web-context.json';
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error exporting global data:', error);
      status.textContent = 'Error: Cannot export data';
    }
  });

  async function checkGlobalRecordingState() {
    try {
      const response = await chrome.runtime.sendMessage({ action: 'getGlobalRecordingState' });
      
      if (response && response.isRecording) {
        startBtn.classList.add('recording');
        status.textContent = 'Recording in progress across all tabs...';
      } else {
        startBtn.classList.remove('recording');
        status.textContent = 'Ready to record across all tabs';
      }
    } catch (error) {
      console.error('Error checking global recording state:', error);
      status.textContent = 'Error: Cannot check recording state';
    }
  }
}); 