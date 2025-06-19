"""Google Docs tool registrations."""

from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_tool_result

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def register_docs_tools(registry: 'ToolRegistry') -> None:
    """Register all Google Docs-related tools."""
    
    # Document operations
    registry.register(ToolMetadata(
        name="get_document",
        description="Get a Google Docs document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document to retrieve", required=True),
            ToolParameter("suggestions_view_mode", "string", "Suggestions view mode", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="create_document",
        description="Create a new Google Docs document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("title", "string", "Document title", required=True),
            ToolParameter("body", "object", "Document body content", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="update_document",
        description="Update a Google Docs document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document to update", required=True),
            ToolParameter("requests", "array", "Array of update requests", required=True, items_type="object"),
            ToolParameter("write_control", "object", "Write control options", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="batch_update_document",
        description="Batch update a Google Docs document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document to update", required=True),
            ToolParameter("requests", "array", "Array of update requests", required=True, items_type="object"),
            ToolParameter("write_control", "object", "Write control options", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="get_document_revision",
        description="Get a specific revision of a document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("revision_id", "string", "ID of the revision to retrieve", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="list_document_revisions",
        description="List revisions of a document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("page_size", "integer", "Number of revisions to return", required=False),
            ToolParameter("page_token", "string", "Token for pagination", required=False),
        ],
        result_formatter=format_tool_result
    ))

    # Content operations
    registry.register(ToolMetadata(
        name="insert_text",
        description="Insert text into a document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("location", "object", "Location to insert text", required=True),
            ToolParameter("text", "string", "Text to insert", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="delete_content_range",
        description="Delete content from a document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("range", "object", "Range of content to delete", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="replace_all_text",
        description="Replace all instances of text in a document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("contains_text", "string", "Text to find and replace", required=True),
            ToolParameter("replace_text", "string", "Text to replace with", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="insert_table",
        description="Insert a table into a document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("location", "object", "Location to insert table", required=True),
            ToolParameter("rows", "integer", "Number of rows", required=True),
            ToolParameter("columns", "integer", "Number of columns", required=True),
            ToolParameter("end_of_segment_location", "object", "End of segment location", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="insert_table_row",
        description="Insert a row into a table",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("table_cell_location", "object", "Table cell location", required=True),
            ToolParameter("insert_below", "boolean", "Insert below the specified row", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="insert_table_column",
        description="Insert a column into a table",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("table_cell_location", "object", "Table cell location", required=True),
            ToolParameter("insert_right", "boolean", "Insert to the right of the specified column", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="delete_table_row",
        description="Delete a row from a table",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("table_cell_location", "object", "Table cell location", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="delete_table_column",
        description="Delete a column from a table",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("table_cell_location", "object", "Table cell location", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="insert_inline_image",
        description="Insert an inline image into a document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("location", "object", "Location to insert image", required=True),
            ToolParameter("uri", "string", "URI of the image", required=True),
            ToolParameter("object_size", "object", "Size of the image object", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="insert_page_break",
        description="Insert a page break into a document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("location", "object", "Location to insert page break", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="insert_section_break",
        description="Insert a section break into a document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("location", "object", "Location to insert section break", required=True),
            ToolParameter("section_type", "string", "Type of section break", required=True),
        ],
        result_formatter=format_tool_result
    ))

    # Styling operations
    registry.register(ToolMetadata(
        name="update_paragraph_style",
        description="Update paragraph style in a document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("range", "object", "Range to apply style to", required=True),
            ToolParameter("paragraph_style", "object", "Paragraph style to apply", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="update_text_style",
        description="Update text style in a document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("range", "object", "Range to apply style to", required=True),
            ToolParameter("text_style", "object", "Text style to apply", required=True),
            ToolParameter("fields", "string", "Fields to update", required=True),
        ],
        result_formatter=format_tool_result
    ))

    # Comment operations
    registry.register(ToolMetadata(
        name="create_comment",
        description="Create a comment in a document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("location", "object", "Location for the comment", required=True),
            ToolParameter("content", "string", "Comment content", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="get_comment",
        description="Get a specific comment",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("comment_id", "string", "ID of the comment", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="list_comments",
        description="List comments in a document",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("page_size", "integer", "Number of comments to return", required=False),
            ToolParameter("page_token", "string", "Token for pagination", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="update_comment",
        description="Update a comment",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("comment_id", "string", "ID of the comment", required=True),
            ToolParameter("content", "string", "New comment content", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="delete_comment",
        description="Delete a comment",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("comment_id", "string", "ID of the comment to delete", required=True),
        ],
        result_formatter=format_tool_result
    ))

    # Reply operations
    registry.register(ToolMetadata(
        name="create_reply",
        description="Create a reply to a comment",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("comment_id", "string", "ID of the comment", required=True),
            ToolParameter("content", "string", "Reply content", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="get_reply",
        description="Get a specific reply",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("comment_id", "string", "ID of the comment", required=True),
            ToolParameter("reply_id", "string", "ID of the reply", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="list_replies",
        description="List replies to a comment",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("comment_id", "string", "ID of the comment", required=True),
            ToolParameter("page_size", "integer", "Number of replies to return", required=False),
            ToolParameter("page_token", "string", "Token for pagination", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="update_reply",
        description="Update a reply",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("comment_id", "string", "ID of the comment", required=True),
            ToolParameter("reply_id", "string", "ID of the reply", required=True),
            ToolParameter("content", "string", "New reply content", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="delete_reply",
        description="Delete a reply",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="docs",
        requires_auth=True,
        parameters=[
            ToolParameter("document_id", "string", "ID of the document", required=True),
            ToolParameter("comment_id", "string", "ID of the comment", required=True),
            ToolParameter("reply_id", "string", "ID of the reply to delete", required=True),
        ],
        result_formatter=format_tool_result
    ))

    # Legacy tools (keeping for backward compatibility)
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