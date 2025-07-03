"""
Chrome Control Tools for Jarvus
Provides advanced browser automation capabilities including clicking, typing, scrolling, and more.
"""

import logging
from typing import Dict, Any, List
from jarvus_app.services.chrome_service import chrome_control
from jarvus_app.services.tool_registry import ToolMetadata, ToolCategory, ToolParameter, format_tool_result, format_font_result

logger = logging.getLogger(__name__)

def register_chrome_tools(registry):
    """Register all Chrome control tools."""
    registry.register(ToolMetadata(
        name="chrome_control",
        description="Chrome control tools",
        category=ToolCategory.CHROME,
    ))

def chrome_navigate_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for navigating to URLs in Chrome."""
    try:
        operation = payload.get("operation", "")
        parameters = payload.get("parameters", {})
        
        if operation == "navigate_to_url":
            url = parameters.get("url", "")
            tab_index = parameters.get("tab_index", 0)
            new_tab = parameters.get("new_tab", True)  # Default to new tab
            
            if not url:
                return {"success": False, "error": "URL parameter is required"}
            
            # Check if Chrome is accessible
            if not chrome_control.connect_to_chrome():
                return {"success": False, "error": "Chrome DevTools Protocol not accessible. Make sure Chrome is running with --remote-debugging-port=9222"}
            
            result = chrome_control.navigate_to_url(url, tab_index, new_tab)
            return result
            
    except Exception as e:
        logger.error(f" Chrome navigate error: {e}")
        return {"success": False, "error": str(e)}

def chrome_open_new_tab_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for opening URLs in new tabs."""
    try:
        operation = payload.get("operation", "")
        parameters = payload.get("parameters", {})
        
        if operation == "open_url_in_new_tab":
            url = parameters.get("url", "")
            
            if not url:
                return {"success": False, "error": "URL parameter is required"}
            
            # Check if Chrome is accessible
            if not chrome_control.connect_to_chrome():
                return {"success": False, "error": "Chrome DevTools Protocol not accessible. Make sure Chrome is running with --remote-debugging-port=9222"}
            
            result = chrome_control.open_url_in_new_tab(url)
            return result
            
    except Exception as e:
        logger.error(f" Chrome open new tab error: {e}")
        return {"success": False, "error": str(e)}

def chrome_click_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for clicking elements."""
    try:
        operation = payload.get("operation", "")
        parameters = payload.get("parameters", {})
        
        if operation == "click_element":
            selector = parameters.get("selector", "")
            selector_type = parameters.get("selector_type", "css")
            
            if not selector:
                return {"success": False, "error": "Selector parameter is required"}
            
            # Check if Chrome is accessible
            if not chrome_control.connect_to_chrome():
                return {"success": False, "error": "Chrome DevTools Protocol not accessible. Make sure Chrome is running with --remote-debugging-port=9222"}
            
            result = chrome_control.click_element(selector, selector_type)
            return result
            
    except Exception as e:
        logger.error(f" Chrome click error: {e}")
        return {"success": False, "error": str(e)}

def chrome_type_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for typing text."""
    try:
        operation = payload.get("operation", "")
        parameters = payload.get("parameters", {})
        
        if operation == "type_text":
            selector = parameters.get("selector", "")
            text = parameters.get("text", "")
            selector_type = parameters.get("selector_type", "css")
            
            if not selector or not text:
                return {"success": False, "error": "Selector and text parameters are required"}
            
            # Check if Chrome is accessible
            if not chrome_control.connect_to_chrome():
                return {"success": False, "error": "Chrome DevTools Protocol not accessible. Make sure Chrome is running with --remote-debugging-port=9222"}
            
            result = chrome_control.type_text(selector, text, selector_type)
            return result
            
    except Exception as e:
        logger.error(f" Chrome type error: {e}")
        return {"success": False, "error": str(e)}

def chrome_get_content_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for getting page content."""
    try:
        operation = payload.get("operation", "")
        
        if operation == "get_page_content":
            # Check if Chrome is accessible
            if not chrome_control.connect_to_chrome():
                return {"success": False, "error": "Chrome DevTools Protocol not accessible. Make sure Chrome is running with --remote-debugging-port=9222"}
            
            result = chrome_control.get_page_content()
            return result
            
    except Exception as e:
        logger.error(f" Chrome get content error: {e}")
        return {"success": False, "error": str(e)}

def chrome_get_tabs_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for getting tabs."""
    try:
        operation = payload.get("operation", "")
        
        if operation == "get_tabs":
            # Check if Chrome is accessible
            if not chrome_control.connect_to_chrome():
                return {"success": False, "error": "Chrome DevTools Protocol not accessible. Make sure Chrome is running with --remote-debugging-port=9222"}
            
            tabs = chrome_control.get_tabs()
            return {"success": True, "tabs": tabs}
            
    except Exception as e:
        logger.error(f" Chrome get tabs error: {e}")
        return {"success": False, "error": str(e)}

