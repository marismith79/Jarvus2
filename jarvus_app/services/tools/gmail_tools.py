"""Gmail tool registrations."""

from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_gmail_result

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def register_gmail_tools(registry: 'ToolRegistry') -> None:
    """Register all Gmail-related tools."""
    
    registry.register(ToolMetadata(
        name="list_messages",
        description="List emails in Gmail inbox",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="gmail",
        requires_auth=True,
        parameters=[
            ToolParameter("max_results", "integer", "Maximum number of results to return", required=True),
            ToolParameter("query", "string", "Search query to filter emails", required=True),
        ],
        result_formatter=format_gmail_result
    ))

    registry.register(ToolMetadata(
        name="get_message",
        description="Get a specific email by ID from Gmail",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="gmail",
        requires_auth=True,
        parameters=[
            ToolParameter("message_id", "string", "ID of the email to retrieve", required=True),
        ],
        result_formatter=format_gmail_result
    ))
    
    registry.register(ToolMetadata(
        name="send_message",
        description="Send an email using Gmail",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="gmail",
        requires_auth=True,
        parameters=[
            ToolParameter("to", "string", "Recipient email address", required=True),
            ToolParameter("subject", "string", "Email subject", required=True),
            ToolParameter("body", "string", "Email body", required=True),
            ToolParameter("cc", "string", "CC recipient email address", required=False),
            ToolParameter("bcc", "string", "BCC recipient email address", required=False),
        ],
        result_formatter=format_gmail_result
    ))

    registry.register(ToolMetadata(
        name="delete_message",
        description="Delete an email in Gmail by ID",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="gmail",
        requires_auth=True,
        parameters=[
            ToolParameter("message_id", "string", "ID of the email to delete", required=True),
        ],
        result_formatter=format_gmail_result
    ))

    registry.register(ToolMetadata(
        name="modify_label",
        description="Modify labels of an email in Gmail",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="gmail",
        requires_auth=True,
        parameters=[
            ToolParameter("message_id", "string", "ID of the email to modify", required=True),
            ToolParameter("add_labels", "array", "Labels to add", required=False, items_type="string"),
            ToolParameter("remove_labels", "array", "Labels to remove", required=False, items_type="string"),
        ],
        result_formatter=format_gmail_result
    )) 