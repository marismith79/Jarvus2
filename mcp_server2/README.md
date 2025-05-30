# Selenium MCP Server

A FastAPI-based server that provides a managed Selenium WebDriver environment with browser visualization capabilities through VNC.

## Features

- Chrome browser automation with Selenium WebDriver
- Containerized environment for each browser session
- VNC visualization of browser sessions
- RESTful API for browser control
- Support for multiple concurrent sessions

## Prerequisites

- Docker
- Docker Compose
- Python 3.9+

## Setup

1. Clone the repository and navigate to the project directory:
```bash
cd mcp_server2
```

2. Build and start the server:
```bash
docker-compose up --build
```

The server will be available at:
- API: http://localhost:8000
- VNC Viewer: http://localhost:6080/vnc.html

## API Endpoints

### Create Session
```http
POST /api/v1/sessions
```
Response:
```json
{
    "session_id": "uuid",
    "vnc_url": "http://localhost:6080/vnc.html?host=localhost&port=6080&path=websockify"
}
```

### Execute Browser Action
```http
POST /api/v1/sessions/{session_id}/actions
```
Request body:
```json
{
    "type": "navigate",
    "params": {
        "url": "https://example.com"
    }
}
```

### Delete Session
```http
DELETE /api/v1/sessions/{session_id}
```

## Supported Actions

1. Navigate
```json
{
    "type": "navigate",
    "params": {
        "url": "https://example.com"
    }
}
```

2. Click
```json
{
    "type": "click",
    "params": {
        "selector": "#button-id"
    }
}
```

3. Type
```json
{
    "type": "type",
    "params": {
        "selector": "#input-id",
        "text": "Hello, World!"
    }
}
```

4. Screenshot
```json
{
    "type": "screenshot"
}
```

## Security Notes

- The server is configured for development use
- In production, implement proper authentication and authorization
- Consider implementing rate limiting and session timeouts
- Review and adjust container security settings as needed

## Troubleshooting

1. If the VNC viewer doesn't connect:
   - Ensure ports 6080 and 5900 are not in use
   - Check container logs: `docker-compose logs`

2. If browser actions fail:
   - Check the container logs for detailed error messages
   - Verify the selectors used in actions
   - Ensure the target website is accessible

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 