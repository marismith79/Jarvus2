# Availity MCP Server

A FastAPI-based MCP server that exposes Availity's Enhanced Claim Status APIs as tools for LLM integration.

## Features

- OAuth2 token management for Availity API authentication
- Enhanced Claim Status API endpoints:
  - Summary Search
  - Detail Search
  - Configurations Lookup
- Tool registration for LLM integration
- Async request handling
- Type-safe request/response validation

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Availity credentials:
```env
AVAILITY_CLIENT_ID=your_client_id
AVAILITY_CLIENT_SECRET=your_client_secret
AVAILITY_PAYER_ID=your_payer_id
```

## Running the Server

Start the server with:
```bash
uvicorn app:app --reload
```

The server will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Available Endpoints

### Claim Status

- `POST /availity/v1/claim-statuses/summarySearch`
- `POST /availity/v1/claim-statuses/detailSearch`

### Configurations

- `GET /availity/v1/configurations`

## Tool Integration

The server provides two main tools for LLM integration:

1. `summary_search_tool`: For basic claim status information
2. `detail_search_tool`: For detailed claim status with service lines

Example tool invocation:
```python
result = await summary_search_tool(
    claim_number="12345",
    payer_id="9876"
)
```

## Security Notes

- Never commit the `.env` file
- In production, configure CORS with specific origins
- Use HTTPS in production
- Consider implementing rate limiting
- Monitor token usage and implement proper error handling 