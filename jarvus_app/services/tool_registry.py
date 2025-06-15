"""
Tool Registry System for managing tool metadata and discovery.
This module provides a framework for registering and discovering tools
that are available through various MCP servers.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Callable

from .mcp_client import mcp_client, ToolExecutionError


class ToolCategory(Enum):
    """Categories for different types of tools."""
    EMAIL = "email"
    CALENDAR = "calendar"
    CUSTOM = "custom"


@dataclass
class ToolParameter:
    """Parameter definition for a tool."""
    name: str
    type: str
    description: str
    required: bool = False
    items_type: Optional[str] = None


@dataclass
class ToolMetadata:
    """Metadata for a tool available through the MCP server."""
    name: str
    description: str
    category: ToolCategory
    server_path: str  # The path on the MCP server for this tool (e.g., 'gmail', 'calendar')
    requires_auth: bool = True
    is_active: bool = True
    executor: Optional[Callable] = None  # Function to execute the tool operation
    parameters: Optional[List[ToolParameter]] = None
    result_formatter: Optional[Callable] = None

    @property
    def openai_schema(self) -> Dict:
        """Generate OpenAI function schema for this tool."""
        if self.parameters:
            properties = {}
            required = []
            for param in self.parameters:
                param_schema = {
                    "type": param.type,
                    "description": param.description
                }
                # Add items type for array parameters
                if param.type == "array" and param.items_type:
                    param_schema["items"] = {"type": param.items_type}
                properties[param.name] = param_schema
                if param.required:
                    required.append(param.name)
            
            return {
                "type": "function",
                "function": {
                    "name": self.name,
                    "description": self.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            }
        else:
            # Default schema for tools without explicit parameters
            return {
                "type": "function",
                "function": {
                    "name": self.name,
                    "description": self.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query or parameters for the operation"
                            }
                        }
                    }
                }
            }

    def _get_available_operations(self) -> List[str]:
        """Get list of available operations for this tool."""
        if self.category == ToolCategory.EMAIL:
            return [
                "list_emails",
                "search_emails",
                "send_email",
                "create_draft",
                "send_draft"
            ]
        elif self.category == ToolCategory.CALENDAR:
            return [
                "list_events",
                "create_event",
                "update_event",
                "delete_event"
            ]
        return []


class ToolRegistry:
    """Registry for managing available tools and their metadata."""

    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}
        print("\nTool Registry initialized")

    def register(self, tool: ToolMetadata) -> None:
        """Register a new tool's metadata."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
        print(f"Registered tool: {tool.name}")

    def get_tool(self, tool_name: str) -> Optional[ToolMetadata]:
        """Get a tool's metadata by name."""
        return self._tools.get(tool_name)

    def get_all_tools(self) -> List[ToolMetadata]:
        """Get metadata for all registered tools."""
        return list(self._tools.values())

    def get_active_tools(self) -> List[ToolMetadata]:
        """Get metadata for all active tools."""
        return [tool for tool in self._tools.values() if tool.is_active]

    def get_tools_by_category(self, category: ToolCategory) -> List[ToolMetadata]:
        """Get metadata for all tools in a specific category."""
        return [tool for tool in self._tools.values() if tool.category == category]

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any] = None, jwt_token: Optional[str] = None) -> Any:
        """
        Execute a tool operation.
        
        Args:
            tool_name: The name of the tool to execute
            parameters: Optional parameters for the operation
            jwt_token: Optional JWT token for authentication
            
        Returns:
            The result of the tool execution
            
        Raises:
            ValueError: If the tool is not found or not active
            ToolExecutionError: If tool execution fails
        """
        print("\n=== Tool Registry Debug ===")
        print(f"Executing tool: {tool_name}")
        print(f"Parameters: {parameters}")
        print(f"JWT Token provided: {jwt_token is not None}")
        if jwt_token:
            print(f"JWT Token first 10 chars: {jwt_token[:10]}...")
        print("=========================\n")
        
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
            
        if not tool.is_active:
            raise ValueError(f"Tool is not active: {tool_name}")
            
        # Use tool's executor if provided, otherwise use MCP client
        executor = tool.executor or mcp_client.execute_tool
        result = executor(tool_name=tool_name, parameters=parameters or {}, jwt_token=jwt_token)
        
        # Format result if formatter is provided
        if tool.result_formatter:
            return tool.result_formatter(result)
        return result


def format_tool_result(result: Any) -> str:
    """Format tool results into a human-readable string."""
    if isinstance(result, list):
        return "\n".join([f"- {item}" for item in result])
    elif isinstance(result, dict):
        return "\n".join([f"{k}: {v}" for k, v in result.items()])
    return str(result)


# Create singleton instance
tool_registry = ToolRegistry()

# Register default tools
tool_registry.register(ToolMetadata(
    name="gmail",
    description="Access to Gmail functionality through MCP server",
    category=ToolCategory.EMAIL,
    server_path="gmail",
    requires_auth=True,
    executor=mcp_client.execute_tool,
    result_formatter=format_tool_result,
    parameters=[
        ToolParameter(
            name="query",
            type="string",
            description="Gmail search query (e.g., 'in:inbox', 'from:someone@example.com')",
            required=False
        ),
        ToolParameter(
            name="to",
            type="string",
            description="Recipient email address for sending messages",
            required=False
        ),
        ToolParameter(
            name="subject",
            type="string",
            description="Email subject line",
            required=False
        ),
        ToolParameter(
            name="body",
            type="string",
            description="Email message body",
            required=False
        ),
        ToolParameter(
            name="message_id",
            type="string",
            description="Gmail message ID for specific message operations",
            required=False
        ),
        ToolParameter(
            name="add_labels",
            type="array",
            description="Labels to add to a message",
            required=False,
            items_type="string"
        ),
        ToolParameter(
            name="remove_labels",
            type="array",
            description="Labels to remove from a message",
            required=False,
            items_type="string"
        )
    ]
))

tool_registry.register(ToolMetadata(
    name="calendar",
    description="Access to Google Calendar functionality through MCP server",
    category=ToolCategory.CALENDAR,
    server_path="calendar",
    requires_auth=True,
    executor=mcp_client.execute_tool,
    result_formatter=format_tool_result,
    parameters=[
        ToolParameter(
            name="time_min",
            type="string",
            description="Start time for calendar events (ISO format)",
            required=False
        ),
        ToolParameter(
            name="time_max",
            type="string",
            description="End time for calendar events (ISO format)",
            required=False
        ),
        ToolParameter(
            name="summary",
            type="string",
            description="Event summary/title",
            required=False
        ),
        ToolParameter(
            name="description",
            type="string",
            description="Event description",
            required=False
        ),
        ToolParameter(
            name="start",
            type="string",
            description="Event start time (ISO format)",
            required=False
        ),
        ToolParameter(
            name="end",
            type="string",
            description="Event end time (ISO format)",
            required=False
        ),
        ToolParameter(
            name="event_id",
            type="string",
            description="Calendar event ID for specific event operations",
            required=False
        )
    ]
))
