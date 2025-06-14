"""
Tool Registry System for managing tool metadata and discovery.
This module provides a framework for registering and discovering tools
that are available through various MCP servers.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ToolCategory(Enum):
    """Categories for different types of tools."""
    EMAIL = "email"
    CALENDAR = "calendar"
    CUSTOM = "custom"


@dataclass
class ToolMetadata:
    """Metadata for a tool available through the MCP server."""
    name: str
    description: str
    category: ToolCategory
    server_path: str  # The path on the MCP server for this tool (e.g., 'gmail', 'calendar')
    requires_auth: bool = True
    is_active: bool = True

    @property
    def openai_schema(self) -> Dict:
        """Generate OpenAI function schema for this tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": f"The operation to perform with {self.name}",
                            "enum": self._get_available_operations()
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Operation-specific parameters"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }

    def _get_available_operations(self) -> List[str]:
        """Get list of available operations for this tool."""
        # This could be expanded to be more dynamic based on the tool type
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

    def register(self, tool: ToolMetadata) -> None:
        """Register a new tool's metadata."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

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


# Create a singleton instance
tool_registry = ToolRegistry()

# Register default tools
tool_registry.register(ToolMetadata(
    name="gmail",
    description="Access to Gmail functionality through MCP server",
    category=ToolCategory.EMAIL,
    server_path="gmail",
    requires_auth=True
))

tool_registry.register(ToolMetadata(
    name="calendar",
    description="Access to Google Calendar functionality through MCP server",
    category=ToolCategory.CALENDAR,
    server_path="calendar",
    requires_auth=True
))
