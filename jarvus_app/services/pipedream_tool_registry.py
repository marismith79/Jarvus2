"""
Pipedream MCP Tool Registry
Handles tool discovery and execution for Pipedream MCP services.
"""

import os
import time
import logging
import requests
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from azure.ai.inference.models import ChatCompletionsToolDefinition, FunctionDefinition

from .pipedream_auth_service import pipedream_auth_service

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


class PipedreamToolService:
    """Service for managing Pipedream MCP tool discovery and execution."""
    
    def __init__(self):
        """Initialize the Pipedream tool service."""
        self.tools_registry = PipedreamToolsRegistry()
    
    def _parse_sse_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse SSE (Server-Sent Events) response and extract JSON data.
        
        Args:
            response_text: The raw response text from the server
            
        Returns:
            Optional[Dict[str, Any]]: Parsed JSON data if successful, None otherwise
        """
        try:
            lines = response_text.strip().split('\n')
            for line in lines:
                if line.startswith('data: '):
                    json_str = line[6:]  # Remove 'data: ' prefix
                    return json.loads(json_str)
            # If no SSE format, try parsing as regular JSON
            return json.loads(response_text)
        except (json.JSONDecodeError, IndexError) as e:
            print(f"[ERROR] Failed to parse SSE response: {e}")
            print(f"[DEBUG] Raw response: {response_text}")
            return None

    def get_tools_for_app(self, external_user_id: str, app_slug: str, oauth_app_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get available tools for a specific app from Pipedream MCP server (direct, no Inspector proxy).
        """
        remote_base = "https://remote.mcp.pipedream.net/v1"
        base_url = remote_base
        project_id = os.getenv("PIPEDREAM_PROJECT_ID")
        if not project_id:
            print("PIPEDREAM_PROJECT_ID not configured")
            return None
        try:
            print(f"Getting tools for app: {app_slug}")
            headers = pipedream_auth_service.get_mcp_auth_headers(external_user_id, app_slug, oauth_app_id)
            if not headers:
                print("No headers")
                return None
            headers["Content-Type"] = "application/json"
            headers["Accept"] = "application/json, text/event-stream"
            body = {
                "jsonrpc": "2.0",
                "id": 20,
                "method": "tools/list",
                "params": {}
            }
            url = f"{base_url}/{external_user_id}/{app_slug}"
            print(f"[DEBUG] Tool list POST URL: {url}")
            print(f"[DEBUG] Tool list POST headers: {headers}")
            print(f"[DEBUG] Tool list POST body: {body}")
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=30
                )
                print(f"[DEBUG] Tool list POST status: {response.status_code}")
                print(f"[DEBUG] Tool list POST response: {response.text}")
            except Exception as e:
                print(f"[ERROR] Exception during tool list POST: {e}")
                raise
            if response.status_code == 200:
                payload = self._parse_sse_response(response.text)
                if not payload:
                    print(f"Failed to parse response for {app_slug}")
                    return None
                if "error" in payload:
                    print(f"MCP error for {app_slug}: {payload['error']}")
                    return None
                result = payload.get("result", {})
                tools = result.get("tools", [])
                print(f"Successfully retrieved {len(tools)} tools for {app_slug}")
                return {"tools": tools}
            else:
                print(f"Failed to get tools for {app_slug}. Status: {response.status_code}, Response: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request error getting tools for {app_slug}: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error getting tools for {app_slug}: {str(e)}")
            return None
    
    def discover_all_tools(self, external_user_id: str) -> PipedreamToolsRegistry:
        """
        Discover tools for a user from hardcoded list of apps.
        
        Args:
            external_user_id: The user's ID in your system
            
        Returns:
            PipedreamToolsRegistry: Registry containing all discovered tools
        """
        print(f"Discovering tools for user: {external_user_id}")
        
        # Clear existing registry
        self.tools_registry.clear()
        
        # Hardcoded list of app slugs to discover
        target_apps = [
            {"slug": "google_docs", "name": "Google Docs"},
            # {"slug": "notion", "name": "Notion"}
        ]
        
        for app in target_apps:
            app_slug = app["slug"]
            app_name = app["name"]
            
            print(f"Fetching tools for app: {app_slug}")
            tools_data = self.get_tools_for_app(external_user_id, app_slug)
            print(f"Tools data: {tools_data}")
            
            if tools_data:
                self.tools_registry.register_app_tools(app_slug, app_name, tools_data)
                print(f"Successfully registered {len(tools_data.get('tools', []))} tools for {app_slug}")
            else:
                print(f"Could not retrieve tools for {app_slug}")
        
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
        Execute a tool via the Pipedream MCP endpoint using JSON-RPC protocol (direct, no Inspector proxy).
        """
        remote_base = "https://remote.mcp.pipedream.net/v1"
        base_url = remote_base
        headers = pipedream_auth_service.get_mcp_auth_headers(external_user_id, app_slug, oauth_app_id)
        if not headers:
            return {"error": "No valid Pipedream access token or headers"}
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json, text/event-stream"
        if tool_mode:
            headers["x-pd-tool-mode"] = tool_mode
        body = {
            "jsonrpc": "2.0",
            "id": 20,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": tool_args
            }
        }
        url = f"{base_url}/{external_user_id}/{app_slug}"
        print(f"[DEBUG] Tool exec POST URL: {url}")
        print(f"[DEBUG] Tool exec POST headers: {headers}")
        print(f"[DEBUG] Tool exec POST body: {body}")
        try:
            response = requests.post(
                url,
                headers=headers,
                json=body,
                timeout=60
            )
            print(f"[DEBUG] Tool exec POST status: {response.status_code}")
            print(f"[DEBUG] Tool exec POST response: {response.text}")
        except Exception as e:
            print(f"[ERROR] Exception during tool exec POST: {e}")
            raise
        if response.status_code == 200:
            payload = self._parse_sse_response(response.text)
            if not payload:
                return {"error": "Failed to parse response"}
            if "error" in payload:
                logger.error(f"MCP tool execution error: {payload['error']}")
                return {"error": f"MCP error: {payload['error']}"}
            result = payload.get("result", {})
            return result
        else:
            return {
                "error": f"Failed to execute tool. Status: {response.status_code}",
                "response": response.text
            }


# Create singleton instance
pipedream_tool_service = PipedreamToolService() 