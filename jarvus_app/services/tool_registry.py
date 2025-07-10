"""
Tool Registry System for managing tool metadata and discovery.
This module provides a framework for registering and discovering tools
that are available through various MCP servers.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from azure.ai.inference.models import ChatCompletionsToolDefinition, FunctionDefinition

from .mcp_client import mcp_client, ToolExecutionError


class ToolCategory(Enum):
    """Categories for different types of tools."""
    # Service Provider Categories
    MICROSOFT_365 = "microsoft-365"
    CUSTOM = "custom"
    WEB = "web"
    BROWSER = "browser"
    CHROME = "chrome"
    DOCS = "docs"
    GMAIL = "gmail"
    CALENDAR = "calendar"
    DRIVE = "drive"
    SHEETS = "sheets"
    SLIDES = "slides"


@dataclass
class ToolParameter:
    """Parameter definition for a tool."""
    name: str
    type: str
    description: str
    required: bool = False
    items_type: Optional[str] = None  # for backward compatibility
    items: Optional["ToolParameter"] = None  # for nested arrays/objects

    def to_schema(self) -> dict:
        schema = {"type": self.type, "description": self.description}
        if self.type == "array":
            if self.items:
                schema["items"] = self.items.to_schema()
            elif self.items_type:
                schema["items"] = {"type": self.items_type}
        return schema


@dataclass
class ToolMetadata:
    """Metadata for a tool available through the MCP server."""
    name: str
    description: str
    category: ToolCategory
    server_path: str                
    requires_auth: bool = True
    is_active: bool = True
    executor: Optional[Callable] = None
    parameters: Optional[List[ToolParameter]] = None
    result_formatter: Optional[Callable] = None

    def to_sdk_definition(self) -> ChatCompletionsToolDefinition:
        """Convert this metadata into an Azure SDK ChatCompletionsToolDefinition."""
        props: Dict[str, Any] = {}
        required: List[str] = []

        if self.parameters:
            for p in self.parameters:
                schema = p.to_schema()
                props[p.name] = schema
                if p.required:
                    required.append(p.name)
        else:
            # Default single-query parameter
            props = {
                "query": {
                    "type": "string",
                    "description": "Search query or parameters for the operation"
                }
            }

        func_def = FunctionDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": props,
                "required": required
            }
        )
        return ChatCompletionsToolDefinition(function=func_def)


class ToolRegistry:
    """Registry for managing available tools and their metadata."""

    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}
        print("Tool Registry initialized")

    def register(self, tool: ToolMetadata) -> None:
        """Register a new tool's metadata."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
        # print(f"Registered tool: {tool.name}")

    def get_tool(self, tool_name: str) -> Optional[ToolMetadata]:
        """Get a tool's metadata by name."""
        return self._tools.get(tool_name)

    def get_all_tools(self) -> List[ToolMetadata]:
        """Get metadata for all registered tools."""
        return list(self._tools.values())

    def get_active_tools(self) -> List[ToolMetadata]:
        """Get metadata for all active tools."""
        return [t for t in self._tools.values() if t.is_active]

    def get_tools_by_category(self, category: Optional[ToolCategory] = None) -> List[ToolMetadata]:
        """Get metadata for all tools in a specific category."""
        if category is None:
            return list(self._tools.values())
        return [t for t in self._tools.values() if t.category == category]

    def get_tools_by_category_dict(self) -> Dict[ToolCategory, List[ToolMetadata]]:
        """Get all tools grouped by category."""
        tools_by_category: Dict[ToolCategory, List[ToolMetadata]] = {}
        for tool in self._tools.values():
            if tool.category not in tools_by_category:
                tools_by_category[tool.category] = []
            tools_by_category[tool.category].append(tool)
        return tools_by_category

    def get_sdk_tools(self) -> List[ChatCompletionsToolDefinition]:
        """Return all active tools as Azure SDK definitions."""
        return [m.to_sdk_definition() for m in self._tools.values() if m.is_active]

    def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any] = None,
        jwt_token: Optional[str] = None
    ) -> Any:
        """Execute a tool operation and format the result."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔧 ToolRegistry.execute_tool called with tool_name: {tool_name}")
        logger.info(f"🔧 Parameters: {parameters}")
        
        tool = self.get_tool(tool_name)
        if not tool or not tool.is_active:
            logger.error(f"🔧 Tool not available or not active: {tool_name}")
            raise ValueError(f"Tool not available: {tool_name}")

        logger.info(f"🔧 Found tool: {tool.name}, executor: {tool.executor}")
        executor = tool.executor or mcp_client.execute_tool
        
        # For browser tools, pass parameters directly
        if tool_name in ["open_website", "get_page_metadata", "get_tabs_info", "get_page_content", "execute_javascript"]:
            logger.info("🔧 Using direct parameter passing for browser tool")
            raw_result = executor(tool_name, parameters, jwt_token)
        else:
            # For other tools, use the legacy format
            request_body = {
                "operation": tool_name,
                "parameters": parameters
            }
            logger.info(f"🔧 Using legacy format, request_body: {request_body}")
            raw_result = executor(
                tool_name=tool.server_path,
                payload=request_body,
                jwt_token=jwt_token
            )
        
        logger.info(f"🔧 Raw result: {raw_result}")
        return self._handle_tool_response(tool, raw_result)

    def _handle_tool_response(self, tool: ToolMetadata, raw_result: Any) -> Any:
        """Handle and optionally format the raw tool execution result."""
        print(f"\nTool Registry: Got result from {tool.name}")
        if tool.result_formatter:
            return tool.result_formatter(raw_result)
        return raw_result

    def get_tools_by_module(self, module_name: str) -> List[ChatCompletionsToolDefinition]:
        """Get tools from a specific module/file."""
        # Map frontend tool names to tool categories
        module_to_category = {
            'web': ToolCategory.WEB,
            'docs': ToolCategory.DOCS,
            'gmail': ToolCategory.GMAIL,
            'calendar': ToolCategory.CALENDAR,
            'web': ToolCategory.WEB,
            'browser': ToolCategory.BROWSER,
        }
        
        category = module_to_category.get(module_name.lower())
        if category:
            # Debug logging to help diagnose issues
            tools = [m.to_sdk_definition() 
                    for m in self._tools.values() 
                    if m.is_active and m.category == category]
            
            print(f"Found {len(tools)} tools for category {category}")
            return tools
        print(f"No category found for module {module_name}")
        return []

    def get_sdk_tools_by_modules(self, module_names: List[str]) -> List[ChatCompletionsToolDefinition]:
        """Get tools from multiple modules."""
        all_tools = []
        for module_name in module_names:
            all_tools.extend(self.get_tools_by_module(module_name))
        return all_tools


def format_tool_result(result: Any) -> str:
    """Format generic tool result into a human-readable string."""
    if isinstance(result, list):
        return "\n".join(f"- {item}" for item in result)
    if isinstance(result, dict):
        return "\n".join(f"{k}: {v}" for k, v in result.items())
    return str(result)


def format_font_result(result: Any) -> str:
    """Format font detection results into a human-readable string."""
    if not isinstance(result, dict):
        return str(result)
    
    if not result.get("success"):
        return f"Font detection failed: {result.get('error', 'Unknown error')}"
    
    font_data = result.get("fonts", {})
    if not font_data:
        return "No font data found"
    
    # Build a comprehensive font report
    report = []
    report.append("🎨 FONT ANALYSIS REPORT")
    report.append("=" * 50)
    
    # Unique fonts
    unique_fonts = font_data.get("uniqueFonts", [])
    report.append(f"📝 Unique Fonts Found: {len(unique_fonts)}")
    for font in unique_fonts:
        report.append(f"   • {font}")
    
    # Font usage statistics
    font_usage = font_data.get("fontUsage", {})
    if font_usage:
        report.append(f"\n📊 FONT USAGE STATISTICS:")
        for font_name, usage in font_usage.items():
            report.append(f"\n🔤 {font_name}:")
            report.append(f"   • Full family: {usage.get('fontFamily', 'Unknown')}")
            report.append(f"   • Used {usage.get('usageCount', 0)} times")
            report.append(f"   • Sizes: {', '.join(usage.get('sizes', []))}")
            report.append(f"   • Weights: {', '.join(usage.get('weights', []))}")
            report.append(f"   • Elements: {', '.join(usage.get('elements', []))}")
    
    # @font-face rules
    font_faces = font_data.get("fontFaces", [])
    if font_faces:
        report.append(f"\n🔗 @FONT-FACE RULES ({len(font_faces)} found):")
        for face in font_faces[:5]:  # Show first 5
            report.append(f"   • {face.get('fontFamily', 'Unknown')}: {face.get('src', 'No source')}")
        if len(font_faces) > 5:
            report.append(f"   ... and {len(font_faces) - 5} more")
    
    # Summary
    total_elements = font_data.get("totalElements", 0)
    elements_with_fonts = font_data.get("elementsWithFonts", 0)
    report.append(f"\n📈 SUMMARY:")
    report.append(f"   • Total elements analyzed: {total_elements}")
    report.append(f"   • Elements with fonts: {elements_with_fonts}")
    report.append(f"   • Font coverage: {(elements_with_fonts/total_elements*100):.1f}%" if total_elements > 0 else "   • Font coverage: N/A")
    
    return "\n".join(report)


def format_browser_result(result: Any) -> Dict[str, Any]:
    """Format browser tool results while preserving dictionary structure."""
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        return {"items": result}
    return {"result": str(result)}


# Instantiate registry
tool_registry = ToolRegistry()

# Import all tool registration functions
from .tools import (
    register_chrome_tools,
    register_web_search_tools,
    # register_docs_tools,
    # register_gmail_tools,
    register_calendar_tools,
    # register_drive_tools,
    # register_sheets_tools,
    # register_slides_tools
)

# Register all tools
register_browser_tools(tool_registry)
register_web_search_tools(tool_registry)
# register_docs_tools(tool_registry)
# register_gmail_tools(tool_registry)
register_calendar_tools(tool_registry)
# register_drive_tools(tool_registry)
# register_sheets_tools(tool_registry)
# register_slides_tools(tool_registry) 