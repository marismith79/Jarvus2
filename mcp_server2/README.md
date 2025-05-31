# Selenium MCP Server

A Model Context Protocol (MCP) server that provides browser automation capabilities using Selenium WebDriver. This server follows Anthropic's Model Context Protocol specification to provide a standardized interface for AI models to interact with web browsers.

## Project Structure

```
mcp_server2/
├── app.py                 # FastAPI server implementation
├── services/
│   ├── __init__.py
│   └── browser_service.py # Selenium browser service wrapper
├── test_mcp.py           # Test script for browser automation
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile           # Docker configuration
└── requirements.txt     # Project dependencies
```

## Features

- Browser automation with Selenium WebDriver
- Containerized environment for each browser session
- Support for multiple concurrent sessions
- Comprehensive browser control actions
- Screenshot capabilities
- Tab management
- JavaScript execution

## Setup and Installation

1. Ensure you have Docker and Docker Compose installed on your system.

2. Clone the repository and navigate to the project directory:
```bash
cd mcp_server2
```

3. Build and start the containers:
```bash
docker-compose up --build
```

The server will be available at:
- API: http://localhost:8000
- Selenium Grid: http://localhost:4444

## Testing

The server includes a test script (`test_mcp.py`) that verifies the functionality of the browser automation tools. This script tests the following capabilities:

1. **Basic Browser Operations:**
   - Creating a browser session
   - Navigation to websites
   - Getting page titles
   - Finding elements
   - Executing JavaScript
   - Taking screenshots
   - Managing tabs
   - Getting window handles

2. **Screenshot Functionality:**
   - Navigates to specified websites
   - Takes screenshots
   - Saves screenshots as PNG files

To run the tests:
```bash
docker exec mcp_server2-selenium-mcp-1 python3 test_mcp.py
```

The test script will:
1. Create a browser session
2. Navigate to example.com
3. Perform various browser actions
4. Take a screenshot of dictionary.com
5. Save the screenshot as `dictionary_com_screenshot.png`
6. Clean up the session

## Available Browser Actions

### 1. Navigation
```python
{
    "type": "navigate",
    "params": {
        "url": "https://example.com"
    }
}
```

### 2. Element Finding
```python
{
    "type": "find_element",
    "params": {
        "by": "css",
        "value": "h1"
    }
}
```

### 3. JavaScript Execution
```python
{
    "type": "execute_script",
    "params": {
        "script": "return document.title;"
    }
}
```

### 4. Screenshot
```python
{
    "type": "screenshot",
    "params": {}
}
```

### 5. Tab Management
```python
{
    "type": "new_tab",
    "params": {}
}
```

## Security Notes

- The server is configured for development use
- In production, implement proper authentication and authorization
- Consider implementing rate limiting and session timeouts
- Review and adjust container security settings as needed

## Troubleshooting

1. If browser actions fail:
   - Check the container logs: `docker-compose logs`
   - Verify the selectors used in actions
   - Ensure the target website is accessible

2. If screenshots aren't saving:
   - Check file permissions in the container
   - Verify the screenshot data is being properly encoded/decoded
   - Ensure sufficient disk space

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Performance Monitoring

The server provides comprehensive performance monitoring capabilities for both browser and general performance metrics.

### Browser Performance Metrics

1. **Start Performance Monitoring**
```python
{
    "type": "start_performance_monitoring",
    "params": {}
}
```

2. **Get Performance Metrics**
```python
{
    "type": "get_performance_metrics",
    "params": {}
}
```

The performance metrics include:
- Page load duration
- Navigation timing metrics:
  - `navigationStart`: When navigation begins
  - `loadEventEnd`: When the load event ends
  - `domComplete`: When the DOM is complete
  - `domInteractive`: When the DOM is interactive
  - `responseEnd`: When the response ends
  - `responseStart`: When the response starts
  - `requestStart`: When the request starts
  - `connectEnd`: When the connection ends
  - `connectStart`: When the connection starts
  - `domainLookupEnd`: When domain lookup ends
  - `domainLookupStart`: When domain lookup starts

### Network Conditions Testing

Simulate different network conditions to test application performance:

```python
{
    "type": "set_network_conditions",
    "params": {
        "offline": false,
        "latency": 100,  # milliseconds
        "download_throughput": 1024 * 1024,  # 1MB/s
        "upload_throughput": 1024 * 1024,  # 1MB/s
        "connection_type": "4G"  # Options: none, 2G, 3G, 4G
    }
}
```

### Example Usage

```python
# Start performance monitoring
browser_service.execute_action(session_id, {
    "type": "start_performance_monitoring",
    "params": {}
})

# Navigate to a page
browser_service.execute_action(session_id, {
    "type": "navigate",
    "params": {"url": "https://example.com"}
})

# Get performance metrics
metrics = browser_service.execute_action(session_id, {
    "type": "get_performance_metrics",
    "params": {}
})

# Test under different network conditions
browser_service.execute_action(session_id, {
    "type": "set_network_conditions",
    "params": {
        "latency": 100,
        "download_throughput": 1024 * 1024,
        "connection_type": "4G"
    }
})
```

### Performance Testing Best Practices

1. **Baseline Testing**
   - Run tests under normal conditions first
   - Record baseline metrics for comparison

2. **Network Simulation**
   - Test under various network conditions
   - Simulate different connection types (2G, 3G, 4G)
   - Test with different latency and throughput values

3. **Load Testing**
   - Monitor performance during multiple concurrent sessions
   - Track resource usage and response times

4. **Error Handling**
   - Monitor for performance degradation
   - Set up alerts for performance thresholds
   - Track error rates under different conditions

## Note on Network Throttling
The current Selenium setup does not support network throttling via Chrome DevTools Protocol (CDP). To enable network condition simulation, you need a Selenium Grid/node that supports CDP commands (e.g., using a compatible Docker image like `selenium/standalone-chrome`). Please refer to the [Selenium Docker documentation](https://github.com/SeleniumHQ/docker-selenium) for more details. 