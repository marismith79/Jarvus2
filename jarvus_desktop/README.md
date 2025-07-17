# Jarvus Desktop App

A floating control bar desktop application built with Electron that provides quick access to Jarvus features without disrupting your workflow.

## Features

- **Floating Control Bar**: Always-on-top control bar that can be dragged horizontally
- **Click-through Design**: The app doesn't interfere with other applications
- **Cross-desktop Visibility**: Works across all macOS Spaces/desktops
- **Chat Interface**: Built-in chat functionality with a clean UI
- **Login Integration**: Ready for authentication integration
- **Options Menu**: Expandable settings and controls
- **Dynamic Chrome Profile Selection**: Automatically selects the best available Chrome profile
- **Session Preservation**: Maintains recently opened tabs and browser state
- **Auto-Reconnection**: Reconnects to existing debug Chrome instances

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

### Chrome Profile Management
The app now supports dynamic Chrome profile selection:

- **Automatic Profile Selection**: Automatically finds and uses the best available Chrome profile
- **Profile Availability Checking**: Detects which profiles are locked by other Chrome instances
- **Session Preservation**: Maintains your recently opened tabs and browser state
- **Auto-Reconnection**: If you restart the app, it will reconnect to the existing debug Chrome

### Keyboard Shortcuts
- `Cmd/Ctrl + Shift + C`: Toggle chat interface
- `Escape`: Close chat interface

### Dragging
- Click and drag the control bar horizontally to reposition it
- The bar is constrained to screen boundaries

## Chrome Profile Features

### Dynamic Profile Selection
- **Smart Profile Detection**: Automatically finds available Chrome profiles
- **Primary Account Priority**: Prefers profiles with primary Google accounts
- **No Hardcoded Profiles**: Completely dynamic profile selection
- **Lock Detection**: Avoids profiles currently in use by other Chrome instances
- **Automatic Chrome Shutdown**: Shuts down non-debugger Chrome instances to free up profiles

### Session Preservation
- **Tab Restoration**: Maintains recently opened tabs
- **Browser State**: Preserves scroll positions and form data
- **Login States**: Keeps authentication sessions active
- **Configurable**: Option to enable/disable session preservation

### Auto-Reconnection
- **Persistent Debug Browser**: Debug Chrome stays running between app restarts
- **Fast Startup**: Reconnects to existing instance instead of launching new one
- **Session Continuity**: Maintains browser state across app restarts

### Chrome Management
- **Automatic Shutdown**: Shuts down non-debugger Chrome instances on startup
- **Process Verification**: Waits for Chrome processes to fully terminate
- **Cross-platform Support**: Works on macOS, Windows, and Linux
- **Safe Shutdown**: Graceful termination with timeout protection

## Testing

To test the dynamic profile functionality:

```bash
node test_dynamic_profiles.js
```

This will:
1. Discover all available Chrome profiles
2. Check which profiles are available (not locked)
3. Select the best available profile
4. Launch a debug browser with session preservation
5. Test session management features

To test the Chrome shutdown functionality:

```bash
node test_chrome_shutdown.js
```

This will:
1. Shut down non-debugger Chrome instances
2. Wait for processes to fully terminate
3. Verify no Chrome processes are running

## Architecture

```
jarvus_desktop/
├── main.js              # Main Electron process
├── preload.js           # Preload script for secure IPC
├── profile-manager.js   # Chrome profile management
├── launch_browser.js    # Browser launching with session support
├── test_dynamic_profiles.js # Test script for dynamic profiles
├── test_chrome_shutdown.js  # Test script for Chrome shutdown
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

## Chrome Profile Management API

The app exposes several APIs for profile management:

### Profile Discovery
- `getAvailableProfiles()`: Get all profiles not locked by other Chrome instances
- `isProfileAvailable(profileName)`: Check if a specific profile is available
- `getBestAvailableProfile()`: Get the best available profile (primary account first)

### Browser Launch
- `launchBrowserWithProfileAndSessions(profileName, preserveSessions)`: Launch browser with specific profile and session settings

### Session Management
- `getSessionInfo()`: Get information about current browser session
- `restoreSession()`: Restore browser session state

### Chrome Management
- `shutdownNonDebuggerChrome()`: Shut down non-debugger Chrome instances
- `waitForChromeShutdown()`: Wait for Chrome processes to fully terminate

## Troubleshooting

### No Available Profiles
If you see "No available profiles found":
1. Close all Chrome instances
2. Wait a few seconds for lock files to be removed
3. Restart the app

### Profile Locked
If a profile is locked:
1. Close Chrome instances using that profile
2. Check for Chrome processes in Activity Monitor/Task Manager
3. Force quit if necessary

### Session Not Preserved
If tabs aren't being restored:
1. Ensure session preservation is enabled
2. Check that the profile has recent browsing history
3. Verify Chrome was closed cleanly (not force quit) 