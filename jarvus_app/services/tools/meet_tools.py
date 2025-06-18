"""Google Meet tool registrations."""

from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_tool_result

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def register_meet_tools(registry: 'ToolRegistry') -> None:
    """Register all Google Meet-related tools."""
    
    registry.register(ToolMetadata(
        name="meet_create",
        description="Create a new Google Meet meeting",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="meet",
        requires_auth=True,
        parameters=[
            ToolParameter("summary", "string", "Meeting summary/title", required=True),
            ToolParameter("start_time", "string", "Meeting start time (ISO format)", required=True),
            ToolParameter("duration_minutes", "integer", "Duration of the meeting in minutes", required=True),
            ToolParameter("description", "string", "Meeting description", required=False),
            ToolParameter("attendees", "array", "List of attendee email addresses", required=False, items_type="string"),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="meet_get",
        description="Get details of a Google Meet meeting",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="meet",
        requires_auth=True,
        parameters=[
            ToolParameter("meeting_id", "string", "ID of the meeting to retrieve", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="meet_update",
        description="Update a Google Meet meeting",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="meet",
        requires_auth=True,
        parameters=[
            ToolParameter("meeting_id", "string", "ID of the meeting to update", required=True),
            ToolParameter("summary", "string", "Meeting summary/title", required=False),
            ToolParameter("start_time", "string", "Meeting start time (ISO format)", required=False),
            ToolParameter("duration_minutes", "integer", "Duration of the meeting in minutes", required=False),
            ToolParameter("description", "string", "Meeting description", required=False),
            ToolParameter("attendees", "array", "List of attendee email addresses", required=False, items_type="string"),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="meet_delete",
        description="Delete a Google Meet meeting",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="meet",
        requires_auth=True,
        parameters=[
            ToolParameter("meeting_id", "string", "ID of the meeting to delete", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="meet_list",
        description="List Google Meet meetings",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="meet",
        requires_auth=True,
        parameters=[
            ToolParameter("max_results", "integer", "Maximum number of results to return", required=False),
            ToolParameter("time_min", "string", "Start time for meetings (ISO format)", required=False),
            ToolParameter("time_max", "string", "End time for meetings (ISO format)", required=False),
        ],
        result_formatter=format_tool_result
    )) 