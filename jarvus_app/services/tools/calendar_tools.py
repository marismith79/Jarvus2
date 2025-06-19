"""Calendar tool registrations."""

from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_calendar_result

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def register_calendar_tools(registry: 'ToolRegistry') -> None:
    """Register all Calendar-related tools."""
    
    registry.register(ToolMetadata(
        name="list_events",
        description="List calendar events",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
            ToolParameter("max_results", "integer", "Maximum number of results to return", required=False),
            ToolParameter("time_min", "string", "Start time for events (ISO format)", required=False),
            ToolParameter("time_max", "string", "End time for events (ISO format)", required=False),
            ToolParameter("single_events", "boolean", "Whether to expand recurring events", required=False),
            ToolParameter("order_by", "string", "Order of events (startTime)", required=False),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="create_event",
        description="Create a new calendar event",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
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
        name="get_event",
        description="Get a specific calendar event",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
            ToolParameter("event_id", "string", "ID of the event to retrieve", required=True),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="update_event",
        description="Update an existing calendar event",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
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
        name="delete_event",
        description="Delete a calendar event",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
            ToolParameter("event_id", "string", "ID of the event to delete", required=True),
        ],
        result_formatter=format_calendar_result
    ))

    # Additional Event Operations
    registry.register(ToolMetadata(
        name="move_event",
        description="Move an event to a different calendar",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "Source calendar ID (default: primary)", required=False),
            ToolParameter("event_id", "string", "ID of the event to move", required=True),
            ToolParameter("destination", "string", "Destination calendar ID", required=True),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="quick_add_event",
        description="Quick add an event using natural language",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
            ToolParameter("text", "string", "Natural language description of the event", required=True),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="get_event_instances",
        description="Get instances of a recurring event",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
            ToolParameter("event_id", "string", "ID of the recurring event", required=True),
            ToolParameter("max_results", "integer", "Maximum number of instances to return", required=False),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="import_event",
        description="Import an event from external data",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
            ToolParameter("event_data", "object", "Event data to import", required=True),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="patch_event",
        description="Patch specific fields of an event",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
            ToolParameter("event_id", "string", "ID of the event to patch", required=True),
            ToolParameter("summary", "string", "Event summary/title", required=False),
            ToolParameter("start_time", "string", "Event start time (ISO format)", required=False),
            ToolParameter("end_time", "string", "Event end time (ISO format)", required=False),
            ToolParameter("description", "string", "Event description", required=False),
            ToolParameter("location", "string", "Event location", required=False),
            ToolParameter("attendees", "array", "List of attendee email addresses", required=False, items_type="string"),
        ],
        result_formatter=format_calendar_result
    ))

    # Calendar Operations
    registry.register(ToolMetadata(
        name="list_calendars",
        description="List available calendars",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("max_results", "integer", "Maximum number of calendars to return", required=False),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="get_calendar",
        description="Get a specific calendar",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "ID of the calendar to retrieve", required=True),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="create_calendar",
        description="Create a new calendar",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("summary", "string", "Calendar name", required=True),
            ToolParameter("description", "string", "Calendar description", required=False),
            ToolParameter("time_zone", "string", "Calendar timezone (default: UTC)", required=False),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="update_calendar",
        description="Update an existing calendar",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "ID of the calendar to update", required=True),
            ToolParameter("summary", "string", "Calendar name", required=False),
            ToolParameter("description", "string", "Calendar description", required=False),
            ToolParameter("time_zone", "string", "Calendar timezone", required=False),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="delete_calendar",
        description="Delete a calendar",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "ID of the calendar to delete", required=True),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="clear_calendar",
        description="Clear all events from a calendar",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "ID of the calendar to clear", required=True),
        ],
        result_formatter=format_calendar_result
    ))

    # Additional Resource Operations
    registry.register(ToolMetadata(
        name="freebusy_query",
        description="Query free/busy information for calendars",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("time_min", "string", "Start time for query (ISO format)", required=True),
            ToolParameter("time_max", "string", "End time for query (ISO format)", required=True),
            ToolParameter("items", "array", "List of calendar IDs to check", required=True, items_type="object"),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="get_colors",
        description="Get available calendar colors",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="list_settings",
        description="List calendar settings",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("max_results", "integer", "Maximum number of settings to return", required=False),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="get_setting",
        description="Get a specific calendar setting",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("setting", "string", "Setting name to retrieve", required=True),
        ],
        result_formatter=format_calendar_result
    ))

    # Meet Operations
    registry.register(ToolMetadata(
        name="create_meeting",
        description="Create a new meeting with video conferencing",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("summary", "string", "Meeting summary/title", required=True),
            ToolParameter("description", "string", "Meeting description", required=False),
            ToolParameter("start_time", "string", "Meeting start time (ISO format)", required=True),
            ToolParameter("end_time", "string", "Meeting end time (ISO format)", required=True),
            ToolParameter("attendees", "array", "List of attendee email addresses", required=False, items_type="string"),
            ToolParameter("location", "string", "Meeting location", required=False),
            ToolParameter("conference_data_version", "integer", "Conference data version (default: 1)", required=False),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="get_meeting",
        description="Get a specific meeting",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("event_id", "string", "ID of the meeting to retrieve", required=True),
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="update_meeting",
        description="Update an existing meeting",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("event_id", "string", "ID of the meeting to update", required=True),
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
            ToolParameter("summary", "string", "Meeting summary/title", required=False),
            ToolParameter("description", "string", "Meeting description", required=False),
            ToolParameter("start_time", "string", "Meeting start time (ISO format)", required=False),
            ToolParameter("end_time", "string", "Meeting end time (ISO format)", required=False),
            ToolParameter("attendees", "array", "List of attendee email addresses", required=False, items_type="string"),
            ToolParameter("location", "string", "Meeting location", required=False),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="delete_meeting",
        description="Delete a meeting",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("event_id", "string", "ID of the meeting to delete", required=True),
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="list_meetings",
        description="List meetings",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
            ToolParameter("time_min", "string", "Start time for meetings (ISO format)", required=False),
            ToolParameter("time_max", "string", "End time for meetings (ISO format)", required=False),
            ToolParameter("max_results", "integer", "Maximum number of meetings to return", required=False),
            ToolParameter("single_events", "boolean", "Whether to expand recurring meetings", required=False),
            ToolParameter("order_by", "string", "Order of meetings (startTime)", required=False),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="add_meeting_attendee",
        description="Add an attendee to a meeting",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("event_id", "string", "ID of the meeting", required=True),
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
            ToolParameter("email", "string", "Email address of the attendee", required=True),
            ToolParameter("display_name", "string", "Display name of the attendee", required=False),
        ],
        result_formatter=format_calendar_result
    ))

    registry.register(ToolMetadata(
        name="remove_meeting_attendee",
        description="Remove an attendee from a meeting",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="calendar",
        requires_auth=True,
        parameters=[
            ToolParameter("event_id", "string", "ID of the meeting", required=True),
            ToolParameter("calendar_id", "string", "Calendar ID (default: primary)", required=False),
            ToolParameter("email", "string", "Email address of the attendee to remove", required=True),
        ],
        result_formatter=format_calendar_result
    )) 