"""
Pipedream MCP Authentication Service
Handles authentication with Pipedream MCP API for tool discovery and execution.
"""

import os
import time
import logging
import requests
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from flask import session
from azure.ai.inference.models import ChatCompletionsToolDefinition, FunctionDefinition

logger = logging.getLogger(__name__)


@dataclass
class PipedreamToolParameter:
    """Parameter definition for a Pipedream MCP tool following JSON-RPC schema."""
    name: str
    type: str
    description: str
    required: bool = False
    items: Optional[Dict[str, Any]] = None
    any_of: Optional[List[Dict[str, Any]]] = None
    additional_properties: bool = False
    
    def to_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = {
            "type": self.type,
            "description": self.description
        }
        
        if self.items:
            schema["items"] = self.items
        
        if self.any_of:
            schema["anyOf"] = self.any_of
            
        if self.additional_properties is False:
            schema["additionalProperties"] = False
            
        return schema


@dataclass
class PipedreamTool:
    """Represents a tool from Pipedream MCP server following JSON-RPC protocol."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    app_slug: str
    is_active: bool = True
    
    def to_sdk_definition(self) -> ChatCompletionsToolDefinition:
        """Convert to Azure SDK ChatCompletionsToolDefinition."""
        # Extract properties and required fields from input_schema
        properties = self.input_schema.get("properties", {})
        required = self.input_schema.get("required", [])
        
        func_def = FunctionDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": self.input_schema.get("additionalProperties", True)
            }
        )
        return ChatCompletionsToolDefinition(function=func_def)


@dataclass
class PipedreamAppTools:
    """Collection of tools for a specific Pipedream app."""
    app_slug: str
    app_name: str
    tools: List[PipedreamTool] = field(default_factory=list)
    is_connected: bool = False
    
    def get_sdk_tools(self) -> List[ChatCompletionsToolDefinition]:
        """Get all tools as Azure SDK definitions."""
        return [tool.to_sdk_definition() for tool in self.tools if tool.is_active]


class PipedreamToolsRegistry:
    """Registry for managing Pipedream MCP tools discovered from the server."""
    
    def __init__(self):
        self._apps: Dict[str, PipedreamAppTools] = {}
        self._discovered_at: Optional[int] = None
        
    def register_app_tools(self, app_slug: str, app_name: str, tools_data: Dict[str, Any]) -> None:
        """Register tools for a specific app."""
        tools = []
        
        # Parse tools from the MCP response
        for tool_data in tools_data.get("tools", []):
            tool = PipedreamTool(
                name=tool_data.get("name", ""),
                description=tool_data.get("description", ""),
                input_schema=tool_data.get("inputSchema", {}),
                app_slug=app_slug,
                is_active=True
            )
            tools.append(tool)
        
        app_tools = PipedreamAppTools(
            app_slug=app_slug,
            app_name=app_name,
            tools=tools,
            is_connected=len(tools) > 0
        )
        
        self._apps[app_slug] = app_tools
        logger.info(f"Registered {len(tools)} tools for app {app_slug}")
    
    def get_all_sdk_tools(self) -> List[ChatCompletionsToolDefinition]:
        """Get all tools as Azure SDK definitions."""
        all_tools = []
        for app_tools in self._apps.values():
            all_tools.extend(app_tools.get_sdk_tools())
        return all_tools
    
    def get_tools_by_app(self, app_slug: str) -> List[ChatCompletionsToolDefinition]:
        """Get tools for a specific app."""
        app_tools = self._apps.get(app_slug)
        if app_tools:
            return app_tools.get_sdk_tools()
        return []
    
    def get_connected_apps(self) -> List[str]:
        """Get list of app slugs that have connected tools."""
        return [app_slug for app_slug, app_tools in self._apps.items() if app_tools.is_connected]
    
    def is_fresh(self, max_age_seconds: int = 3600) -> bool:
        """Check if the tools data is fresh (less than max_age_seconds old)."""
        if not self._discovered_at:
            return False
        return (int(time.time()) - self._discovered_at) < max_age_seconds
    
    def mark_discovered(self) -> None:
        """Mark the tools as just discovered."""
        self._discovered_at = int(time.time())
    
    def clear(self) -> None:
        """Clear all tools data."""
        self._apps.clear()
        self._discovered_at = None


class PipedreamAuthService:
    """Service for managing Pipedream MCP authentication tokens."""
    
    def __init__(self):
        """Initialize the Pipedream authentication service."""
        self.base_url = "https://api.pipedream.com"
        self.auth_endpoint = f"{self.base_url}/v1/oauth/token"
        self.mcp_base_url = "https://remote.mcp.pipedream.net"
        
        # Load configuration from environment
        self.client_id = os.getenv("PIPEDREAM_API_CLIENT_ID")
        self.client_secret = os.getenv("PIPEDREAM_API_CLIENT_SECRET")
        self.project_id = os.getenv("PIPEDREAM_PROJECT_ID")
        self.environment = os.getenv("PIPEDREAM_ENVIRONMENT", "development")
        self.refresh_threshold = int("3600")  # 10 minutes default
        
        # Initialize tools registry
        self.tools_registry = PipedreamToolsRegistry()
        
        if not self.client_id or not self.client_secret:
            logger.warning("Pipedream credentials not configured. MCP features will be disabled.")
    
    def get_access_token(self) -> Optional[str]:
        """
        Fetch initial access token from Pipedream using client credentials.
        
        Returns:
            Optional[str]: Access token if successful, None otherwise
        """
        if not self.client_id or not self.client_secret:
            logger.error("Pipedream credentials not configured")
            return None
        
        try:
            logger.info("Fetching initial Pipedream access token")
            
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = requests.post(
                self.auth_endpoint,
                data=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
                
                print(f"DEBUG: Token data: {token_data}")
                print(f"DEBUG: Access token: {access_token}")
                print(f"DEBUG: Expires in: {expires_in}")
                
                if access_token:
                    # Store token in session
                    self._store_token_in_session(access_token, expires_in)
                    logger.info("Successfully acquired Pipedream access token")
                    return access_token
                else:
                    logger.error("No access_token in Pipedream response")
                    return None
            else:
                logger.error(f"Failed to acquire Pipedream token. Status: {response.status_code}, Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error acquiring Pipedream token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error acquiring Pipedream token: {str(e)}")
            return None
    
    def refresh_access_token(self) -> Optional[str]:
        """
        Get a new access token using client credentials (no refresh token needed).
        
        Returns:
            Optional[str]: New access token if successful, None otherwise
        """
        logger.info("Getting new Pipedream access token using client credentials")
        return self.get_access_token()
    
    def get_token_from_session(self) -> Optional[str]:
        """
        Retrieve cached access token from session, getting new one if necessary.
        
        Returns:
            Optional[str]: Valid access token if available, None otherwise
        """
        # Check if we have a valid token in session
        if self.is_token_valid():
            access_token = session.get("pipedream_access_token")
            logger.debug("Using cached Pipedream access token")
            return access_token
        
        # Token is expired or missing, get a new one
        logger.info("Pipedream token expired or missing, getting new token")
        return self.refresh_access_token()
    
    def is_token_valid(self) -> bool:
        """
        Check if the current access token is valid and not expired.
        
        Returns:
            bool: True if token is valid, False otherwise
        """
        access_token = session.get("pipedream_access_token")
        expires_at = session.get("pipedream_token_expires_at")
        
        if not access_token or not expires_at:
            return False
        
        # Check if token is expired (with refresh threshold)
        current_time = int(time.time())
        refresh_time = expires_at - self.refresh_threshold
        
        if current_time >= refresh_time:
            logger.debug(f"Pipedream token expired or near expiry. Current: {current_time}, Expires: {expires_at}")
            return False
        
        return True
    
    def _store_token_in_session(self, access_token: str, expires_in: int) -> None:
        """
        Store token information in Flask session.
        
        Args:
            access_token: The access token string
            expires_in: Token expiration time in seconds
        """
        current_time = int(time.time())
        expires_at = current_time + expires_in
        
        session["pipedream_access_token"] = access_token
        session["pipedream_token_expires_at"] = expires_at
        session["pipedream_token_created_at"] = current_time
        
        logger.debug(f"Stored Pipedream token in session. Expires at: {expires_at}")
    
    def clear_session_tokens(self) -> None:
        """Clear all Pipedream tokens from the session."""
        session_keys = [
            "pipedream_access_token",
            "pipedream_token_expires_at", 
            "pipedream_token_created_at"
        ]
        
        for key in session_keys:
            session.pop(key, None)
        
        # Also clear the tools registry
        self.tools_registry.clear()
        
        logger.info("Cleared Pipedream tokens and tools registry")
    
    def get_auth_headers(self) -> Optional[Dict[str, str]]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Optional[Dict[str, str]]: Headers with Bearer token if available, None otherwise
        """
        token = self.get_token_from_session()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return None
    
    def get_mcp_auth_headers(self, external_user_id: str, app_slug: str, oauth_app_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Get authentication headers for MCP server requests.
        
        Args:
            external_user_id: The user's ID in your system
            app_slug: The app slug (e.g., 'notion', 'gmail', 'slack')
            oauth_app_id: Optional OAuth app ID for custom OAuth clients
            
        Returns:
            Optional[Dict[str, str]]: Headers for MCP requests if token available, None otherwise
        """
        token = self.get_token_from_session()
        if not token:
            logger.error("No Pipedream access token available for MCP request")
            return None
        
        headers = {
            "Authorization": f"Bearer {token}",
            "x-pd-project-id": self.project_id,
            "x-pd-environment": self.environment,
            "x-pd-external-user-id": external_user_id,
            "x-pd-app-slug": app_slug
        }
        
        if oauth_app_id:
            headers["x-pd-oauth-app-id"] = oauth_app_id
        
        return headers
    
    def discover_available_apps(self) -> Optional[Dict[str, Any]]:
        """
        Discover all available apps from Pipedream.
        
        Returns:
            Optional[Dict[str, Any]]: Available apps data if successful, None otherwise
        """
        if not self.project_id:
            logger.error("PIPEDREAM_PROJECT_ID not configured")
            return None
        
        try:
            logger.info("Discovering available Pipedream apps")
            
            headers = self.get_auth_headers()
            if not headers:
                return None
            
            # Add project ID to headers for this request
            headers["x-pd-project-id"] = self.project_id
            headers["x-pd-environment"] = self.environment
            
            response = requests.get(
                f"{self.base_url}/v1/apps",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                apps_data = response.json()
                logger.info(f"Successfully discovered {len(apps_data.get('data', []))} available apps")
                return apps_data
            else:
                logger.error(f"Failed to discover apps. Status: {response.status_code}, Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error discovering apps: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error discovering apps: {str(e)}")
            return None
    
    def get_tools_for_app(self, external_user_id: str, app_slug: str, oauth_app_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get available tools for a specific app from Pipedream MCP server.
        
        Args:
            external_user_id: The user's ID in your system
            app_slug: The app slug (e.g., 'notion', 'gmail', 'slack')
            oauth_app_id: Optional OAuth app ID for custom OAuth clients
            
        Returns:
            Optional[Dict[str, Any]]: Tools data if successful, None otherwise
        """
        if not self.project_id:
            logger.error("PIPEDREAM_PROJECT_ID not configured")
            return None
        
        try:
            logger.info(f"Getting tools for app: {app_slug}")
            
            headers = self.get_mcp_auth_headers(external_user_id, app_slug, oauth_app_id)
            if not headers:
                return None
            
            # Make request to MCP server to get tools
            mcp_url = f"{self.mcp_base_url}/{external_user_id}/{app_slug}"
            
            response = requests.get(
                mcp_url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                tools_data = response.json()
                logger.info(f"Successfully retrieved tools for {app_slug}")
                return tools_data
            else:
                logger.error(f"Failed to get tools for {app_slug}. Status: {response.status_code}, Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting tools for {app_slug}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting tools for {app_slug}: {str(e)}")
            return None
    
    def discover_all_tools(self, external_user_id: str) -> PipedreamToolsRegistry:
        """
        Discover tools for a user from hardcoded list of apps.
        
        Args:
            external_user_id: The user's ID in your system
            
        Returns:
            PipedreamToolsRegistry: Registry containing all discovered tools
        """
        logger.info(f"Discovering tools for user: {external_user_id}")
        
        # Clear existing registry
        self.tools_registry.clear()
        
        # Hardcoded list of app slugs to discover
        target_apps = [
            {"slug": "google_docs", "name": "Google Docs"},
            {"slug": "notion", "name": "Notion"}
        ]
        
        for app in target_apps:
            app_slug = app["slug"]
            app_name = app["name"]
            
            logger.info(f"Getting tools for app: {app_slug}")
            tools_data = self.get_tools_for_app(external_user_id, app_slug)
            
            if tools_data:
                self.tools_registry.register_app_tools(app_slug, app_name, tools_data)
                logger.info(f"Successfully registered {len(tools_data.get('tools', []))} tools for {app_slug}")
            else:
                logger.warning(f"Could not retrieve tools for {app_slug}")
        
        # Mark as discovered
        self.tools_registry.mark_discovered()
        logger.info(f"Total apps with tools discovered: {len(self.tools_registry._apps)}")
        return self.tools_registry
    
    def get_tools_registry(self) -> PipedreamToolsRegistry:
        """
        Get the current tools registry.
        
        Returns:
            PipedreamToolsRegistry: The current tools registry
        """
        return self.tools_registry
    
    def get_all_sdk_tools(self) -> List[ChatCompletionsToolDefinition]:
        """
        Get all discovered tools as Azure SDK definitions.
        
        Returns:
            List[ChatCompletionsToolDefinition]: All tools ready for LLM
        """
        if not self.tools_registry.is_fresh():
            logger.warning("Tools registry is stale, tools need to be rediscovered")
            return []
        
        return self.tools_registry.get_all_sdk_tools()
    
    def get_tools_by_app(self, app_slug: str) -> List[ChatCompletionsToolDefinition]:
        """
        Get tools for a specific app as Azure SDK definitions.
        
        Args:
            app_slug: The app slug to get tools for
            
        Returns:
            List[ChatCompletionsToolDefinition]: Tools for the specified app
        """
        if not self.tools_registry.is_fresh():
            logger.warning("Tools registry is stale, tools need to be rediscovered")
            return []
        
        return self.tools_registry.get_tools_by_app(app_slug)

    def get_mcp_req_endpoint(self) -> str:
        """
        Get the MCP tool execution endpoint from environment variable.
        """
        return os.getenv("PIPEDREAM_MCP_REQ_ENDPOINT", "https://remote.mcp.pipedream.net")

    def execute_tool(
        self,
        external_user_id: str,
        app_slug: str,
        tool_name: str,
        tool_args: dict,
        oauth_app_id: Optional[str] = None,
        tool_mode: Optional[str] = None
    ) -> dict:
        """
        Execute a tool via the Pipedream MCP endpoint using the correct headers and params.
        """
        # Build headers
        headers = self.get_mcp_auth_headers(external_user_id, app_slug, oauth_app_id)
        if not headers:
            return {"error": "No valid Pipedream access token or headers"}
        if tool_mode:
            headers["x-pd-tool-mode"] = tool_mode

        # Build URL
        base_url = self.get_mcp_req_endpoint().rstrip("/")
        url = f"{base_url}/{external_user_id}/{app_slug}/{tool_name}"
        

        try:
            response = requests.post(
                url,
                headers=headers,
                json=tool_args,
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Failed to execute tool. Status: {response.status_code}",
                    "response": response.text
                }
        except Exception as e:
            return {"error": f"Exception during tool execution: {str(e)}"}


# Create singleton instance
pipedream_auth_service = PipedreamAuthService() 