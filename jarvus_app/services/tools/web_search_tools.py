"""Web Search and HTTP Request tool registrations for MCP server."""

from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_tool_result
from ..mcp_client import mcp_client

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def google_search_executor(tool_name, payload, jwt_token=None):
    query = payload.get('parameters', {}).get('query')
    body = {'mode': 'google', 'query': query}
    return mcp_client.execute_tool(tool_name='search/google', payload=body, jwt_token=jwt_token)

def http_request_executor(tool_name, payload, jwt_token=None):
    params = payload.get('parameters', {})
    body = {'mode': 'http'}
    body.update(params)
    return mcp_client.execute_tool(tool_name='search/http', payload=body, jwt_token=jwt_token)

def register_web_search_tools(registry: 'ToolRegistry') -> None:
    """Register the Google Web Search and HTTP Request tools."""
    # Google Custom Search tool
    registry.register(ToolMetadata(
        name="google_web_search",
        description="Perform a web search using Google Custom Search via the MCP server.",
        category=ToolCategory.WEB,
        server_path="search/google",  # This should match the MCP server route
        requires_auth=False,
        parameters=[
            ToolParameter("query", "string", "Search query for Google Custom Search", required=True),
        ],
        result_formatter=format_tool_result,
        executor=google_search_executor
    ))

    # Direct HTTP Request tool
    registry.register(ToolMetadata(
        name="http_request",
        description="Send a direct HTTP request via the MCP server (GET, POST, etc.).",
        category=ToolCategory.WEB,
        server_path="search/http",  # This should match the MCP server route
        requires_auth=False,
        parameters=[
            ToolParameter("url", "string", "URL for direct HTTP request", required=True),
            ToolParameter("method", "string", "HTTP method for the request (default: GET)", required=False),
            ToolParameter("headers", "object", "Headers for the HTTP request", required=False),
            ToolParameter("body", "string", "Body for the HTTP request", required=False),
        ],
        result_formatter=format_tool_result,
        executor=http_request_executor
    )) 