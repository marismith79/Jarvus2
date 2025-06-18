"""Google Drive tool registrations."""

from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_tool_result

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def register_drive_tools(registry: 'ToolRegistry') -> None:
    """Register all Google Drive-related tools."""
    
    registry.register(ToolMetadata(
        name="drive_upload",
        description="Upload a file to Google Drive",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_name", "string", "Name of the file", required=True),
            ToolParameter("file_content", "string", "Content of the file", required=True),
            ToolParameter("mime_type", "string", "MIME type of the file", required=True),
            ToolParameter("parent_id", "string", "ID of the parent folder", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="drive_download",
        description="Download a file from Google Drive",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file to download", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="drive_list",
        description="List files in Google Drive",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("max_results", "integer", "Maximum number of results to return", required=False),
            ToolParameter("query", "string", "Search query to filter files", required=False),
            ToolParameter("parent_id", "string", "ID of the parent folder", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="drive_create_folder",
        description="Create a new folder in Google Drive",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("folder_name", "string", "Name of the folder", required=True),
            ToolParameter("parent_id", "string", "ID of the parent folder", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="drive_share",
        description="Share a file or folder in Google Drive",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file or folder to share", required=True),
            ToolParameter("email", "string", "Email address to share with", required=True),
            ToolParameter("role", "string", "Role (reader, commenter, writer, owner)", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="drive_delete",
        description="Delete a file or folder from Google Drive",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file or folder to delete", required=True),
        ],
        result_formatter=format_tool_result
    )) 