# Jarvus: Detailed MVP Development Plan

## 1. Project Overview

Jarvus is a cross-platform AI assistant with a modern chat UI, deep macOS context integration, and automation capabilities. We focus on the **observe → contextualize → collaborate** loop: capturing user actions, building rich personal context, and fostering a trusting collaborative relationship.

### Long-Term Differentiation Strategy

Our product will focus on five key differentiators that set us apart from traditional AI tools:

**1. Deep Context Building**
- Continuously observe and learn from a broad set of user signals (app usage, file edits, clipboard, typing patterns, etc.) to build a rich, evolving model of each person's habits and workflows.

**2. Relationship-Driven Intelligence**
- Leverage that context to create an emotional rapport—remembering personal style, past approvals/rejections, tone preferences and "micro-rituals"—so the agent feels more like a trusted companion than a tool.

**3. Seamless Background Partnership**
- Operate unobtrusively alongside the user's main work, surfacing suggestions only at the right moments (e.g. after repeated actions or pauses), thereby avoiding notification fatigue and preserving flow.

**4. Proactive Suggestion Engine**
- Move from reactive "prompt-and-wait" to a feedback-driven decision loop: the agent proposes end-to-end workflows it can execute, solicits approval (thumbs up/down), and learns continuously from that feedback.

**5. Full-Task Automation**
- Go beyond "here's how" to "I can do it for you"—integrating with browser agents, Shortcuts/MCPs, and other tooling so the agent can carry out complete workflows in one click.

### MVP Foundation

This MVP builds the foundational infrastructure for these long-term capabilities:
- **Context Capture**: Active window, clipboard, browser events
- **Memory System**: Encrypted local storage for relationship building
- **Proactive Suggestions**: Basic trigger rules and feedback loops
- **Workflow Execution**: Browser-based automation capabilities
- **Relationship Signals**: Tone preferences, approval/rejection tracking

---

## 2. Architecture & Tech Stack

### Core Components

* **Electron App**

  * Renders chat UI, settings, Memory Editor, toasts.
  * Handles global hotkeys (e.g. ⌘⇧A via `electron-localshortcut`).
  * Spawns `jarvus-helper` native binary, maintains IPC.
  * Communicates with backend over HTTPS for AI, memory sync, auth.

* **Native Helper (`jarvus-helper`)**

  * **Language**: Swift (deep macOS API access).
  * **Interface**: JSON-RPC over WebSocket (`ws://localhost:4000/`).
  * **Features** (MVP):
    * **Context events**: active window + title, clipboard changes (classified: URL vs. text).
    * **Heartbeat** ping/pong for liveness.
    * **Automation**: stub "open URL" action only.
    * **Security**: localhost-only, request validation.
  * **Deferred (post-MVP)**:
    * File open/edit in `~/Documents`.
    * Complex automations (macros, AppleScript/JXA).
    * Advanced context signals (typing patterns, app usage analytics).

* **Backend (Flask or FastAPI)**

  * AI endpoints (Azure OpenAI), memory sync, user auth.
  * Stores minimal metadata, user preferences, and feedback.
  * **Future**: Advanced context modeling and relationship intelligence.

* **Browser Integration (MVP)**
  * **Only Chrome** extension for URL/title & selection capture.
  * **Deferred (post-MVP):** Safari extension, advanced web interaction patterns.

---

## 3. IPC & Communication

* **Electron Main Process**

  * Spawn helper on startup, watch for exit, auto-restart.
  * Establish WebSocket + heartbeat every 5s.
  * Forward context events (with timestamps) to renderer/UI via `ipcMain`/`ipcRenderer`.
  * Handle helper errors: show "Context unavailable" status.

* **JSON-RPC API**

  * Versioned methods with clear contract. Example:

    ```json
    { "jsonrpc": "2.0", "method": "onWindowChange", "params": { "app": "Safari", "title": "Article Title", "url": "https://...", "timestamp": 1234567890 } }
    ```
  * Validate each request, authenticate via local token.

---

## 4. Context Capture Enhancements (MVP)

