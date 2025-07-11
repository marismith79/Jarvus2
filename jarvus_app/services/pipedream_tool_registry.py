"""
Pipedream MCP Tool Registry
Handles tool discovery and execution for Pipedream MCP services.
"""

import os
import time
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from azure.ai.inference.models import ChatCompletionsToolDefinition, FunctionDefinition
import pickle

from .pipedream_auth_service import pipedream_auth_service
from jarvus_app.models.tool_discovery_cache import ToolDiscoveryCache
from jarvus_app.config import ALL_PIPEDREAM_APPS
from jarvus_app.services.tool_registry import ToolCategory

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


@dataclass
class PipedreamToolMetadata:
    """Unified metadata for Pipedream MCP tools that integrates with the agent system."""
    name: str
    description: str
    app_slug: str
    app_name: str
    category: ToolCategory  # Use the same enum as ToolMetadata
    input_schema: Dict[str, Any]  # Keep the JSON-RPC schema
    requires_auth: bool = True
    is_active: bool = True
    executor: Optional[Callable] = None
    result_formatter: Optional[Callable] = None
    oauth_app_id: Optional[str] = None
    
    def to_sdk_definition(self) -> ChatCompletionsToolDefinition:
        """Convert to Azure SDK definition using the input_schema."""
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


class PipedreamToolsRegistry:
    """Registry for managing Pipedream MCP tools discovered from the server."""
    
    def __init__(self):
        self._tools: Dict[str, PipedreamToolMetadata] = {}
        
    def register_app_tools(self, app_slug: str, app_name: str, tools_data: Dict[str, Any]) -> None:
        """Register tools for a specific app."""
        for tool_data in tools_data.get("tools", []):
            tool_name = tool_data.get("name", "")
            
            tool_metadata = PipedreamToolMetadata(
                name=tool_name,
                description=tool_data.get("description", ""),
                app_slug=app_slug,
                app_name=app_name,
                category=ToolCategory.CUSTOM,
                input_schema=tool_data.get("inputSchema", {}),
                executor=self._create_executor(app_slug, tool_name),
                is_active=True
            )
            
            self._tools[tool_name] = tool_metadata
    
    def _create_executor(self, app_slug: str, tool_name: str) -> Callable:
        """Create an executor function that calls your existing execute_tool."""
        def executor(user_id: str, tool_args: dict, jwt_token: Optional[str] = None) -> dict:
            return pipedream_tool_service.execute_tool(
                external_user_id=user_id,
                app_slug=app_slug,
                tool_name=tool_name,
                tool_args=tool_args,
                jwt_token=jwt_token
            )
        return executor
    
    def get_tool(self, tool_name: str) -> Optional[PipedreamToolMetadata]:
        """Get tool metadata by name."""
        return self._tools.get(tool_name)
    
    def execute_tool(self, tool_name: str, user_id: str, parameters: Dict[str, Any] = None, jwt_token: Optional[str] = None) -> Any:
        """Execute tool using the unified interface."""
        tool = self.get_tool(tool_name)
        if not tool or not tool.is_active:
            raise ValueError(f"Tool not available: {tool_name}")
        
        raw_result = tool.executor(user_id, parameters, jwt_token)
        
        if tool.result_formatter:
            return tool.result_formatter(raw_result)
        return raw_result
    
    def get_all_sdk_tools(self) -> List[ChatCompletionsToolDefinition]:
        """Get all tools as Azure SDK definitions."""
        return [tool.to_sdk_definition() for tool in self._tools.values() if tool.is_active]

    def get_tool_to_app_mapping(self) -> Dict[str, str]:
        """Get a mapping of tool names to their app slugs."""
        return {tool.name: tool.app_slug for tool in self._tools.values()}


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
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=30
                )
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
    
    def discover_all_tools(self, user_id):
        """
        Discover tools for a user from hardcoded list of apps.
        
        Args:
            external_user_id: The user's ID in your system
            
        Returns:
            PipedreamToolsRegistry: Registry containing all discovered tools
        """
        print(f"Discovering tools for user: {user_id}")
        
        # Hardcoded list of app slugs to discover
        all_possible_apps = ALL_PIPEDREAM_APPS

        for app in all_possible_apps:
            app_slug = app["slug"]
            app_name = app["name"]
            
            print(f"Fetching tools for app: {app_slug}")
            tools_data = self.get_tools_for_app(user_id, app_slug)
            
            if tools_data:
                self.tools_registry.register_app_tools(app_slug, app_name, tools_data)
                print(f"Successfully registered {len(tools_data.get('tools', []))} tools for {app_slug}")
            else:
                print(f"Could not retrieve tools for {app_slug}")
        
        # Register local MCP tools using the same registration logic as the main ToolRegistry
        from jarvus_app.services.tools.web_search_tools import register_web_search_tools
        from jarvus_app.services.tool_registry import ToolRegistry
        # Create a temporary ToolRegistry to collect local tools
        local_registry = ToolRegistry()
        register_web_search_tools(local_registry)
        # Convert ToolMetadata to PipedreamTool-compatible dicts
        local_tools = []
        for tool in local_registry.get_all_tools():
            # Build inputSchema from parameters
            props = {}
            required = []
            if tool.parameters:
                for p in tool.parameters:
                    props[p.name] = p.to_schema()
                    if p.required:
                        required.append(p.name)
            else:
                props = {"query": {"type": "string", "description": "Search query or parameters for the operation"}}
            input_schema = {
                "type": "object",
                "properties": props,
                "required": required
            }
            local_tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": input_schema
            })
        self.tools_registry.register_app_tools(
            "web", "Local MCP Web browser", {"tools": local_tools}
        )
        
        logger.info(f"Total tools discovered: {len(self.tools_registry._tools)}")
        return self.tools_registry
    
    def get_tools_registry(self) -> PipedreamToolsRegistry:
        """
        Get the current tools registry.
        
        Returns:
            PipedreamToolsRegistry: The current tools registry
        """
        return self.tools_registry
    
    def get_all_sdk_tools(self, session_data=None) -> List[ChatCompletionsToolDefinition]:
        """
        Get all discovered tools as Azure SDK definitions.
        
        Returns:
            List[ChatCompletionsToolDefinition]: All tools ready for LLM
        """
        return self.tools_registry.get_all_sdk_tools()

    def execute_tool(
        self,
        external_user_id: str,
        app_slug: str,
        tool_name: str,
        tool_args: dict,
        oauth_app_id: Optional[str] = None,
        tool_mode: Optional[str] = None,
        jwt_token: Optional[str] = None
    ) -> dict:
        """
        Execute a tool via the Pipedream MCP endpoint using JSON-RPC protocol (direct, no Inspector proxy).
        """
        # Route local MCP tools using the same executor as ToolRegistry
        from jarvus_app.services.tools.web_search_tools import register_web_search_tools
        from jarvus_app.services.tool_registry import ToolRegistry
        # Create a temporary ToolRegistry and register local tools
        local_registry = ToolRegistry()
        register_web_search_tools(local_registry)
        tool = local_registry.get_tool(tool_name)
        if tool and tool.executor:
            payload = {"parameters": tool_args}
            return tool.executor(tool_name, payload, jwt_token=jwt_token)
        else:
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
            try:
                print(f"==========Pipe Dream Tool Call==========")
                print(f"[DEBUG] Request body: {json.dumps(body, indent=2)}")
                response = requests.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=30  # Reduced timeout to 30 seconds
                )
                print(f"[DEBUG] Request completed at: {datetime.now()}")
                print(f"[DEBUG] Tool exec POST status: {response.status_code}")
                print("==========================================")
            except requests.exceptions.Timeout:
                print(f"[ERROR] Request timed out after 30 seconds")
                return {"error": "Request timed out after 30 seconds"}
            except requests.exceptions.ConnectionError as e:
                print(f"[ERROR] Connection error: {e}")
                return {"error": f"Connection error: {e}"}
            except Exception as e:
                print(f"[ERROR] Exception during tool exec POST: {e}")
                return {"error": f"Request failed: {e}"}
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

    def get_tool_to_app_mapping(self, session_data=None) -> Dict[str, str]:
        """
        Get a mapping of tool names to their app slugs.
        
        Returns:
            Dict[str, str]: Mapping of tool names to app slugs
        """
        return self.tools_registry.get_tool_to_app_mapping()


