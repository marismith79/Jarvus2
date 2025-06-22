"""Vercel tool registrations."""

from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_tool_result

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def register_vercel_tools(registry: 'ToolRegistry') -> None:
    """Register all Vercel-related tools."""
    
    registry.register(ToolMetadata(
        name="generate_ui",
        description="Generate UI components using v0-1.5-md model",
        category=ToolCategory.CUSTOM,
        server_path="vercel",
        requires_auth=False,
        parameters=[
            ToolParameter("prompt", "string", "Text prompt describing the UI component to generate", required=True),
            ToolParameter("framework", "string", "Framework to use for UI generation (e.g., vite, next.js)", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="generate_json_schema",
        description="Generate JSON schema for UI components using v0-1.5-md",
        category=ToolCategory.CUSTOM,
        server_path="vercel",
        requires_auth=False,
        parameters=[
            ToolParameter("description", "string", "Description of the UI component for schema generation", required=True),
        ],
        result_formatter=format_tool_result
    )) 