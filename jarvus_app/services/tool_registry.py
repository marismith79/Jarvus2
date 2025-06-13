"""
Tool Registry System for managing and executing LLM tools.
This module provides a framework for registering, managing, and executing tools
that can be used by the LLM to perform various actions.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ToolCategory(Enum):
    """Categories for different types of tools."""

    FILE_SYSTEM = "file_system"
    DATABASE = "database"
    NETWORK = "network"
    SYSTEM = "system"
    CUSTOM = "custom"


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""

    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass
class Tool:
    """Base class for all tools that can be used by the LLM."""

    name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter]
    function: Callable
    requires_auth: bool = False
    is_active: bool = True


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a new tool."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool."""
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' is not registered")
        del self._tools[tool_name]

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(tool_name)

    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_active_tools(self) -> List[Tool]:
        """Get all active tools."""
        return [tool for tool in self._tools.values() if tool.is_active]

    def get_tools_by_category(self, category: ToolCategory) -> List[Tool]:
        """Get all tools in a specific category."""
        return [
            tool for tool in self._tools.values() if tool.category == category
        ]

    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool with the given parameters."""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        if not tool.is_active:
            raise ValueError(f"Tool '{tool_name}' is not active")

        # Validate required parameters
        for param in tool.parameters:
            if param.required and param.name not in kwargs:
                if param.default is not None:
                    kwargs[param.name] = param.default
                else:
                    raise ValueError(
                        f"Required parameter '{param.name}' not provided"
                    )

        # Execute the tool
        return tool.function(**kwargs)

    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get the JSON schema for a tool."""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: {
                        "type": param.type,
                        "description": param.description,
                    }
                    for param in tool.parameters
                },
                "required": [
                    param.name for param in tool.parameters if param.required
                ],
            },
        }


# Create a singleton instance
tool_registry = ToolRegistry()
