"""Google Sheets tool registrations."""

from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_tool_result

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def register_sheets_tools(registry: 'ToolRegistry') -> None:
    """Register all Google Sheets-related tools."""
    
    # Spreadsheet operations
    registry.register(ToolMetadata(
        name="get_spreadsheet",
        description="Get a Google Sheets spreadsheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("spreadsheet_id", "string", "ID of the spreadsheet to retrieve", required=True),
            ToolParameter("include_grid_data", "boolean", "Whether to include grid data", required=False),
            ToolParameter("ranges", "array", "Specific ranges to retrieve", required=False, items_type="string"),
            ToolParameter("fields", "string", "Fields to include in the response", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="create_spreadsheet",
        description="Create a new Google Sheets spreadsheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("properties", "object", "Spreadsheet properties", required=False),
            ToolParameter("sheets", "array", "Initial sheets to create", required=False, items_type="object"),
            ToolParameter("named_ranges", "array", "Named ranges to create", required=False, items_type="object"),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="update_spreadsheet",
        description="Update a Google Sheets spreadsheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("spreadsheet_id", "string", "ID of the spreadsheet to update", required=True),
            ToolParameter("fields", "string", "Fields to update", required=True),
            ToolParameter("properties", "object", "Spreadsheet properties", required=False),
            ToolParameter("sheets", "array", "Sheets to update", required=False, items_type="object"),
            ToolParameter("named_ranges", "array", "Named ranges to update", required=False, items_type="object"),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="batch_update_spreadsheet",
        description="Batch update a Google Sheets spreadsheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("spreadsheet_id", "string", "ID of the spreadsheet to update", required=True),
            ToolParameter("requests", "array", "Array of update requests", required=True, items_type="object"),
            ToolParameter("include_spreadsheet_in_response", "boolean", "Include spreadsheet in response", required=False),
            ToolParameter("response_ranges", "array", "Ranges to include in response", required=False, items_type="string"),
            ToolParameter("response_include_grid_data", "boolean", "Include grid data in response", required=False),
        ],
        result_formatter=format_tool_result
    ))

    # Sheet operations
    registry.register(ToolMetadata(
        name="get_sheet",
        description="Get values from a sheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("spreadsheet_id", "string", "ID of the spreadsheet", required=True),
            ToolParameter("ranges", "array", "Ranges to retrieve", required=True, items_type="string"),
            ToolParameter("major_dimension", "string", "Major dimension (ROWS or COLUMNS)", required=False),
            ToolParameter("value_render_option", "string", "How values should be rendered", required=False),
            ToolParameter("date_time_render_option", "string", "How dates should be rendered", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="update_sheet",
        description="Update values in a sheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("spreadsheet_id", "string", "ID of the spreadsheet", required=True),
            ToolParameter("range", "string", "Range to update", required=True),
            ToolParameter("values", "array", "Values to write", required=True, items_type="array"),
            ToolParameter("value_input_option", "string", "How input data should be interpreted", required=False),
            ToolParameter("include_values_in_response", "boolean", "Include values in response", required=False),
            ToolParameter("response_value_render_option", "string", "How response values should be rendered", required=False),
            ToolParameter("response_date_time_render_option", "string", "How response dates should be rendered", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="batch_update_sheet",
        description="Batch update values in a sheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("spreadsheet_id", "string", "ID of the spreadsheet", required=True),
            ToolParameter("data", "array", "Data to update", required=True, items_type="object"),
            ToolParameter("value_input_option", "string", "How input data should be interpreted", required=False),
            ToolParameter("include_values_in_response", "boolean", "Include values in response", required=False),
            ToolParameter("response_value_render_option", "string", "How response values should be rendered", required=False),
            ToolParameter("response_date_time_render_option", "string", "How response dates should be rendered", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="clear_sheet",
        description="Clear values from a sheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("spreadsheet_id", "string", "ID of the spreadsheet", required=True),
            ToolParameter("range", "string", "Range to clear", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="batch_clear_sheet",
        description="Batch clear values from a sheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("spreadsheet_id", "string", "ID of the spreadsheet", required=True),
            ToolParameter("ranges", "array", "Ranges to clear", required=True, items_type="string"),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="append_sheet",
        description="Append values to a sheet",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="sheets",
        requires_auth=True,
        parameters=[
            ToolParameter("spreadsheet_id", "string", "ID of the spreadsheet", required=True),
            ToolParameter("range", "string", "Range to append to", required=True),
            ToolParameter("values", "array", "Values to append", required=True, items_type="array"),
            ToolParameter("value_input_option", "string", "How input data should be interpreted", required=False),
            ToolParameter("insert_data_option", "string", "How the input data should be inserted", required=False),
            ToolParameter("include_values_in_response", "boolean", "Include values in response", required=False),
            ToolParameter("response_value_render_option", "string", "How response values should be rendered", required=False),
            ToolParameter("response_date_time_render_option", "string", "How response dates should be rendered", required=False),
        ],
        result_formatter=format_tool_result
    ))

    # Legacy tools (keeping for backward compatibility)
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
            ToolParameter(
                "values",
                "array",
                "2D array of values to write",
                required=True,
                items=ToolParameter(
                    name="row",
                    type="array",
                    description="Row of values",
                    items_type="string"
                )
            ),
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
            ToolParameter(
                "values",
                "array",
                "2D array of values to append",
                required=True,
                items=ToolParameter(
                    name="row",
                    type="array",
                    description="Row of values",
                    items_type="string"
                )
            ),
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