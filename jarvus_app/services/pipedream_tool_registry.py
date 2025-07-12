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
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from azure.ai.inference.models import ChatCompletionsToolDefinition, FunctionDefinition
import pickle

from .pipedream_auth_service import pipedream_auth_service
from jarvus_app.models.tool_discovery_cache import ToolDiscoveryCache
from jarvus_app.config import ALL_PIPEDREAM_APPS

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
            tool_name = tool_data.get("name", "")
            # print(f"[DEBUG] Registering tool: {tool_name}")
            # print(f"[DEBUG] Tool description: {tool_data.get('description', '')}")
            # print(f"[DEBUG] Tool input schema: {tool_data.get('inputSchema', {})}")
            
            tool = PipedreamTool(
                name=tool_name,
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

    def get_tool_to_app_mapping(self) -> Dict[str, str]:
        """Get a mapping of tool names to their app slugs."""
        mapping = {}
        for app_slug, app_tools in self._apps.items():
            for tool in app_tools.tools:
                mapping[tool.name] = app_slug
        return mapping


class PipedreamToolService:
    """Service for managing Pipedream MCP tool discovery and execution."""
    
    def __init__(self):
        """Initialize the Pipedream tool service."""
        self.tools_registry = PipedreamToolsRegistry()
        self._initialized = False
        self._initialization_lock = False  # Simple lock to prevent concurrent initialization
    
    def ensure_initialized(self, user_id: str, force_refresh: bool = False) -> None:
        """
        Ensure tools are discovered and cached. Only discovers if not already done or if forced.
        
        Args:
            user_id: The user ID to discover tools for
            force_refresh: If True, force rediscovery even if already initialized
        """
        # Check if we need to initialize
        if self._initialized and not force_refresh and self.tools_registry.is_fresh():
            logger.debug("Tools already initialized and fresh, skipping discovery")
            return
        
        # Prevent concurrent initialization
        if self._initialization_lock:
            logger.debug("Tool initialization already in progress, waiting...")
            return
        
        try:
            self._initialization_lock = True
            logger.info(f"Initializing tools for user {user_id}")
            self.discover_all_tools(user_id, force_refresh=force_refresh)
            self._initialized = True
            logger.info("Tool initialization completed successfully")
        except Exception as e:
            logger.error(f"Failed to initialize tools: {str(e)}")
            raise
        finally:
            self._initialization_lock = False
    
    def reset_initialization(self) -> None:
        """
        Reset the initialization state, forcing rediscovery on next ensure_initialized call.
        Useful for testing or when you need to force a refresh.
        """
        self._initialized = False
        self._initialization_lock = False
        self.tools_registry.clear()
        logger.info("Tool initialization state reset")
    
    def is_initialized(self) -> bool:
        """
        Check if tools have been initialized and are fresh.
        
        Returns:
            bool: True if tools are initialized and fresh, False otherwise
        """
        return self._initialized and self.tools_registry.is_fresh()
    
    def get_initialization_status(self) -> dict:
        """
        Get detailed initialization status for debugging.
        
        Returns:
            dict: Status information including initialized flag, lock status, and freshness
        """
        return {
            'initialized': self._initialized,
            'initialization_lock': self._initialization_lock,
            'registry_fresh': self.tools_registry.is_fresh(),
            'discovered_at': self.tools_registry._discovered_at,
            'apps_count': len(self.tools_registry._apps),
            'total_tools': len(self.tools_registry.get_all_sdk_tools())
        }

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
            # print(f"[DEBUG] Tool list POST URL: {url}")
            # print(f"[DEBUG] Tool list POST headers: {headers}")
            # print(f"[DEBUG] Tool list POST body: {body}")
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=30
                )
                # print(f"[DEBUG] Tool list POST status: {response.status_code}")
                # print(f"[DEBUG] Tool list POST response: {response.text}")
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
                
                # Log all available tool names for debugging
                tool_names = [tool.get("name", "unknown") for tool in tools]
                # print(f"[DEBUG] Available tool names for {app_slug}: {tool_names}")
                
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
    
    def discover_all_tools(self, user_id, force_refresh=False):
        """
        Discover tools for a user from hardcoded list of apps.
        
        Args:
            user_id: The user's ID in your system
            force_refresh: If True, force rediscovery even if already fresh
            
        Returns:
            PipedreamToolsRegistry: Registry containing all discovered tools
        """
        print(f"Discovering tools for user: {user_id}")
        
        # Only clear if forcing refresh or if not fresh
        if force_refresh or not self.tools_registry.is_fresh():
            self.tools_registry.clear()
        else:
            print("Tools registry is fresh, skipping discovery")
            return self.tools_registry
        
        # Hardcoded list of app slugs to discover
        all_possible_apps = ALL_PIPEDREAM_APPS

        for app in all_possible_apps:
            app_slug = app["slug"]
            app_name = app["name"]
            
            print(f"Fetching tools for app: {app_slug}")
            tools_data = self.get_tools_for_app(user_id, app_slug)
            # print(f"Tools data: {tools_data}")
            
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
        Uses session registry if available, otherwise falls back to global registry.
        
        Returns:
            List[ChatCompletionsToolDefinition]: All tools ready for LLM
        """
        # Try to use session registry first
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
            # print(f"[DEBUG] Tool exec POST URL: {url}")
            # print(f"[DEBUG] Tool exec POST headers: {headers}")
            # print(f"[DEBUG] Tool exec POST body: {body}")
            # print(f"[DEBUG] External user ID: {external_user_id}")
            # print(f"[DEBUG] App slug: {app_slug}")
            # print(f"[DEBUG] Tool name: {tool_name}")
            # print(f"[DEBUG] Tool args: {tool_args}")
            try:
                print(f"==========Pipe Dream Tool Call==========")
                # print(f"[DEBUG] Request started at: {datetime.now()}")
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
                # print(f"[DEBUG] Tool exec POST response: {response.text}")
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

    def get_sdk_tools_for_apps(self, app_slugs: List[str]) -> List[ChatCompletionsToolDefinition]:
        """
        Get SDK tools for the specified app slugs.
        Args:
            app_slugs: List of app slugs to get tools for
        Returns:
            List[ChatCompletionsToolDefinition]: Tools for the specified apps
        """
        if not self.tools_registry.is_fresh():
            logger.warning("Tools registry is stale, tools need to be rediscovered")
            return []
        sdk_tools = []
        for app_slug in app_slugs:
            sdk_tools.extend(self.tools_registry.get_tools_by_app(app_slug))
        return sdk_tools

    def get_tool_to_app_mapping(self) -> Dict[str, str]:
        """
        Get a mapping of tool names to their app slugs.
        Only uses in-memory or DB cache. Session is not used for tool registry anymore.
        Returns:
            Dict[str, str]: Mapping of tool names to app slugs
        """
        if not self.tools_registry.is_fresh():
            logger.warning("Tools registry is stale, tools need to be rediscovered")
            return {}
        return self.tools_registry.get_tool_to_app_mapping()


# Create singleton instance
pipedream_tool_service = PipedreamToolService() 

def ensure_tools_discovered(user_id, session_data=None, force_refresh=False):
    """
    Ensure tools are discovered for the user if the registry is not fresh.
    Use only the DB cache or in-memory registry. Do NOT store the registry in the session.
    Call this from login or before agent requests.
    
    Args:
        user_id: The user ID to discover tools for
        session_data: Deprecated, kept for compatibility
        force_refresh: If True, force rediscovery even if already initialized
    """
    from jarvus_app.services.pipedream_tool_registry import pipedream_tool_service
    
    # Use the new initialization method that caches properly
    pipedream_tool_service.ensure_initialized(str(user_id), force_refresh=force_refresh)


def get_session_tool_registry(session_data):
    """
    Get the tool registry from session data.
    Returns None if not found or not fresh.
    """
    if not session_data or 'tool_registry' not in session_data:
        return None
    
    registry_data = session_data['tool_registry']
    if not registry_data.get('is_fresh', False):
        return None
    
    # Reconstruct the registry from session data
    from jarvus_app.services.pipedream_tool_registry import PipedreamToolsRegistry
    registry = PipedreamToolsRegistry()
    registry._apps = registry_data.get('apps', {})
    registry._discovered_at = registry_data.get('discovered_at')
    
    return registry 

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
                sdk_tools_list = pipedream_tool_service.tools_registry.get_tools_by_app(app_slug)
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