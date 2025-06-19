"""Google Slides tool registrations."""

from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_tool_result

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def register_slides_tools(registry: 'ToolRegistry') -> None:
    """Register all Google Slides-related tools."""
    
    # Presentation operations
    registry.register(ToolMetadata(
        name="get_presentation",
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
        name="create_presentation",
        description="Create a new Google Slides presentation",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("title", "string", "Presentation title", required=False),
            ToolParameter("slides", "array", "Initial slides to create", required=False, items_type="object"),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="update_presentation",
        description="Update a Google Slides presentation",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation to update", required=True),
            ToolParameter("requests", "array", "Array of update requests", required=True, items_type="object"),
            ToolParameter("write_control", "object", "Write control options", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="batch_update_presentation",
        description="Batch update a Google Slides presentation",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation to update", required=True),
            ToolParameter("requests", "array", "Array of update requests", required=True, items_type="object"),
            ToolParameter("write_control", "object", "Write control options", required=False),
        ],
        result_formatter=format_tool_result
    ))

    # Slide operations
    registry.register(ToolMetadata(
        name="create_slide",
        description="Create a new slide",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("object_id", "string", "ID for the new slide", required=False),
            ToolParameter("insertion_index", "integer", "Index where to insert the slide", required=False),
            ToolParameter("slide_layout_reference", "object", "Layout reference for the slide", required=False),
            ToolParameter("placeholder_id_mappings", "array", "Placeholder ID mappings", required=False, items_type="object"),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="duplicate_slide",
        description="Duplicate a slide",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("object_id", "string", "ID of the slide to duplicate", required=True),
            ToolParameter("insertion_index", "integer", "Index where to insert the duplicated slide", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="delete_slide",
        description="Delete a slide",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("object_id", "string", "ID of the slide to delete", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="get_slide",
        description="Get a specific slide",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("page_object_id", "string", "ID of the slide to retrieve", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="list_slides",
        description="List all slides in a presentation",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
        ],
        result_formatter=format_tool_result
    ))

    # Page element operations
    registry.register(ToolMetadata(
        name="create_shape",
        description="Create a shape on a slide",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("page_object_id", "string", "ID of the slide", required=True),
            ToolParameter("shape_type", "string", "Type of shape to create", required=True),
            ToolParameter("object_id", "string", "ID for the new shape", required=False),
            ToolParameter("element_properties", "object", "Properties of the shape", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="create_text_box",
        description="Create a text box on a slide",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("page_object_id", "string", "ID of the slide", required=True),
            ToolParameter("object_id", "string", "ID for the new text box", required=False),
            ToolParameter("element_properties", "object", "Properties of the text box", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="create_image",
        description="Create an image on a slide",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("page_object_id", "string", "ID of the slide", required=True),
            ToolParameter("url", "string", "URL of the image", required=True),
            ToolParameter("object_id", "string", "ID for the new image", required=False),
            ToolParameter("element_properties", "object", "Properties of the image", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="create_table",
        description="Create a table on a slide",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("page_object_id", "string", "ID of the slide", required=True),
            ToolParameter("rows", "integer", "Number of rows", required=True),
            ToolParameter("columns", "integer", "Number of columns", required=True),
            ToolParameter("object_id", "string", "ID for the new table", required=False),
            ToolParameter("element_properties", "object", "Properties of the table", required=False),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="delete_page_element",
        description="Delete a page element",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("object_id", "string", "ID of the element to delete", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="get_page_element",
        description="Get a specific page element",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("object_id", "string", "ID of the element to retrieve", required=True),
        ],
        result_formatter=format_tool_result
    ))

    # Text operations
    registry.register(ToolMetadata(
        name="slides_insert_text",
        description="Insert text into a text element",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("object_id", "string", "ID of the text element", required=True),
            ToolParameter("insertion_index", "integer", "Index where to insert text", required=True),
            ToolParameter("text", "string", "Text to insert", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="delete_text",
        description="Delete text from a text element",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("object_id", "string", "ID of the text element", required=True),
            ToolParameter("text_range", "object", "Range of text to delete", required=True),
        ],
        result_formatter=format_tool_result
    ))

    registry.register(ToolMetadata(
        name="slides_replace_all_text",
        description="Replace all instances of text",
        category=ToolCategory.GOOGLE_WORKSPACE,
        server_path="slides",
        requires_auth=True,
        parameters=[
            ToolParameter("presentation_id", "string", "ID of the presentation", required=True),
            ToolParameter("contains_text", "string", "Text to find and replace", required=True),
            ToolParameter("replace_text", "string", "Text to replace with", required=True),
        ],
        result_formatter=format_tool_result
    ))

    # Legacy tools (keeping for backward compatibility)
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
