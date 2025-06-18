"""Calendar tool registrations."""

from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_calendar_result

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def register_calendar_tools(registry: 'ToolRegistry') -> None:
    """Register all Calendar-related tools."""
    
    registry.register(ToolMetadata(
        name="calendar_list",
        description="List calendar events",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("max_results", "integer", "Maximum number of results to return", required=False),
            ToolParameter("time_min", "string", "Start time for events (ISO format)", required=False),
            ToolParameter("time_max", "string", "End time for events (ISO format)", required=False),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="calendar_create",
        description="Create a new calendar event",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("summary", "string", "Event summary/title", required=True),
            ToolParameter("start_time", "string", "Event start time (ISO format)", required=True),
            ToolParameter("end_time", "string", "Event end time (ISO format)", required=True),
            ToolParameter("description", "string", "Event description", required=False),
            ToolParameter("location", "string", "Event location", required=False),
            ToolParameter("attendees", "array", "List of attendee email addresses", required=False, items_type="string"),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="calendar_get",
        description="Get a specific calendar event",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("event_id", "string", "ID of the event to retrieve", required=True),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="calendar_update",
        description="Update an existing calendar event",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("event_id", "string", "ID of the event to update", required=True),
            ToolParameter("summary", "string", "Event summary/title", required=False),
            ToolParameter("start_time", "string", "Event start time (ISO format)", required=False),
            ToolParameter("end_time", "string", "Event end time (ISO format)", required=False),
            ToolParameter("description", "string", "Event description", required=False),
            ToolParameter("location", "string", "Event location", required=False),
            ToolParameter("attendees", "array", "List of attendee email addresses", required=False, items_type="string"),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="calendar_delete",
        description="Delete a calendar event",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("event_id", "string", "ID of the event to delete", required=True),
        ],
        result_formatter=format_calendar_result
    )) 