# Jarvus Desktop App

A floating control bar desktop application built with Electron that provides quick access to Jarvus features without disrupting your workflow.

## Features

- **Floating Control Bar**: Always-on-top control bar that can be dragged horizontally
- **Click-through Design**: The app doesn't interfere with other applications
- **Cross-desktop Visibility**: Works across all macOS Spaces/desktops
- **Chat Interface**: Built-in chat functionality with a clean UI
- **Login Integration**: Ready for authentication integration
- **Options Menu**: Expandable settings and controls

## Installation

1. **Install Dependencies**:
   ```bash
   cd jarvus_desktop
   npm install
   ```

2. **Run in Development Mode**:
   ```bash
   npm run dev
   ```

3. **Build for Production**:
   ```bash
   npm run build
   ```

## Usage

### Control Bar
- **Login Button**: Access authentication features
- **Chat Button**: Toggle the chat interface
- **Options Button**: Access settings and additional features

### Keyboard Shortcuts
- `Cmd/Ctrl + Shift + C`: Toggle chat interface
- `Escape`: Close chat interface

### Dragging
- Click and drag the control bar horizontally to reposition it
- The bar is constrained to screen boundaries

## Architecture

```
jarvus_desktop/
├── main.js              # Main Electron process
├── preload.js           # Preload script for secure IPC
├── renderer/            # Frontend files
│   ├── control-bar.html # Main UI
│   ├── control-bar.css  # Styling
│   └── control-bar.js   # Frontend logic
└── package.json         # Dependencies and scripts
```

## Integration with Flask Backend

The desktop app is designed to integrate with your existing Flask application:

1. **API Integration**: The chat functionality will connect to your Flask routes
2. **Authentication**: Login will use your existing OAuth system
3. **Data Flow**: Messages and responses will flow through your Flask backend

## macOS Permissions

The app will request necessary permissions:
- **Accessibility**: For event capture and overlay functionality
- **Screen Recording**: For capturing screen content (future feature)

## Development Notes

- The app uses `alwaysOnTop` and `skipTaskbar` for a floating experience
- The window is set to be visible on all workspaces
- Click-through behavior is implemented to not interfere with other apps
- The control bar uses modern CSS with backdrop blur effects

## Next Steps

1. **Integrate Flask Backend**: Connect chat functionality to your existing routes
2. **Add Chrome Debugger**: Implement the Chrome debugger launch functionality
3. **Event Capture**: Add the full-screen event capture overlay
4. **Cross-platform**: Extend to Windows and Linux support

## Troubleshooting

If the app doesn't appear:
1. Check that Electron is properly installed
2. Ensure you're running from the `jarvus_desktop` directory
3. Check the console for any error messages

For permission issues:
1. Go to System Preferences > Security & Privacy > Privacy
2. Add the app to Accessibility and Screen Recording permissions 