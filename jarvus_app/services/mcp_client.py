"""
MCP Client for communicating with MCP servers.
Provides a generic interface for interacting with various services through their respective MCP servers.
"""

import os
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import RequestException

from .tool_registry import tool_registry

# Get MCP server URL from environment variable, default to localhost for development
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
print(f"\nMCP Server URL set to: {MCP_SERVER_URL}")


class MCPError(Exception):
    """Base exception for MCP client errors."""
    pass


class AuthenticationError(MCPError):
    """Raised when authentication fails."""
    pass


class PermissionError(MCPError):
    """Raised when user lacks required permissions."""
    pass


class RateLimitError(MCPError):
    """Raised when rate limit is exceeded."""
    pass


class MCPClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or MCP_SERVER_URL
        print(f"\nMCP Client initialized with URL: {self.base_url}")

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle HTTP response and raise appropriate exceptions."""
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code == 403:
            raise PermissionError("Permission denied")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        response.raise_for_status()
        return response.json()

    def handle_operation(self, tool_name: str, operation: str, parameters: Dict[str, Any]) -> Any:
        """
        Generic handler for tool operations.
        
        Args:
            tool_name: The name of the tool (e.g., 'gmail', 'calendar')
            operation: The operation to perform
            parameters: Operation-specific parameters
            
        Returns:
            The operation result
        """
        print(f"\nCalling {tool_name} operation: {operation}")
        print(f"Parameters: {parameters}")
        
        # Get the tool metadata from the registry
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        try:
            # Construct the full URL using the tool's server path
            url = f"{self.base_url}/{tool.server_path}/{operation}"
            print(f"Making request to: {url}")
            
            resp = requests.post(url, json=parameters)
            return self._handle_response(resp)
        except requests.exceptions.RequestException as e:
            print(f"\nError making request: {str(e)}")
            print(f"Request URL: {url}")
            print(f"Request payload: {parameters}")
            raise


# Singleton instance
mcp_client = MCPClient()
