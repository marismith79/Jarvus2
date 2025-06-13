"""
Google Workspace MCP tools registration (concise version).
This file only defines tool metadata and registers them with the registry.
"""

from typing import Any, Dict, List, Optional, cast

from .mcp_client import mcp_client
from .tool_registry import Tool, ToolCategory, ToolParameter, tool_registry

# --- Tool metadata definitions ---
TOOL_DEFS: List[Dict[str, Any]] = [
    {
        "name": "list_emails",
        "description": "List recent emails from your inbox with optional filtering",
        "category": ToolCategory.CUSTOM,
        "parameters": [
            ToolParameter(
                "max_results",
                "integer",
                "Maximum number of emails to return",
                required=False,
                default=5,
            ),
            ToolParameter(
                "query",
                "string",
                "Gmail query syntax for filtering emails",
                required=False,
            ),
        ],
        "function": mcp_client.list_emails,
        "requires_auth": True,
    },
    {
        "name": "search_emails",
        "description": "Advanced email search with Gmail query syntax",
        "category": ToolCategory.CUSTOM,
        "parameters": [
            ToolParameter(
                "query", "string", "Gmail query syntax for searching emails"
            ),
            ToolParameter(
                "max_results",
                "integer",
                "Maximum number of emails to return",
                required=False,
                default=10,
            ),
        ],
        "function": mcp_client.search_emails,
        "requires_auth": True,
    },
    {
        "name": "send_email",
        "description": "Send new emails with support for CC and BCC",
        "category": ToolCategory.CUSTOM,
        "parameters": [
            ToolParameter("to", "string", "Recipient email address"),
            ToolParameter("subject", "string", "Email subject"),
            ToolParameter("body", "string", "Email body content"),
            ToolParameter("cc", "string", "CC email address", required=False),
            ToolParameter(
                "bcc", "string", "BCC email address", required=False
            ),
        ],
        "function": mcp_client.send_email,
        "requires_auth": True,
    },
    {
        "name": "list_events",
        "description": "List upcoming calendar events with date range filtering",
        "category": ToolCategory.CUSTOM,
        "parameters": [
            ToolParameter(
                "max_results",
                "integer",
                "Maximum number of events to return",
                required=False,
                default=10,
            ),
            ToolParameter(
                "time_min",
                "string",
                "Start time in ISO 8601 format (e.g., 2024-01-01T00:00:00Z)",
                required=False,
            ),
            ToolParameter(
                "time_max",
                "string",
                "End time in ISO 8601 format (e.g., 2024-12-31T23:59:59Z)",
                required=False,
            ),
        ],
        "function": mcp_client.list_events,
        "requires_auth": True,
    },
    {
        "name": "create_event",
        "description": "Create new calendar events with attendees",
        "category": ToolCategory.CUSTOM,
        "parameters": [
            ToolParameter("summary", "string", "Event title"),
            ToolParameter(
                "start",
                "string",
                "Start time in ISO 8601 format (e.g., 2024-01-24T10:00:00Z)",
            ),
            ToolParameter(
                "end",
                "string",
                "End time in ISO 8601 format (e.g., 2024-01-24T11:00:00Z)",
            ),
            ToolParameter(
                "location", "string", "Event location", required=False
            ),
            ToolParameter(
                "description", "string", "Event description", required=False
            ),
            ToolParameter(
                "attendees",
                "array",
                "List of attendee email addresses",
                required=False,
            ),
        ],
        "function": mcp_client.create_event,
        "requires_auth": True,
    },
]

# --- Register all tools ---
for tool_def in TOOL_DEFS:
    tool = Tool(
        name=cast(str, tool_def["name"]),
        description=cast(str, tool_def["description"]),
        category=cast(ToolCategory, tool_def["category"]),
        parameters=cast(List[ToolParameter], tool_def["parameters"]),
        function=cast(Any, tool_def["function"]),
        requires_auth=cast(bool, tool_def["requires_auth"]),
    )
    tool_registry.register(tool)
