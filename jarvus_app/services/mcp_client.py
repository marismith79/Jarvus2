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
        self.default_timeout = 60  # 60 second default timeout
        
        # Pipedream endpoints for Google Workspace services
        self.pipedream_endpoints = {
            "docs": os.getenv("PIPEDREAM_DOCS_ENDPOINT"),
            "sheets": os.getenv("PIPEDREAM_SHEETS_ENDPOINT"),
            "slides": os.getenv("PIPEDREAM_SLIDES_ENDPOINT"),
            "drive": os.getenv("PIPEDREAM_DRIVE_ENDPOINT"),
            "gmail": os.getenv("PIPEDREAM_GMAIL_ENDPOINT"),
            "calendar": os.getenv("PIPEDREAM_CALENDAR_ENDPOINT"),
        }

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

    def execute_tool(self, tool_name: str, payload: Dict[str, Any], jwt_token: Optional[str] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a tool operation through the MCP server.
        
        Args:
            tool_name: The name of the tool (e.g., 'gmail', 'calendar')
            payload: Operation-specific parameters
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
        if not isinstance(payload, dict):
            raise ToolExecutionError("Parameters must be a dictionary")
        
        print(f"\nExecuting {tool_name}")
        print(f"Original payload: {payload}")
        print(f"JWT Token provided: {jwt_token is not None}")
        
        try:
            # Check if this is a service that should use Pipedream
            pipedream_endpoint = self.pipedream_endpoints.get(tool_name)
            if pipedream_endpoint:
                url = pipedream_endpoint
                print(f"Routing {tool_name} to Pipedream endpoint: {url}")
                
                # Format request for Pipedream
                request_body = self._format_pipedream_request(tool_name, payload, jwt_token)
            else:
                # Use the default MCP server URL
                url = f"{self.base_url}/{tool_name}/"
                print(f"Making request to MCP server: {url}")
                request_body = payload
            
            # Set up headers with JWT token if provided
            headers = {}
            if jwt_token:
                headers['Authorization'] = f'Bearer {jwt_token}'
                print(f"Added Authorization header: Bearer {jwt_token[:10]}...")
            else:
                print("No JWT token provided, skipping Authorization header")
            
            print(f"Request headers: {headers}")
            print(f"Request payload: {request_body}")
            
            # Send request with timeout
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

    def _format_pipedream_request(self, tool_name: str, payload: Dict[str, Any], jwt_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Format request for Pipedream HTTP-triggered workflow.
        
        Args:
            tool_name: The name of the tool (e.g., 'docs', 'sheets')
            payload: Original payload from tool registry
            jwt_token: Optional JWT token for user identification
            
        Returns:
            Dict[str, Any]: Formatted request body for Pipedream
        """
        try:
            # Extract user_id from JWT token if available
            user_id = None
            if jwt_token:
                # Simple extraction - in production you'd want proper JWT decoding
                import base64
                import json
                try:
                    # Extract payload from JWT (this is a simplified approach)
                    parts = jwt_token.split('.')
                    if len(parts) == 3:
                        payload_part = parts[1]
                        # Add padding if needed
                        payload_part += '=' * (4 - len(payload_part) % 4)
                        decoded = base64.b64decode(payload_part)
                        jwt_payload = json.loads(decoded)
                        user_id = jwt_payload.get('sub') or jwt_payload.get('user_id')
                except Exception as e:
                    print(f"Warning: Could not extract user_id from JWT: {e}")
            
            # Get the user's connect_id for this service
            connect_id = None
            if user_id:
                from ..models.oauth import OAuthCredentials
                creds = OAuthCredentials.get_credentials(user_id, tool_name)
                if creds and hasattr(creds, 'connect_id'):
                    connect_id = creds.connect_id
                    print(f"Found connect_id for {tool_name}: {connect_id}")
                else:
                    print(f"No connect_id found for user {user_id} and service {tool_name}")
            else:
                print("No user_id available, cannot get connect_id")
            
            # Extract operation and parameters from payload
            operation = payload.get('operation', tool_name)
            parameters = payload.get('parameters', payload)
            
            # Format according to Pipedream's expected structure
            pipedream_request = {
                "connection_id": connect_id,
                "action": operation,
                "params": parameters
            }
            
            # Add user context if available
            if user_id:
                pipedream_request["user_id"] = user_id
            
            print(f"Formatted Pipedream request: {pipedream_request}")
            return pipedream_request
            
        except Exception as e:
            print(f"Error formatting Pipedream request: {e}")
            # Fallback to original payload if formatting fails
            return payload


# Create a singleton instance
mcp_client = MCPClient() 