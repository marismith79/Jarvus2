# Selenium MCP Server

This is a JSON-RPC server that provides a programmatic interface to Selenium WebDriver operations. It allows you to control a Chrome browser instance through HTTP requests.

## Prerequisites

- Python 3.8 or higher
- Chrome browser installed
- ChromeDriver (automatically managed by webdriver-manager)

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

Start the server with:
```bash
python handler.py
```

The server will start on `http://localhost:8000` with two endpoints:
- `/mcp` - JSON-RPC endpoint for browser control
- `/tools` - GET endpoint that returns the available methods and their parameters

## Example Usage

### 1. Navigate to a URL
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "navigate",
    "params": {
      "url": "https://www.example.com"
    }
  }'
```

### 2. Find an Element
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "findElement",
    "params": {
      "using": "css selector",
      "value": "#search-input"
    }
  }'
```

### 3. Click an Element
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "click",
    "params": {
      "elementId": "element-id-from-findElement"
    }
  }'
```

## Available Methods

The server supports various Selenium operations including:
- Navigation (navigate, refresh, back, forward)
- Element interaction (click, sendKeys, clear)
- Element finding (findElement, findElements)
- Screenshots (takeScreenshot)
- Page information (getCurrentUrl, getTitle)
- And more...

For a complete list of available methods and their parameters, make a GET request to `/tools`.

## Error Handling

The server returns JSON-RPC compliant responses:
- Success responses include a `result` field
- Error responses include `code` and `message` fields

Common error codes:
- -32601: Method not found
- -32602: Invalid parameters
- -32000: Server error

## Notes

- The server runs Chrome in headless mode by default
- The browser instance is maintained between requests
- The browser is automatically closed when the server shuts down 