"""
Google Workspace MCP tools registration.
This file defines high-level tool descriptions for the LLM to understand available capabilities.
"""

from typing import Any, Dict, List, Optional, cast, Callable

from .mcp_client import mcp_client
from .tool_registry import Tool, ToolCategory, ToolParameter, tool_registry

def format_tool_result(result: Any) -> str:
    """Format tool results into a human-readable string."""
    if isinstance(result, list):
        return "\n".join([f"- {item}" for item in result])
    elif isinstance(result, dict):
        return "\n".join([f"{k}: {v}" for k, v in result.items()])
    return str(result)

def generate_openai_schema(name: str, description: str, parameters: List[ToolParameter]) -> Dict[str, Any]:
    """Generate OpenAI function calling schema from tool parameters."""
    properties = {}
    required = []
    
    for param in parameters:
        properties[param.name] = {
            "type": param.type,
            "description": param.description
        }
        if param.required:
            required.append(param.name)
    
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }

# --- Tool metadata definitions ---
TOOL_DEFS: List[Dict[str, Any]] = [
    {
        "name": "gmail",
        "description": "Access and manage Gmail functionality including reading, sending, and organizing emails. The MCP server handles all Gmail operations including email management, label operations, thread management, draft operations, and settings configuration.",
        "category": ToolCategory.CUSTOM,
        "parameters": [
            ToolParameter(
                "operation",
                "string",
                "The Gmail operation to perform (e.g., 'list_emails', 'search_emails', 'send_email', 'manage_labels')",
                required=True
            ),
            ToolParameter(
                "parameters",
                "object",
                "Parameters specific to the requested operation",
                required=True
            )
        ],
        "function": mcp_client.handle_gmail_operation,
        "requires_auth": True,
    }
]

# --- Register all tools ---
for tool_def in TOOL_DEFS:
    # Generate OpenAI schema from parameters
    tool_def["openai_schema"] = generate_openai_schema(
        tool_def["name"],
        tool_def["description"],
        tool_def["parameters"]
    )
    
    tool = Tool(
        name=cast(str, tool_def["name"]),
        description=cast(str, tool_def["description"]),
        category=cast(ToolCategory, tool_def["category"]),
        parameters=cast(List[ToolParameter], tool_def["parameters"]),
        function=cast(Any, tool_def["function"]),
        requires_auth=cast(bool, tool_def["requires_auth"]),
        result_formatter=format_tool_result,
    )
    tool_registry.register(tool)
