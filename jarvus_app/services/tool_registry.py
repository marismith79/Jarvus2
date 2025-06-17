"""
Tool Registry System for managing tool metadata and discovery.
This module provides a framework for registering and discovering tools
that are available through various MCP servers.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from azure.ai.inference.models import ChatCompletionsToolDefinition, FunctionDefinition

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
    server_path: str                # e.g., 'gmail', 'calendar'
    requires_auth: bool = True
    is_active: bool = True
    executor: Optional[Callable] = None
    parameters: Optional[List[ToolParameter]] = None
    result_formatter: Optional[Callable] = None

    def to_sdk_definition(self) -> ChatCompletionsToolDefinition:
        """Convert this metadata into an Azure SDK ChatCompletionsToolDefinition."""
        # Build JSON schema for function parameters
        props: Dict[str, Any] = {}
        required: List[str] = []

        if self.parameters:
            for p in self.parameters:
                schema: Dict[str, Any] = {"type": p.type, "description": p.description}
                if p.type == "array" and p.items_type:
                    schema["items"] = {"type": p.items_type}
                props[p.name] = schema
                if p.required:
                    required.append(p.name)
        else:
            # Default single-query parameter
            props = {
                "query": {
                    "type": "string",
                    "description": "Search query or parameters for the operation"
                }
            }

        func_def = FunctionDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": props,
                "required": required
            }
        )
        return ChatCompletionsToolDefinition(function=func_def)


class ToolRegistry:
    """Registry for managing available tools and their metadata."""

    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}
        print("Tool Registry initialized")

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
        return [t for t in self._tools.values() if t.is_active]

    def get_tools_by_category(self, category: ToolCategory) -> List[ToolMetadata]:
        """Get metadata for all tools in a specific category."""
        return [t for t in self._tools.values() if t.category == category]

    def get_sdk_tools(self) -> List[ChatCompletionsToolDefinition]:
        """Return all active tools as Azure SDK definitions."""
        return [m.to_sdk_definition() for m in self._tools.values() if m.is_active]

    def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any] = None,
        jwt_token: Optional[str] = None
    ) -> Any:
        """Execute a tool operation and format the result."""
        tool = self.get_tool(tool_name)
        if not tool or not tool.is_active:
            raise ValueError(f"Tool not available: {tool_name}")

        executor = tool.executor or mcp_client.execute_tool
        raw_result = executor(
            tool_name=tool_name,
            parameters=parameters or {},
            jwt_token=jwt_token
        )
        return self._handle_tool_response(tool, raw_result)

    def _handle_tool_response(self, tool: ToolMetadata, raw_result: Any) -> Any:
        """Handle and optionally format the raw tool execution result."""
        print(f"\nTool Registry: Got result from {tool.name}")
        if tool.result_formatter:
            return tool.result_formatter(raw_result)
        return raw_result


def format_tool_result(result: Any) -> str:
    """Format generic tool result into a human-readable string."""
    if isinstance(result, list):
        return "\n".join(f"- {item}" for item in result)
    if isinstance(result, dict):
        return "\n".join(f"{k}: {v}" for k, v in result.items())
    return str(result)


def format_gmail_result(result: Any) -> Dict[str, Any]:
    """Format Gmail tool results while preserving dictionary structure."""
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        return {"messages": result}
    return {"result": str(result)}


def format_calendar_result(result: Any) -> Dict[str, Any]:
    """Format Calendar tool results while preserving dictionary structure."""
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        return {"events": result}
    return {"result": str(result)}


# Instantiate registry and register default tools

tool_registry = ToolRegistry()

tool_registry.register(ToolMetadata(
    name="gmail",
    description="Access Gmail via MCP server",
    category=ToolCategory.EMAIL,
    server_path="gmail",
    requires_auth=True,
    executor=mcp_client.execute_tool,
    parameters=[
        ToolParameter("query", "string", "Gmail search query", required=False),
        ToolParameter("to", "string", "Recipient email address", required=False),
        ToolParameter("subject", "string", "Email subject line", required=False),
        ToolParameter("body", "string", "Email message body", required=False),
    ],
    result_formatter=format_gmail_result
))

tool_registry.register(ToolMetadata(
    name="calendar",
    description="Access Google Calendar via MCP server",
    category=ToolCategory.CALENDAR,
    server_path="calendar",
    requires_auth=True,
    executor=mcp_client.execute_tool,
    parameters=[
        ToolParameter("time_min", "string", "Start time for events (ISO)", required=False),
        ToolParameter("time_max", "string", "End time for events (ISO)", required=False),
        ToolParameter("summary", "string", "Event summary/title", required=False),
        ToolParameter("description", "string", "Event description", required=False),
        ToolParameter("start", "string", "Event start time (ISO)", required=False),
        ToolParameter("end", "string", "Event end time (ISO)", required=False),
        ToolParameter("event_id", "string", "Calendar event ID", required=False),
    ],
    result_formatter=format_calendar_result
))