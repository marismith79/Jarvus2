# Availity MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with Availity's API. This server follows Anthropic's Model Context Protocol specification to provide a standardized interface for AI models to interact with Availity's services.

## Project Structure

```
mcp_server/
├── __init__.py
├── app.py                 # MCP server implementation
├── config.py             # Configuration and environment settings
├── services/
│   ├── __init__.py
│   └── availity.py      # Availity API service wrapper
└── requirements.txt      # Project dependencies
```

## Features

- MCP-compliant tool definitions
- Availity API integration
- Type-safe request/response handling
- Environment-based configuration

## Available Tools

### 1. Get Claim Status
```python
@mcp.tool()
async def get_claim_status(claim_id: str, payer_id: str) -> Dict[str, Any]
```
Get the status of a specific claim.

### 2. List Claim Statuses
```python
@mcp.tool()
async def list_claim_statuses(payer_id: str, claim_number: str) -> Dict[str, Any]
```
List all claim statuses for a payer and claim number.

### 3. Get Configurations
```python
@mcp.tool()
async def get_configurations(type: str, subtype_id: str, payer_id: str) -> Dict[str, Any]
```
Get payer configurations.

## Setup and Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```env
AVAILITY_CLIENT_ID=your_client_id
AVAILITY_CLIENT_SECRET=your_client_secret
AVAILITY_PAYER_ID=your_payer_id
AVAILITY_TOKEN_URL=https://api.availity.com/availity/v1/token
AVAILITY_API_BASE_URL=https://api.availity.com/availity/development-partner/v1
```

3. Run the server:
```bash
python -m mcp_server.app
```

## Claude Desktop Integration

To use this server with Claude Desktop, add the following to your Claude Desktop configuration:

```json
{
    "mcpServers": {
        "availity": {
            "command": "python",
            "args": [
                "-m",
                "mcp_server.app"
            ]
        }
    }
}
```

## Development

The server uses the official MCP SDK and follows the Model Context Protocol specification. Key features:

- Tool definitions using `@mcp.tool()` decorator
- Type hints and docstrings for better tool documentation
- Standardized error handling
- Environment-based configuration

### Testing

The server includes a test script (`test_mcp.py`) that verifies the functionality of the MCP tools. This script tests the following endpoints:

- **get_claim_status**: Retrieves the status of a specific claim.
- **list_claim_statuses**: Lists all claim statuses for a given payer and claim number.
- **get_configurations**: Retrieves payer configurations.

To run the tests, execute:

```bash
python test_mcp.py
```

## Security

- Credentials are managed through environment variables
- All API calls are authenticated
- Error handling for failed requests
- Input validation through type hints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License 