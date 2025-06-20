"""Google Drive tool registrations."""

from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_tool_result

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def register_drive_tools(registry: 'ToolRegistry') -> None:
    """Register all Google Drive-related tools."""
    
    # File operations
    registry.register(ToolMetadata(
        name="list_files",
        description="List files in Google Drive",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("page_size", "integer", "Number of files to return", required=False),
            ToolParameter("spaces", "string", "Spaces to search in", required=False),
            ToolParameter("include_items_from_all_drives", "boolean", "Include items from all drives", required=False),
            ToolParameter("supports_all_drives", "boolean", "Support all drives", required=False),
            ToolParameter("page_token", "string", "Token for pagination", required=False),
            ToolParameter("q", "string", "Search query", required=False),
            ToolParameter("fields", "string", "Fields to include in response", required=False),
            ToolParameter("order_by", "string", "Order of results", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="get_file",
        description="Get a specific file from Google Drive",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file to retrieve", required=True),
            ToolParameter("supports_all_drives", "boolean", "Support all drives", required=False),
            ToolParameter("fields", "string", "Fields to include in response", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="create_file",
        description="Create a new file in Google Drive",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("name", "string", "Name of the file", required=True),
            ToolParameter("mime_type", "string", "MIME type of the file", required=True),
            ToolParameter("parents", "array", "Parent folder IDs", required=False, items_type="string"),
            ToolParameter("description", "string", "File description", required=False),
            ToolParameter("content", "string", "File content (for text files)", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="update_file",
        description="Update an existing file in Google Drive",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file to update", required=True),
            ToolParameter("name", "string", "New name for the file", required=False),
            ToolParameter("description", "string", "New description for the file", required=False),
            ToolParameter("parents", "array", "New parent folder IDs", required=False, items_type="string"),
            ToolParameter("content", "string", "New file content (for text files)", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="delete_file",
        description="Delete a file from Google Drive",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file to delete", required=True),
            ToolParameter("supports_all_drives", "boolean", "Support all drives", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="copy_file",
        description="Copy a file in Google Drive",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file to copy", required=True),
            ToolParameter("name", "string", "Name for the copied file", required=False),
            ToolParameter("parents", "array", "Parent folder IDs for the copy", required=False, items_type="string"),
            ToolParameter("description", "string", "Description for the copied file", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="empty_trash",
        description="Empty the trash in Google Drive",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="export_file",
        description="Export a Google Workspace document",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file to export", required=True),
            ToolParameter("mime_type", "string", "MIME type for export format", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="generate_ids",
        description="Generate file IDs for Google Drive",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("count", "integer", "Number of IDs to generate", required=True),
            ToolParameter("space", "string", "Space for the IDs", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="download_file",
        description="Download a file from Google Drive",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file to download", required=True),
            ToolParameter("supports_all_drives", "boolean", "Support all drives", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="watch_file",
        description="Watch for changes to a file",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file to watch", required=True),
            ToolParameter("kind", "string", "Kind of the channel", required=True),
            ToolParameter("id", "string", "ID of the channel", required=True),
            ToolParameter("resource_id", "string", "Resource ID", required=True),
            ToolParameter("resource_uri", "string", "Resource URI", required=True),
            ToolParameter("token", "string", "Token for the channel", required=False),
            ToolParameter("expiration", "string", "Expiration time", required=False),
        ],
        result_formatter=format_tool_result
    ))

    # Permission operations
    registry.register(ToolMetadata(
        name="list_permissions",
        description="List permissions for a file",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file", required=True),
            ToolParameter("page_size", "integer", "Number of permissions to return", required=False),
            ToolParameter("supports_all_drives", "boolean", "Support all drives", required=False),
            ToolParameter("page_token", "string", "Token for pagination", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="get_permission",
        description="Get a specific permission",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file", required=True),
            ToolParameter("permission_id", "string", "ID of the permission", required=True),
            ToolParameter("supports_all_drives", "boolean", "Support all drives", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="create_permission",
        description="Create a new permission for a file",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file", required=True),
            ToolParameter("type", "string", "Type of permission (user, group, domain, anyone)", required=True),
            ToolParameter("role", "string", "Role (reader, commenter, writer, owner)", required=True),
            ToolParameter("allow_file_discovery", "boolean", "Allow file discovery", required=True),
            ToolParameter("email_address", "string", "Email address for user/group permission", required=False),
            ToolParameter("domain", "string", "Domain for domain permission", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="update_permission",
        description="Update an existing permission",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file", required=True),
            ToolParameter("permission_id", "string", "ID of the permission", required=True),
            ToolParameter("role", "string", "New role (reader, commenter, writer, owner)", required=False),
            ToolParameter("expiration_time", "string", "Expiration time for the permission", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="delete_permission",
        description="Delete a permission",
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file", required=True),
            ToolParameter("permission_id", "string", "ID of the permission to delete", required=True),
        ],
        result_formatter=format_tool_result
    ))

    # Legacy tools (keeping for backward compatibility)
    registry.register(ToolMetadata(
        name="drive_upload",
        description="Upload a file to Google Drive",
        category=ToolCategory.DRIVE,
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
        category=ToolCategory.DRIVE,
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
        category=ToolCategory.DRIVE,
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
        category=ToolCategory.DRIVE,
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
        category=ToolCategory.DRIVE,
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
        category=ToolCategory.DRIVE,
        server_path="drive",
        requires_auth=True,
        parameters=[
            ToolParameter("file_id", "string", "ID of the file or folder to delete", required=True),
        ],
        result_formatter=format_tool_result
    )) 