# Create singleton instance
pipedream_tool_service = PipedreamToolService() 

def ensure_tools_discovered(user_id, session_data=None):
    """
    Ensure tools are discovered for the user.
    Call this from login or before agent requests.
    """
    from jarvus_app.services.pipedream_tool_registry import pipedream_tool_service
    
    logger.info(f"Discovering tools for user {user_id}")
    tools_registry = pipedream_tool_service.discover_all_tools(user_id)
    logger.info(f"Discovered {len(tools_registry._tools)} tools for user {user_id}")


def get_or_discover_tools_for_user_apps(user_id, app_slugs, freshness_minutes=60):
    """
    For each app_slug, check the DB cache for tools for this user. If fresh, use cache. If not, fetch from Pipedream, update cache, and return tools as SDK definitions.
    Returns a list of ChatCompletionsToolDefinition for all requested app_slugs.
    """
    from jarvus_app.services.pipedream_tool_registry import pipedream_tool_service
    from jarvus_app import db
    now = datetime.utcnow()
    fresh_cutoff = now - timedelta(minutes=freshness_minutes)
    sdk_tools = []
    for app_slug in app_slugs:
        cache = ToolDiscoveryCache.query.filter_by(user_id=str(user_id), app_slug=app_slug).first()
        use_cache = False
        if cache and cache.discovered_at > fresh_cutoff and cache.sdk_tools_blob:
            try:
                cached_sdk_tools = pickle.loads(cache.sdk_tools_blob)
                sdk_tools.extend(cached_sdk_tools)
                use_cache = True
            except Exception as e:
                print(f"[ToolDiscoveryCache] Failed to load pickled SDK tools for {app_slug}: {e}")
        if not use_cache:
            # Fetch from Pipedream and update cache
            tools_data = pipedream_tool_service.get_tools_for_app(user_id, app_slug)
            if tools_data and "tools" in tools_data:
                # Convert to SDK definitions
                pipedream_tool_service.tools_registry.register_app_tools(app_slug, app_slug, tools_data)
                sdk_tools_list = [tool.to_sdk_definition() for tool in pipedream_tool_service.tools_registry._tools.values() 
                                 if tool.app_slug == app_slug and tool.is_active]
                sdk_tools.extend(sdk_tools_list)
                # Update or create cache
                tools_json = json.dumps(tools_data["tools"])
                sdk_tools_blob = pickle.dumps(sdk_tools_list)
                if cache:
                    cache.tools_json = tools_json
                    cache.discovered_at = now
                    cache.sdk_tools_blob = sdk_tools_blob
                else:
                    cache = ToolDiscoveryCache(
                        user_id=str(user_id),
                        app_slug=app_slug,
                        tools_json=tools_json,
                        discovered_at=now,
                        sdk_tools_blob=sdk_tools_blob
                    )
                    db.session.add(cache)
                db.session.commit()
    return sdk_tools 