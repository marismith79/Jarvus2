"""Google Sheets tool registrations."""

from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_tool_result

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def register_sheets_tools(registry: 'ToolRegistry') -> None:
    """Register all Google Sheets-related tools."""
    
    registry.register(ToolMetadata(
        name="sheets_create",
        description="Create a new Google Sheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("title", "string", "Sheet title", required=True),
            ToolParameter("headers", "array", "Column headers", required=False, items_type="string"),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="sheets_get",
        description="Get data from a Google Sheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("sheet_id", "string", "ID of the sheet to retrieve", required=True),
            ToolParameter("range", "string", "Range to retrieve (e.g., 'A1:D10')", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="sheets_update",
        description="Update data in a Google Sheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("sheet_id", "string", "ID of the sheet to update", required=True),
            ToolParameter("range", "string", "Range to update (e.g., 'A1:D10')", required=True),
            ToolParameter("values", "array", "2D array of values to write", required=True, items_type="array"),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="sheets_append",
        description="Append data to a Google Sheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("sheet_id", "string", "ID of the sheet to append to", required=True),
            ToolParameter("range", "string", "Range to append to (e.g., 'A1:D')", required=True),
            ToolParameter("values", "array", "2D array of values to append", required=True, items_type="array"),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="sheets_clear",
        description="Clear data from a Google Sheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("sheet_id", "string", "ID of the sheet to clear", required=True),
            ToolParameter("range", "string", "Range to clear (e.g., 'A1:D10')", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="sheets_list",
        description="List Google Sheets",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("max_results", "integer", "Maximum number of results to return", required=False),
            ToolParameter("query", "string", "Search query to filter sheets", required=False),
        ],
        result_formatter=format_tool_result
    )) 