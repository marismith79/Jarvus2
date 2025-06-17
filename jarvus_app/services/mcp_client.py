"""
MCP Client for communicating with MCP servers.
Provides a generic interface for interacting with various services through their respective MCP servers.
"""

import os
from typing import Any, Dict, Optional

import requests
from requests.exceptions import RequestException


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


class ToolExecutionError(MCPError):
    """Raised when tool execution fails."""
    pass


class MCPClient:
    """Client for communicating with MCP servers."""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("MCP_SERVER_URL", "http://localhost:8000")
        print(f"\nMCP Client initialized with URL: {self.base_url}")
        self.default_timeout = 30  # 30 second default timeout

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle HTTP response and raise appropriate exceptions."""
        print("\n=== MCP Response Debug ===")
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code == 403:
            raise PermissionError("Permission denied")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
            
        response.raise_for_status()
        result = response.json()
        
        print(f"Response body type: {type(result)}")
        # print(f"Response body: {result}")
        print("=== End MCP Response Debug ===\n")
        
        return result

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any], jwt_token: Optional[str] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a tool operation through the MCP server.
        
        Args:
            tool_name: The name of the tool (e.g., 'gmail', 'calendar')
            parameters: Operation-specific parameters
            jwt_token: Optional JWT token for authentication
            timeout: Optional timeout in seconds (defaults to self.default_timeout)
            
        Returns:
            Dict[str, Any]: The operation result as a dictionary
            
        Raises:
            ToolExecutionError: If tool execution fails
            AuthenticationError: If authentication fails
            PermissionError: If user lacks required permissions
            RateLimitError: If rate limit is exceeded
        """
        # Validate inputs
        if not tool_name:
            raise ToolExecutionError("Tool name cannot be empty")
        if not isinstance(parameters, dict):
            raise ToolExecutionError("Parameters must be a dictionary")
        
        print(f"\nExecuting {tool_name}")
        print(f"Parameters: {parameters}")
        print(f"JWT Token provided: {jwt_token is not None}")
        
        try:
            # Construct the URL for the MCP server with trailing slash
            url = f"{self.base_url}/{tool_name}/"
            print(f"Making request to: {url}")
            
            # Set up headers with JWT token if provided
            headers = {}
            if jwt_token:
                headers['Authorization'] = f'Bearer {jwt_token}'
                print(f"Added Authorization header: Bearer {jwt_token[:10]}...")
            else:
                print("No JWT token provided, skipping Authorization header")
            
            print(f"Request headers: {headers}")
            
            # If parameters contains an 'operation' field, use the nested parameters
            request_body = parameters.get('parameters', parameters)
            print(f"Request payload: {request_body}")
            
            # Send parameters directly as the request body with timeout
            timeout = timeout or self.default_timeout
            resp = requests.post(
                url, 
                json=request_body, 
                headers=headers, 
                allow_redirects=True,
                timeout=timeout
            )
            
            # Handle the response and get the result
            result = self._handle_response(resp)
            
            # Log successful execution
            print(f"Successfully executed {tool_name}")
            # print(f"About to return result: {result}")
            print(f"Result type: {type(result)}")
            return result
            
        except requests.exceptions.Timeout:
            error_msg = f"Request timed out after {timeout} seconds for {tool_name}"
            print(f"\n{error_msg}")
            raise ToolExecutionError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            print(f"\n{error_msg}")
            print(f"Request URL: {url}")
            print(f"Request payload: {request_body}")
            raise ToolExecutionError(error_msg) from e


# Create a singleton instance
mcp_client = MCPClient() 