def chrome_open_website_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for opening websites - a simple navigation tool."""
    try:
        operation = payload.get("operation", "")
        parameters = payload.get("parameters", {})
        
        if operation == "open_website":
            url = parameters.get("url", "")
            
            if not url:
                return {"success": False, "error": "URL parameter is required"}
            
            # Add https:// if not present
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Check if Chrome is accessible
            if not chrome_control.connect_to_chrome():
                return {"success": False, "error": "Chrome DevTools Protocol not accessible. Make sure Chrome is running with --remote-debugging-port=9222"}
            
            # Always open in a new tab, never in the same tab
            result = chrome_control.open_url_in_new_tab(url)
            return result
            
    except Exception as e:
        logger.error(f"Chrome open website error: {e}")
        return {"success": False, "error": str(e)}

def chrome_get_tabs_info_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for getting detailed information about all open tabs."""
    try:
        operation = payload.get("operation", "")
        
        if operation == "get_tabs_info":
            # Check if Chrome is accessible
            if not chrome_control.connect_to_chrome():
                return {"success": False, "error": "Chrome DevTools Protocol not accessible. Make sure Chrome is running with --remote-debugging-port=9222"}
            
            tabs = chrome_control.get_tabs()
            tabs_info = []
            
            for i, tab in enumerate(tabs):
                tab_info = {
                    "index": i,
                    "id": tab.get('id'),
                    "url": tab.get('url', ''),
                    "title": tab.get('title', ''),
                    "type": tab.get('type', ''),
                    "active": tab.get('id') == chrome_control.current_tab_id
                }
                
                # Try to get page content summary for the current tab
                if tab.get('id') == chrome_control.current_tab_id:
                    try:
                        content_result = chrome_control.get_page_content()
                        if content_result.get("success"):
                            content = content_result.get("content", "")
                            # Create a brief summary (first 200 characters)
                            summary = content[:200] + "..." if len(content) > 200 else content
                            tab_info["content_summary"] = summary
                        else:
                            tab_info["content_summary"] = "Unable to get content"
                    except Exception as e:
                        tab_info["content_summary"] = f"Error getting content: {str(e)}"
                else:
                    tab_info["content_summary"] = "Not current tab"
                
                tabs_info.append(tab_info)
            
            return {
                "success": True,
                "tabs": tabs_info,
                "total_tabs": len(tabs),
                "current_tab_index": next((i for i, tab in enumerate(tabs) if tab.get('id') == chrome_control.current_tab_id), 0)
            }
            
    except Exception as e:
        logger.error(f"Chrome get tabs info error: {e}")
        return {"success": False, "error": str(e)}

