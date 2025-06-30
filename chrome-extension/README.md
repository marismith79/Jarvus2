# Web Action Recorder Chrome Extension

This Chrome extension records your web actions and generates context data that can be used with the Jarvus AI web browsing tool.

## Installation

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked" and select the `chrome-extension` folder
4. The extension icon should appear in your toolbar

## Usage

1. Navigate to any website you want to record actions on
2. Click the extension icon in your toolbar
3. Click "Start Recording" to begin capturing your actions
4. **Important**: After clicking "Start Recording", you can close the popup - recording will continue
5. A red "RECORDING" indicator will appear in the top-right corner of the page
6. Perform the actions you want to record (clicks, inputs, form submissions, etc.)
7. Click the extension icon again and click "Stop Recording" when you're done
8. Click "Export Context" to download the recorded data as JSON

## What Gets Recorded

- **Clicks**: Element clicked, position, XPath selector
- **Inputs**: Text entered, element details
- **Form submissions**: Form data and element info
- **Screenshots**: Full window screenshots after each action (when possible)
- **Timestamps**: Exact timing of each action
- **Sequential order**: Actions are numbered in order of execution

## Visual Indicators

- **Red "RECORDING" badge**: Appears in the top-right corner when recording is active
- **Pulsing dot**: Indicates active recording
- **Extension icon**: Shows recording state in the toolbar

## Output Format

The exported JSON contains:
```json
{
  "url": "https://example.com",
  "actions": [
    {
      "type": "click",
      "sequence": 1,
      "timestamp": 1732686025000,
      "element": {
        "tagName": "BUTTON",
        "id": "submit-btn",
        "xpath": "//button[@id='submit-btn']"
      },
      "screenshot": {
        "data": "data:image/png;base64,...",
        "filename": "screenshot_0.png",
        "windowSize": {"width": 1920, "height": 1080}
      }
    }
  ],
  "summary": {
    "totalActions": 5,
    "clicks": 3,
    "inputs": 2,
    "duration": 5000
  }
}
```

## Using with Jarvus AI

1. Record your actions using this extension
2. Export the context data
3. Use the `recorded_actions` parameter in your web tool call:

```python
{
  "task": "Repeat the same actions I just recorded",
  "recorded_actions": [/* paste the exported actions array here */]
}
```

## Features

- ✅ Sequential action recording
- ✅ Full window screenshots (when html2canvas works)
- ✅ Element position fallback (when screenshots fail)
- ✅ XPath selectors for precise element targeting
- ✅ Element attributes and text content
- ✅ Timestamp tracking
- ✅ Export to JSON format
- ✅ Copy to clipboard functionality
- ✅ Visual recording indicator
- ✅ Persistent recording state

## Troubleshooting

- **Extension popup disappears**: This is normal! Recording continues even when the popup is closed
- **Screenshots fail**: The extension falls back to element position data
- **Recording indicator not visible**: Check if the page has high z-index elements that might cover it
- **Some websites block recording**: This is due to Content Security Policy restrictions

## Technical Notes

- Uses local html2canvas library to avoid CSP violations
- Recording state persists across popup opens/closes
- Visual indicator shows recording status on the page
- Fallback screenshot system for when html2canvas fails 