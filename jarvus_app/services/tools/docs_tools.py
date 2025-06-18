"""Google Docs tool registrations."""

from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_tool_result

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def register_docs_tools(registry: 'ToolRegistry') -> None:
    """Register all Google Docs-related tools."""
    
    registry.register(ToolMetadata(
        name="docs_create",
        description="Create a new Google Doc",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("title", "string", "Document title", required=True),
            ToolParameter("content", "string", "Initial document content", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="docs_get",
        description="Get a Google Doc by ID",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("doc_id", "string", "ID of the document to retrieve", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="docs_update",
        description="Update a Google Doc",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("doc_id", "string", "ID of the document to update", required=True),
            ToolParameter("content", "string", "New document content", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="docs_share",
        description="Share a Google Doc with others",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("doc_id", "string", "ID of the document to share", required=True),
            ToolParameter("email", "string", "Email address to share with", required=True),
            ToolParameter("role", "string", "Role (reader, commenter, writer, owner)", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="docs_list",
        description="List Google Docs",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("max_results", "integer", "Maximum number of results to return", required=False),
            ToolParameter("query", "string", "Search query to filter documents", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="docs_delete",
        description="Delete a Google Doc",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("doc_id", "string", "ID of the document to delete", required=True),
        ],
        result_formatter=format_tool_result
    )) 