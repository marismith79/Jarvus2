"""Google Slides tool registrations."""

from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_tool_result

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def register_slides_tools(registry: 'ToolRegistry') -> None:
    """Register all Google Slides-related tools."""
    
    registry.register(ToolMetadata(
        name="slides_create",
        description="Create a new Google Slides presentation",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("title", "string", "Presentation title", required=True),
            ToolParameter("template_id", "string", "ID of template to use", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="slides_get",
        description="Get a Google Slides presentation",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation to retrieve", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="slides_update",
        description="Update a Google Slides presentation",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation to update", required=True),
            ToolParameter("requests", "array", "Array of update requests", required=True, items_type="object"),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="slides_share",
        description="Share a Google Slides presentation",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation to share", required=True),
            ToolParameter("email", "string", "Email address to share with", required=True),
            ToolParameter("role", "string", "Role (reader, commenter, writer, owner)", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="slides_list",
        description="List Google Slides presentations",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("max_results", "integer", "Maximum number of results to return", required=False),
            ToolParameter("query", "string", "Search query to filter presentations", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="slides_delete",
        description="Delete a Google Slides presentation",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation to delete", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="slides_create_slide",
        description="Create a new slide in a Google Slides presentation",
        category=ToolCategory.SLIDES,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("slide_layout", "string", "Layout type for the new slide", required=False),
            ToolParameter("placeholder_ids", "array", "List of placeholder IDs", required=False, items_type="string"),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="slides_insert_text",
        description="Insert text into a shape or text box in a Google Slides presentation",
        category=ToolCategory.SLIDES,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("object_id", "string", "ID of the shape or text box", required=True),
            ToolParameter("text", "string", "Text to insert", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="slides_create_shape",
        description="Create a shape in a Google Slides presentation",
        category=ToolCategory.SLIDES,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("shape_type", "string", "Type of shape to create", required=True),
            ToolParameter("page_id", "string", "ID of the slide page", required=True),
            ToolParameter("size", "object", "Size of the shape", required=True),
            ToolParameter("position", "object", "Position of the shape", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="slides_create_image",
        description="Insert an image into a Google Slides presentation",
        category=ToolCategory.SLIDES,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("page_id", "string", "ID of the slide page", required=True),
            ToolParameter("image_url", "string", "URL of the image to insert", required=True),
            ToolParameter("size", "object", "Size of the image", required=True),
            ToolParameter("position", "object", "Position of the image", required=True),
        ],
        result_formatter=format_tool_result
    ))