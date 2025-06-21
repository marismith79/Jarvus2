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
from ..utils.scope_helpers import generate_scope_description


class ToolCategory(Enum):
    """Categories for different types of tools."""
    # Service Provider Categories
    GOOGLE_WORKSPACE = "google-workspace"
    MICROSOFT_365 = "microsoft-365"
    CUSTOM = "custom"
    
    # Google Workspace Service Categories
    GMAIL = "google-workspace.gmail"
    DRIVE = "google-workspace.drive"
    DOCS = "google-workspace.docs"
    SHEETS = "google-workspace.sheets"
    SLIDES = "google-workspace.slides"

    CALENDAR = "google-workspace.calendar"


@dataclass
class ToolParameter:
    """Parameter definition for a tool."""
    name: str
    type: str
    description: str
    required: bool = False
    items_type: Optional[str] = None  # for backward compatibility
    items: Optional["ToolParameter"] = None  # for nested arrays/objects

    def to_schema(self) -> dict:
        schema = {"type": self.type, "description": self.description}
        if self.type == "array":
            if self.items:
                schema["items"] = self.items.to_schema()
            elif self.items_type:
                schema["items"] = {"type": self.items_type}
        return schema


@dataclass
class ToolMetadata:
    """Metadata for a tool available through the MCP server."""
    name: str
    description: str
    category: ToolCategory
    server_path: str                
    requires_auth: bool = True
    is_active: bool = True
    executor: Optional[Callable] = None
    parameters: Optional[List[ToolParameter]] = None
    result_formatter: Optional[Callable] = None

    def to_sdk_definition(self, user_scopes: Optional[List[str]] = None, scope_description: Optional[str] = None) -> ChatCompletionsToolDefinition:
        """Convert this metadata into an Azure SDK ChatCompletionsToolDefinition."""
        props: Dict[str, Any] = {}
        required: List[str] = []

        if self.parameters:
            for p in self.parameters:
                schema = p.to_schema()
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

        # Add scope description to the tool description if available
        description = self.description
        if scope_description:
            description = f"{description}\n\n{scope_description}"

        func_def = FunctionDefinition(
            name=self.name,
            description=description,
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
        # print(f"Registered tool: {tool.name}")

    def get_tool(self, tool_name: str) -> Optional[ToolMetadata]:
        """Get a tool's metadata by name."""
        return self._tools.get(tool_name)

    def get_all_tools(self) -> List[ToolMetadata]:
        """Get metadata for all registered tools."""
        return list(self._tools.values())

    def get_active_tools(self) -> List[ToolMetadata]:
        """Get metadata for all active tools."""
        return [t for t in self._tools.values() if t.is_active]

    def get_tools_by_category(self, category: Optional[ToolCategory] = None) -> List[ToolMetadata]:
        """Get metadata for all tools in a specific category."""
        if category is None:
            return list(self._tools.values())
        return [t for t in self._tools.values() if t.category == category]

    def get_tools_by_category_dict(self) -> Dict[ToolCategory, List[ToolMetadata]]:
        """Get all tools grouped by category."""
        tools_by_category: Dict[ToolCategory, List[ToolMetadata]] = {}
        for tool in self._tools.values():
            if tool.category not in tools_by_category:
                tools_by_category[tool.category] = []
            tools_by_category[tool.category].append(tool)
        return tools_by_category

    def get_sdk_tools(self, user_scopes: Optional[List[str]] = None) -> List[ChatCompletionsToolDefinition]:
        """Return all active tools as Azure SDK definitions."""
        return [m.to_sdk_definition(user_scopes) for m in self._tools.values() if m.is_active]

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
        request_body = {
            "operation": tool_name,
            "parameters": parameters
        }
        raw_result = executor(
            tool_name=tool.server_path,
            payload=request_body,
            jwt_token=jwt_token
        )
        return self._handle_tool_response(tool, raw_result)

    def _handle_tool_response(self, tool: ToolMetadata, raw_result: Any) -> Any:
        """Handle and optionally format the raw tool execution result."""
        print(f"\nTool Registry: Got result from {tool.name}")
        if tool.result_formatter:
            return tool.result_formatter(raw_result)
        return raw_result

    def get_tools_by_module(self, module_name: str, user_scopes: Optional[List[str]] = None) -> List[ChatCompletionsToolDefinition]:
        """Get tools from a specific module/file."""
        # Map frontend tool names to tool categories
        module_to_category = {
            'gmail': ToolCategory.GMAIL,
            'docs': ToolCategory.DOCS,
            'slides': ToolCategory.SLIDES,
            'sheets': ToolCategory.SHEETS,
            'drive': ToolCategory.DRIVE,
            'calendar': ToolCategory.CALENDAR,
        }
        
        category = module_to_category.get(module_name.lower())
        if category:
            # Generate scope description for this module
            scope_description = None
            if user_scopes:
                service_names = {
                    ToolCategory.GMAIL: "Gmail",
                    ToolCategory.CALENDAR: "Calendar", 
                    ToolCategory.DRIVE: "Drive",
                    ToolCategory.DOCS: "Docs",
                    ToolCategory.SHEETS: "Sheets",
                    ToolCategory.SLIDES: "Slides"
                }
                service_name = service_names.get(category, module_name.title())
                scope_description = generate_scope_description(user_scopes, service_name)
            
            # Debug logging to help diagnose issues
            tools = [m.to_sdk_definition(scope_description=scope_description) 
                    for m in self._tools.values() 
                    if m.is_active and m.category == category]
            
            print(f"Found {len(tools)} tools for category {category}")
            return tools
        print(f"No category found for module {module_name}")
        return []

    def get_sdk_tools_by_modules(self, module_names: List[str], user_scopes: Optional[List[str]] = None) -> List[ChatCompletionsToolDefinition]:
        """Get tools from multiple modules."""
        all_tools = []
        for module_name in module_names:
            all_tools.extend(self.get_tools_by_module(module_name, user_scopes))
        return all_tools


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


# Instantiate registry
tool_registry = ToolRegistry()

# Import tool registrations from separate modules
from .tools import (
    register_gmail_tools,
    register_calendar_tools,
    register_drive_tools,
    register_docs_tools,
    register_sheets_tools,
    register_slides_tools
)

# Register all tools
register_gmail_tools(tool_registry)
register_calendar_tools(tool_registry)
register_drive_tools(tool_registry)
register_docs_tools(tool_registry)
register_sheets_tools(tool_registry)
register_slides_tools(tool_registry) 