* **Window Context**: Capture app name, window title.
* **Clipboard**: Detect changes; classify content (URL vs. text).
* **Deferred (post-MVP):** File System (watch open & save events in user's Documents), typing patterns, app usage analytics.
* **Heartbeat & Logging**: Heartbeat events and log all context events with timestamps for diagnostics.

---

## 5. Memory & Relationship Features

* **Encrypted Local Store**: `better-sqlite3` + encryption plugin; key in Keychain.
* **Memory Editor**:

  * List, search (by keyword/date), delete entries.
  * "Forget before [date]".
* **Micro-Rituals & Personalization**:

  * Onboarding: ask tone/style preferences (bullet vs. prose).
  * Greet by name + preference each session.
  * **Future**: Advanced relationship modeling, emotional rapport building.
* **Feedback UX**: thumbs up/down on suggestions; starred memories.
  * **Future**: Continuous learning from approval/rejection patterns.

---

## 5a. Personal Connection Strategies

To deepen the agent–user bond by leveraging captured context, implement features like:

* **Contextual Memory Reminders**: Pop up subtle notes recalling past interactions or content, e.g.:

  * "Last week you discussed **quantum algorithms**—would you like me to pull up that article again?"
  * "You read an article on productivity today; want to see your highlights?"

* **Proactive Care Prompts**: Use calendar/usage data to check in:

  * "You've been in back-to-back meetings all day—want a 5-minute break reminder?"
  * "Scheduling another task for tomorrow—your calendar is full; should I find a free slot?"

* **Adaptive Learning Suggestions**:

  * When reading technical docs, offer related tutorials or cheat-sheets: "It looks like you're editing Python; need a summary of list comprehensions?"
  * If user is revisiting a project folder, suggest past commits or notes: "Earlier you worked on Feature X—see its change log?"

* **Emotion & Tone Matching**:

  * Tailor responses to user's preferred style (concise vs. detailed) captured from past reactions.
  * Occasionally inject light, appropriate phrases: "Hope you're having a productive day!" or a personalized greeting.

* **Shared Journey Highlights**:

  * Summarize progress: "You've automated 5 workflows this week—nice work! Can I suggest another?"
  * Celebrate milestones: "Congrats on wrapping up Project Y—would you like an overview of next steps?"

These tactics let Jarvus feel like a collaborative partner—remembering, caring, and anticipating user needs through the contexts it learns.

---

## 6. Proactive Suggestion Engine

* **Trigger Rules**:

  1. Repetition: same context sequence (window+clipboard) ≥3×.
  2. Pause-and-Ask: user idle >15s after repeating an action.
* **Suggestion UI**:

  * Toast in bottom-right: "I noticed you've done X 3 times—automate?"
  * Buttons: ✔️ Yes (with dry-run toggle) | ❌ No
* **Feedback Logging**: record responses + context for tuning thresholds.
  * **Future**: Advanced learning algorithms for suggestion optimization.

---

## 7. Automation Framework (MVP)

* **Agent Capabilities**:
  * **Suggest workflows** based on observed user patterns
  * **Execute workflows** using browser/web search capabilities
  * **Web-based actions**: form filling, data extraction, web searches, navigation
  * **Browser automation**: click, type, scroll, extract content
  * **Web search integration**: query search engines, parse results

* **MVP Workflow Examples**:
  * Fill out web forms with user data
  * Search for information and extract key details
  * Navigate through multi-step web processes
  * Extract and summarize web content
  * Perform repetitive web tasks

* **Deferred (post-MVP)**:
  * OAuth-based tools (Google Workspace, Slack, etc.)
  * Complex desktop automations (AppleScript/JXA)
  * File system operations
  * Advanced workflow orchestration across multiple tools

---

## 8. Permissions & Onboarding (MVP)

* **Staged Prompts:**
  1. Accessibility (active-window) — on first run.
  2. Clipboard — on first use of suggestion.
  3. Browser automation — when agent needs to execute web actions.
  4. Files — only when needed in post-MVP.
* **Settings → Privacy**:
  * Toggle each category on/off.
  * Permission Log: review timestamped access events.

---

## 9. Testing & Metrics

* **Unit Tests**:
  * Helper: event emission, automation commands.
  * Backend: endpoints, auth, memory API.
* **Integration Tests**:
  * Electron ↔ helper IPC.
  * End-to-end: context → UI update → backend call.
* **Metrics**:
  * Context Coverage: % of events captured.
  * Trigger Precision: suggestions accepted vs. shown.
  * Workflow Success Rate: runs without errors.
  * **Future**: Relationship strength metrics, user satisfaction scores.
  * Use diagnostics export for beta debugging.

---

## 10. Packaging & Beta Release

* **Electron Builder**: package signed, notarized `.dmg` (macOS).
* **Include** helper in `extraResources`, register on install.
* **Beta Prep**:
  * Provide install instructions + test checklist:
    * Check context events in a log UI.
    * Trigger suggestions by repeating an action.
    * Run example automation in dry-run and full mode.

---

## 11. Two-Week Unified MVP Sprint Roadmap

We'll build and test a fully **unified** MVP in 10 working days, integrating Chrome extension context, native helper events, and the Electron UI into one seamless agent that lays the foundation for our long-term vision of relationship-driven intelligence.

### Week 1: Unified Context Capture

**Day 1: Chrome Extension & Helper IPC Setup**

* Scaffold Chrome Extension manifest and background script.
* In extension, listen for `tabs.onUpdated` (URL/title) and content script for `document.body.innerText`.
* Update `jarvus-helper` WebSocket server to accept extension events (`onBrowserNav`, `onPageContent`).
* Electron main: spawn helper, connect WebSocket, relay extension events via `ipcMain`.

**Day 2: Native Helper Context Capture**

* In helper, implement active-window capture (app name + title) and clipboard classification (URL vs. text).
* Emit `onWindowChange` and `onClipboardChange` events over WebSocket.
* Electron renderer: display combined context stream (browser URLs, active windows) in a debug panel.

**Day 3: Helper Enhancements (Window + Clipboard)**

* In helper, finalize active-window capture (app, title) and clipboard classification.
* Emit `onWindowChange` and `onClipboardChange` events over WebSocket.
* Electron UI: show current app/title/clipboard snippet in header and sidebar.

**Day 4: Context Buffer & Session Management**

* Implement in Electron renderer a time-segmented buffer of context events (last 30s).
* Visualize buffer for debugging: timeline view of events.
* Backend: define API to accept batched context (for future memory sync).

**Day 5: End-to-End Chat + Context Prompting**

* Chat UI: include last N context events in prompt payload to `/chat` endpoint.
* Backend: echo context tokens in AI responses for verification.
* Test full cycle: user navigates, helper emits events, Electron includes context, AI responds referencing context.

### Week 2: Agent Workflows & Execution

**Day 6: Proactive Suggestion Integration**

* Implement trigger rule combining browser + desktop context (e.g., same URL + clipboard repeat).
* Toast UI: "I noticed you've done X 3 times—automate?"
* Log user feedback (Yes/No) in memory store.

**Day 7: Agent Workflow Execution**

* Extend helper to accept `executeWorkflow` RPC with web-based actions.
* Implement browser automation: click, type, extract content, web search.
* Wire Yes toast to call `executeWorkflow` with dry-run and full execution modes.
* Show success/failure toast with execution details.

**Day 8: Onboarding & Permissions Flow**

* Build first-run wizard in Electron: install Chrome extension link, request Accessibility permission.
* Add browser automation permission request when agent needs to execute web actions.
* Helper: emit `onPermissionGranted` events; UI displays status.
* Ensure extension installs prompt and extension-to-helper handshake.

**Day 9: Memory Editor & Diagnostics Export**

* Finalize encrypted memory UI: list context snapshots and suggestion history.
* Add "Export Logs" button to dump helper and extension events for debugging.
* Test export on clean user account.

**Day 10: Packaging & Beta Release**

* Bundle Chrome extension into Electron installer or provide install scripts.
* Electron Builder: include helper and extension installers in `extraResources`.
* Notarize macOS app, build `.dmg` with extension install instructions.
* Prepare beta invite with unified install steps and test plan checklist.

---

## 12. Developer Task Assignments

To minimize overlap and allow independent workstreams, Tetsu and Shomari will each own distinct modules. They coordinate only at key handoff points.

# Two-Week MVP Sprint Assignments

## Week 1: Core & Context

| Day         | Tetsu (Native Helper & Backend) | Shomari (UI, Extensions & Memory) |
| ----------- | ------------------------------- | --------------------------------- |
| **Day 1–2** | **Native Helper Prototype**     | **Chrome Extension**    |
|             | • Scaffold `jarvus-helper` in Swift | • Chrome: listen to navigation events, grab URL/title, push via WebSocket |
|             | • Emit active-window events | • Chrome content script: capture selections & form submits |
|             | • Monitor clipboard | |
|             | • JSON-RPC over WebSocket | |
|             | • Electron spawn & IPC | |
| **Day 3–4** | **IPC & UI Context Integration** | **Chat UI Wiring** |
|             | • Forward helper events into renderer | • Show window/app info in chat header |
|             | • Add header display of current app/title | • Display "Summarize?" snippets for clipboard events |
|             | • Context event logging for debugging | • Display "Summarize page" for extension events |
|             | | • UI debug console for incoming context |
| **Day 5**   | **Local Memory Backend** | **Memory Editor UI** |
|             | • Encrypted SQLite setup (Node) with Keychain key | • Settings → Memory tab: list/search/delete entries |
|             | • Memory REST API endpoints (list, delete, forget-before) | • "Forget before [date]" control |
|             | | • Hook Memory UI to backend API |

## Week 2: Agent Workflows & Polish

| Day         | Tetsu (Agent & Workflow Engine) | Shomari (Onboarding, Polish & Packaging) |
| ----------- | ------------------------------- | ---------------------------------------- |
| **Day 6–7** | **Proactive Suggestion Engine (Backend)** | **Suggestion UI & Feedback** |
|             | • Implement rules engine for repeated context (window+clipboard) | • Toast component with Yes/No buttons |
|             | • Expose suggestion triggers via IPC to renderer | • Relay user choice back to Tetsu's engine |
|             | • Store user responses in memory | • Log feedback locally for tuning |
| **Day 8**   | **Agent Workflow Execution** | **Workflow UI** |
|             | • Implement browser automation: click, type, extract, search | • Confirmation modal for workflow parameters |
|             | • Web-based workflow execution engine | • "Dry-run" toggle and cancel button |
|             | • Execute workflows with success/failure tracking | • Success/failure toast with execution details |
| **Day 9**   | **Permissions & Diagnostics** | **Privacy Settings & Testing** |
|             | • Onboarding flow: staged prompts for Accessibility, Clipboard, Browser automation | • Permissions toggles in Settings → Privacy |
|             | • Implement helper heartbeat & crash recovery | • Permission Log view (when each API was accessed) |
|             | • Expose "export logs" endpoint for diagnostics | • Manual smoke tests on clean macOS account |
| **Day 10**  | **Metrics & Handoff** | **UI Polish & Packaging** |
|             | • Instrument core metrics: Context Coverage, Trigger Precision, Workflow Success Rate | • Refine chat bubble & toast animations |
|             | • Expose metrics endpoint in backend for UI dashboard | • Use native dialogs/notifications where possible |
|             | | • Package with Electron Builder & notarize .dmg |
|             | | • Draft beta notes |

---

### Hand-Off Checkpoints

* **End of Day 2:** Helper events successfully driving Chrome extension context.
* **End of Day 5:** Memory API is live; UI can list and delete entries.
* **End of Day 7:** Suggestions fire correctly and appear in the UI.
* **End of Day 10:** Fully packaged beta ready for testers, with agent workflow execution capabilities enabled.

### Long-Term Vision Alignment

This MVP establishes the foundational infrastructure for our five key differentiators:
1. **Deep Context Building**: Basic context capture and memory system
2. **Relationship-Driven Intelligence**: Memory storage and feedback loops
3. **Seamless Background Partnership**: Unobtrusive suggestion system
4. **Proactive Suggestion Engine**: Trigger rules and feedback collection
5. **Full-Task Automation**: Browser-based workflow execution

Post-MVP development will expand these capabilities with advanced context modeling, emotional rapport building, and comprehensive tool integration.

### Ideas
* Harnessing the power of the people that know how to do things: sharing what agents learn from others to other people's agents