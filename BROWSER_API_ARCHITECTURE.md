# Jarvus Browser API Architecture

## Overview

This architecture decouples browser automation from the web app by moving all Playwright and browser control logic into the Electron (desktop) side. The web app communicates with the browser via a secure local HTTP API, rather than direct Playwright calls. This approach resolves event loop, context, and security issues, and enables robust, cross-platform browser automation.

---

## Rationale

- **Event Loop Management:** No more manual event loop or async/sync bridging in Python. All browser automation is handled natively in Node.js.
- **Context Reuse:** Electron owns the browser context, so there are no conflicts between the web app and Electron.
- **Security:** The web app cannot directly control the browser process or access the user's filesystem. All browser actions are mediated by the Electron app, following [Electron security best practices](https://www.electronjs.org/docs/latest/tutorial/security).
- **Separation of Concerns:** The web app is now a pure client, and the Electron app is the privileged controller.

---

## Architecture Diagram

```
+-------------------+         HTTP API         +-------------------+
|   Web App (Flask) | <---------------------> | Electron (Node.js) |
|                   |                         |                   |
|  browser_http_client.py                      |  browser_api.js   |
|                   |                         |  Playwright       |
+-------------------+                         +-------------------+
```

---

## Key Components

- **jarvus_desktop/browser_api.js**: Express server exposing browser automation endpoints (navigate, click, type, tabs, JS, etc). Uses Playwright under the hood.
- **jarvus_app/services/browser_http_client.py**: Python HTTP client for the web app. All browser actions are performed via HTTP requests to the Electron API.
- **jarvus_app/services/tools/browser_tools.py**: Exposes browser tools to the LLM and web app, now using the HTTP client.
- **test_browser_api.py**: Test script to verify the new architecture end-to-end.

---

## Security Considerations

- **No direct Playwright or browser process access from the web app.**
- **All browser actions are mediated by Electron, which can enforce security policies.**
- **No Node.js integration in web content.**
- **Follow Electron's [security checklist](https://www.electronjs.org/docs/latest/tutorial/security).**

---

## Usage

1. **Start the Electron app** (which launches Chrome and the browser API server):
   ```sh
   cd jarvus_desktop
   npm install
   npm start
   ```
2. **Run the web app** as usual (Flask, etc).
3. **Use browser tools** in the web app or LLM as before. All browser actions are routed via HTTP to the Electron API.
4. **Test the integration**:
   ```sh
   python test_browser_api.py
   ```

---

## Extending the API

- To add new browser actions, implement a new endpoint in `browser_api.js` and add a corresponding method in `browser_http_client.py`.
- Always validate and sanitize input, and never expose raw Node.js or Electron APIs to untrusted web content.

---

## References
- [Electron Security Best Practices](https://www.electronjs.org/docs/latest/tutorial/security)
- [Electron FAQ](https://www.electronjs.org/docs/latest/faq)
- [Playwright API Docs](https://playwright.dev/docs/api/class-page#page-evaluate) 