def chrome_get_fonts_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for getting font information from the current page."""
    try:
        operation = payload.get("operation", "")
        
        if operation == "get_page_fonts":
            # Check if Chrome is accessible
            if not chrome_control.connect_to_chrome():
                return {"success": False, "error": "Chrome DevTools Protocol not accessible. Make sure Chrome is running with --remote-debugging-port=9222"}
            
            result = chrome_control.get_page_fonts()
            return result
            
    except Exception as e:
        logger.error(f"Chrome get fonts error: {e}")
        return {"success": False, "error": str(e)}

def register_chrome_tools(registry):
    """Register all Chrome control tools."""
    
    # Simple navigation tool - this is what the LLM should use for basic navigation
    registry.register(ToolMetadata(
        name="open_website",
        description="Open a website in a new tab in Chrome browser. This tool always opens websites in a new tab, never in the current tab. Just provide the URL or website name.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[
            ToolParameter("url", "string", "The website URL or name (e.g., 'google.com', 'https://example.com')", required=True)
        ],
        executor=chrome_open_website_executor,
        result_formatter=format_tool_result
    ))
    
    # Tab information tool - helps LLM understand what's currently open
    registry.register(ToolMetadata(
        name="get_tabs_info",
        description="Get detailed information about all open tabs including URLs, titles, and content summaries. Use this to understand what's currently visible on screen.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[],
        executor=chrome_get_tabs_info_executor,
        result_formatter=format_tool_result
    ))
    
    # Basic navigation tools
    registry.register(ToolMetadata(
        name="navigate_to_url",
        description="Navigate to a URL in Chrome. Defaults to opening in a new tab. Can be configured to use existing tab if needed.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[
            ToolParameter("url", "string", "The URL to navigate to", required=True),
            ToolParameter("tab_index", "integer", "Tab index to use (0-based)", required=False),
            ToolParameter("new_tab", "boolean", "Whether to open in a new tab (defaults to true)", required=False)
        ],
        executor=chrome_navigate_executor,
        result_formatter=format_tool_result
    ))
    
    registry.register(ToolMetadata(
        name="open_url_in_new_tab",
        description="Open a URL in a new tab in Chrome.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[
            ToolParameter("url", "string", "The URL to open in a new tab", required=True)
        ],
        executor=chrome_open_new_tab_executor,
        result_formatter=format_tool_result
    ))
    
    # Element interaction tools
    registry.register(ToolMetadata(
        name="click_element",
        description="Click on an element on the current page using CSS selector, XPath, or text.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[
            ToolParameter("selector", "string", "Element selector (CSS, XPath, or text)", required=True),
            ToolParameter("selector_type", "string", "Type of selector: 'css', 'xpath', or 'text'", required=False)
        ],
        executor=chrome_click_executor,
        result_formatter=format_tool_result
    ))
    
    registry.register(ToolMetadata(
        name="type_text",
        description="Type text into an input field or element on the page.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[
            ToolParameter("selector", "string", "Element selector (CSS, XPath, or text)", required=True),
            ToolParameter("text", "string", "Text to type", required=True),
            ToolParameter("selector_type", "string", "Type of selector: 'css', 'xpath', or 'text'", required=False)
        ],
        executor=chrome_type_executor,
        result_formatter=format_tool_result
    ))
    
    registry.register(ToolMetadata(
        name="fill_form",
        description="Fill multiple form fields with data.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[
            ToolParameter("form_data", "object", "Dictionary mapping field selectors to values", required=True)
        ]
    ))
    
    registry.register(ToolMetadata(
        name="press_key",
        description="Press a keyboard key (enter, tab, escape, space, arrow keys, etc.).",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[
            ToolParameter("key", "string", "Key to press (enter, tab, escape, space, arrow_up, etc.)", required=True)
        ]
    ))
    
    # Page content and information tools
    registry.register(ToolMetadata(
        name="get_page_content",
        description="Get the text content of the current page.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[],
        executor=chrome_get_content_executor,
        result_formatter=format_tool_result
    ))
    
    registry.register(ToolMetadata(
        name="get_page_fonts",
        description="Get detailed font information from the current page including font families, sizes, weights, usage statistics, and CSS @font-face rules. This analyzes the DOM to find all fonts actually being used on the page.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[],
        executor=chrome_get_fonts_executor,
        result_formatter=format_font_result
    ))
    
    registry.register(ToolMetadata(
        name="get_element_info",
        description="Get detailed information about an element on the page.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[
            ToolParameter("selector", "string", "Element selector (CSS, XPath, or text)", required=True),
            ToolParameter("selector_type", "string", "Type of selector: 'css', 'xpath', or 'text'", required=False)
        ]
    ))
    
    registry.register(ToolMetadata(
        name="get_all_links",
        description="Get all links on the current page with their text and URLs.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[]
    ))
    
    registry.register(ToolMetadata(
        name="get_page_metadata",
        description="Get comprehensive page metadata including title, description, meta tags, and more.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[]
    ))
    
    # Tab management tools
    registry.register(ToolMetadata(
        name="get_tabs",
        description="Get list of all open tabs in Chrome.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[],
        executor=chrome_get_tabs_executor,
        result_formatter=format_tool_result
    ))
    
    registry.register(ToolMetadata(
        name="switch_to_tab",
        description="Switch to a specific tab by index.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[
            ToolParameter("tab_index", "integer", "Tab index to switch to (0-based)", required=True)
        ]
    ))
    
    registry.register(ToolMetadata(
        name="close_current_tab",
        description="Close the current tab.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[]
    ))
    
    # Page interaction tools
    registry.register(ToolMetadata(
        name="scroll_page",
        description="Scroll the page up, down, or to a specific position.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[
            ToolParameter("direction", "string", "Scroll direction: 'up', 'down', 'left', 'right', or 'to'", required=False),
            ToolParameter("amount", "integer", "Scroll amount in pixels", required=False),
            ToolParameter("selector", "string", "Element selector to scroll to (when direction is 'to')", required=False)
        ]
    ))
    
    registry.register(ToolMetadata(
        name="highlight_element",
        description="Highlight an element on the page for debugging purposes.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[
            ToolParameter("selector", "string", "Element selector to highlight", required=True),
            ToolParameter("color", "string", "Highlight color", required=False),
            ToolParameter("duration", "integer", "Highlight duration in milliseconds", required=False)
        ]
    ))
    
    # Page management tools
    registry.register(ToolMetadata(
        name="wait_for_page_load",
        description="Wait for the page to fully load.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[
            ToolParameter("timeout", "integer", "Timeout in seconds", required=False)
        ]
    ))
    
    registry.register(ToolMetadata(
        name="execute_javascript",
        description="Execute custom JavaScript code on the current page.",
        category=ToolCategory.WEB,
        server_path="chrome_control",
        requires_auth=False,
        parameters=[
            ToolParameter("script", "string", "JavaScript code to execute", required=True)
        ]
    ))
    
    print("✅ Chrome control tools registered successfully!") 