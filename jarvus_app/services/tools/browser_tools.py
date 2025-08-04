"""
Browser Control Tools for Jarvus
Provides advanced browser automation capabilities using HTTP requests to Electron's Browser API server.
Supports Chrome with encrypted profile data to avoid conflicts with user's main Chrome instance.
"""

import logging
from typing import Dict, Any, List
from jarvus_app.services.browser_http_client import (
    browser_client,
    sync_navigate_to_url,
    sync_open_url_in_new_tab,
    sync_click_element,
    sync_type_text,
    sync_get_page_content,
    sync_get_tabs,
    sync_switch_to_tab,
    sync_close_current_tab,
    sync_take_screenshot,
    sync_execute_javascript,
    sync_get_fonts,
    sync_launch_browser
)
# Profile management is handled by the desktop app - web app only connects to existing browser
from jarvus_app.services.tool_registry import ToolMetadata, ToolCategory, ToolParameter, format_browser_result, format_font_result

logger = logging.getLogger(__name__)

def register_browser_tools(registry):
    """Register all browser control tools."""
    registry.register(ToolMetadata(
        name="browser_control",
        description="Browser control tools using HTTP requests to Electron's Browser API",
        category=ToolCategory.BROWSER,
    ))

def browser_navigate_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for navigating to URLs in browser."""
    try:
        operation = payload.get("operation", "")
        parameters = payload.get("parameters", {})
        
        if operation == "navigate_to_url":
            url = parameters.get("url", "")
            tab_index = parameters.get("tab_index", 0)
            new_tab = parameters.get("new_tab", True)  # Default to new tab
            
            if not url:
                return {"success": False, "error": "URL parameter is required"}
            
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            result = sync_navigate_to_url(url, tab_index, new_tab)
            return result
            
    except Exception as e:
        logger.error(f"Browser navigate error: {e}")
        return {"success": False, "error": str(e)}

def browser_open_new_tab_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for opening URLs in new tabs."""
    try:
        operation = payload.get("operation", "")
        parameters = payload.get("parameters", {})
        
        if operation == "open_url_in_new_tab":
            url = parameters.get("url", "")
            
            if not url:
                return {"success": False, "error": "URL parameter is required"}
            
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            result = sync_open_url_in_new_tab(url)
            return result
            
    except Exception as e:
        logger.error(f"Browser open new tab error: {e}")
        return {"success": False, "error": str(e)}

def browser_click_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for clicking elements."""
    try:
        operation = payload.get("operation", "")
        parameters = payload.get("parameters", {})
        
        if operation == "click_element":
            selector = parameters.get("selector", "")
            selector_type = parameters.get("selector_type", "css")
            
            if not selector:
                return {"success": False, "error": "Selector parameter is required"}
            
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            result = sync_click_element(selector, selector_type)
            return result
            
    except Exception as e:
        logger.error(f"Browser click error: {e}")
        return {"success": False, "error": str(e)}

def browser_type_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
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
            
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            result = sync_type_text(selector, text, selector_type)
            return result
            
    except Exception as e:
        logger.error(f"Browser type error: {e}")
        return {"success": False, "error": str(e)}

def browser_get_content_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for getting page content."""
    try:
        operation = payload.get("operation", "")
        
        if operation == "get_page_content":
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            result = sync_get_page_content()
            return result
            
    except Exception as e:
        logger.error(f"Browser get content error: {e}")
        return {"success": False, "error": str(e)}

def browser_get_tabs_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for getting tabs."""
    try:
        operation = payload.get("operation", "")
        
        if operation == "get_tabs":
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            tabs = sync_get_tabs()
            return {"success": True, "tabs": tabs}
            
    except Exception as e:
        logger.error(f"Browser get tabs error: {e}")
        return {"success": False, "error": str(e)}

def browser_open_website_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for opening websites - a simple navigation tool."""
    try:
        logger.info(f"🔧 browser_open_website_executor called with tool_name: {tool_name}")
        logger.info(f"🔧 Payload: {payload}")
        
        # For direct tool calls, the payload structure is different
        if tool_name == "open_website":
            url = payload.get("url", "")
            logger.info(f"🔧 URL from payload: {url}")
            
            if not url:
                logger.error("🔧 No URL provided in payload")
                return {"success": False, "error": "URL parameter is required"}
            
            # Add https:// if not present
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            logger.info(f"🔧 Final URL: {url}")
            
            # Check if browser is accessible
            logger.info("🔧 Checking browser accessibility...")
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                logger.error("🔧 Browser not accessible")
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            logger.info("🔧 Browser is accessible")
            
            # Always open in a new tab, never in the same tab
            logger.info("🔧 Calling sync_open_url_in_new_tab...")
            result = sync_open_url_in_new_tab(url)
            logger.info(f"🔧 sync_open_url_in_new_tab result: {result}")
            return result
        else:
            # Handle legacy operation-based calls
            operation = payload.get("operation", "")
            parameters = payload.get("parameters", {})
        
        if operation == "open_website":
            url = parameters.get("url", "")
            
            if not url:
                return {"success": False, "error": "URL parameter is required"}
            
            # Add https:// if not present
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            # Always open in a new tab, never in the same tab
            result = sync_open_url_in_new_tab(url)
            return result
            
    except Exception as e:
        logger.error(f"Browser open website error: {e}")
        return {"success": False, "error": str(e)}

def browser_get_tabs_info_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for getting detailed information about all open tabs."""
    try:
        operation = payload.get("operation", "")
        
        if operation == "get_tabs_info":
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            tabs = sync_get_tabs()
            tabs_info = []
            
            for i, tab in enumerate(tabs):
                tab_info = {
                    "index": i,
                    "id": tab.get('id'),
                    "url": tab.get('url', ''),
                    "title": tab.get('title', ''),
                    "type": tab.get('type', ''),
                    "active": tab.get('active', False)
                }
                
                # Try to get page content summary for the current tab
                if tab.get('active'):
                    try:
                        content_result = browser_client.get_page_content()
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
                "current_tab_index": next((i for i, tab in enumerate(tabs) if tab.get('active')), 0)
            }
            
    except Exception as e:
        logger.error(f"Browser get tabs info error: {e}")
        return {"success": False, "error": str(e)}

def browser_get_fonts_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for getting font information from the current page."""
    try:
        operation = payload.get("operation", "")
        
        if operation == "get_page_fonts":
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            result = sync_get_fonts()
            return result
            
    except Exception as e:
        logger.error(f"Browser get fonts error: {e}")
        return {"success": False, "error": str(e)}

def browser_take_screenshot_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for taking screenshots of the current page."""
    try:
        operation = payload.get("operation", "")
        parameters = payload.get("parameters", {})
        
        if operation == "take_screenshot":
            path = parameters.get("path", None)  # Optional path parameter
            
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            result = sync_take_screenshot(path)
            return result
            
    except Exception as e:
        logger.error(f"Browser take screenshot error: {e}")
        return {"success": False, "error": str(e)}

def browser_execute_javascript_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for executing JavaScript code on the current page."""
    try:
        operation = payload.get("operation", "")
        parameters = payload.get("parameters", {})
        
        if operation == "execute_javascript":
            script = parameters.get("script", "")
            
            if not script:
                return {"success": False, "error": "Script parameter is required"}
            
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            result = sync_execute_javascript(script)
            return result
            
    except Exception as e:
        logger.error(f"Browser execute JavaScript error: {e}")
        return {"success": False, "error": str(e)}

def browser_profile_management_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for Chrome profile management - now handled by desktop app."""
    try:
        operation = payload.get("operation", "")
        
        # All profile management is now handled by the desktop app
        return {
            "success": False, 
            "error": "Profile management is handled by the desktop app. Use desktop app to manage Chrome profiles.",
            "message": "This functionality has been moved to the desktop app for security and isolation."
        }
            
    except Exception as e:
        logger.error(f"Browser profile management error: {e}")
        return {"success": False, "error": str(e)}

def browser_fill_form_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for filling form fields."""
    try:
        if tool_name == "fill_form":
            form_data = payload.get("form_data", {})
            
            if not form_data:
                return {"success": False, "error": "form_data parameter is required"}
            
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            # Execute JavaScript to fill form fields
            script = """
            const formData = arguments[0];
            let filledFields = [];
            
            for (const [selector, value] of Object.entries(formData)) {
                try {
                    const element = document.querySelector(selector);
                    if (element) {
                        element.value = value;
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                        element.dispatchEvent(new Event('change', { bubbles: true }));
                        filledFields.push({ selector, value, success: true });
                    } else {
                        filledFields.push({ selector, value, success: false, error: 'Element not found' });
                    }
                } catch (error) {
                    filledFields.push({ selector, value, success: false, error: error.message });
                }
            }
            
            return filledFields;
            """
            
            result = sync_execute_javascript(script, form_data)
            return result
            
    except Exception as e:
        logger.error(f"Browser fill form error: {e}")
        return {"success": False, "error": str(e)}

def browser_press_key_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for pressing keyboard keys."""
    try:
        if tool_name == "press_key":
            key = payload.get("key", "")
            
            if not key:
                return {"success": False, "error": "key parameter is required"}
            
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            # Map common key names to Playwright key names
            key_mapping = {
                "enter": "Enter",
                "tab": "Tab",
                "escape": "Escape",
                "space": " ",
                "arrow_up": "ArrowUp",
                "arrow_down": "ArrowDown",
                "arrow_left": "ArrowLeft",
                "arrow_right": "ArrowRight",
                "backspace": "Backspace",
                "delete": "Delete",
                "home": "Home",
                "end": "End",
                "page_up": "PageUp",
                "page_down": "PageDown"
            }
            
            playwright_key = key_mapping.get(key.lower(), key)
            
            # Execute JavaScript to press the key
            script = f"""
            document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {{ key: '{playwright_key}' }}));
            document.activeElement.dispatchEvent(new KeyboardEvent('keyup', {{ key: '{playwright_key}' }}));
            """
            
            result = sync_execute_javascript(script)
            return result
            
    except Exception as e:
        logger.error(f"Browser press key error: {e}")
        return {"success": False, "error": str(e)}

def browser_get_element_info_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for getting element information."""
    try:
        if tool_name == "get_element_info":
            selector = payload.get("selector", "")
            selector_type = payload.get("selector_type", "css")
            
            if not selector:
                return {"success": False, "error": "selector parameter is required"}
            
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            # Execute JavaScript to get element info
            script = """
            const selector = arguments[0];
            const selectorType = arguments[1];
            
            let element;
            if (selectorType === 'xpath') {
                const result = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                element = result.singleNodeValue;
            } else {
                element = document.querySelector(selector);
            }
            
            if (!element) {
                return { success: false, error: 'Element not found' };
            }
            
            return {
                success: true,
                tagName: element.tagName,
                id: element.id,
                className: element.className,
                textContent: element.textContent?.substring(0, 200),
                value: element.value,
                href: element.href,
                src: element.src,
                title: element.title,
                attributes: Array.from(element.attributes).map(attr => ({ name: attr.name, value: attr.value })),
                boundingRect: element.getBoundingClientRect().toJSON(),
                isVisible: element.offsetParent !== null
            };
            """
            
            result = sync_execute_javascript(script, selector, selector_type)
            return result
            
    except Exception as e:
        logger.error(f"Browser get element info error: {e}")
        return {"success": False, "error": str(e)}

def browser_get_all_links_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for getting all links on the page."""
    try:
        if tool_name == "get_all_links":
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            # Execute JavaScript to get all links
            script = """
            const links = Array.from(document.querySelectorAll('a[href]'));
            return links.map(link => ({
                text: link.textContent?.trim() || '',
                href: link.href,
                title: link.title || '',
                target: link.target || '_self',
                isVisible: link.offsetParent !== null
            })).filter(link => link.href && link.href !== 'javascript:void(0)');
            """
            
            result = sync_execute_javascript(script)
            return result
            
    except Exception as e:
        logger.error(f"Browser get all links error: {e}")
        return {"success": False, "error": str(e)}

def browser_get_page_metadata_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for getting page metadata."""
    try:
        if tool_name == "get_page_metadata":
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            # Use the dedicated get_page_metadata method
            result = browser_client.get_page_metadata()
            return result
            
    except Exception as e:
        logger.error(f"Browser get page metadata error: {e}")
        return {"success": False, "error": str(e)}

def browser_switch_to_tab_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for switching to a specific tab."""
    try:
        if tool_name == "switch_to_tab":
            tab_index = payload.get("tab_index", 0)
            
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            result = sync_switch_to_tab(tab_index)
            return result
            
    except Exception as e:
        logger.error(f"Browser switch to tab error: {e}")
        return {"success": False, "error": str(e)}

def browser_close_current_tab_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for closing the current tab."""
    try:
        if tool_name == "close_current_tab":
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            result = sync_close_current_tab()
            return result
            
    except Exception as e:
        logger.error(f"Browser close current tab error: {e}")
        return {"success": False, "error": str(e)}

def browser_scroll_page_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for scrolling the page."""
    try:
        if tool_name == "scroll_page":
            direction = payload.get("direction", "down")
            amount = payload.get("amount", 500)
            selector = payload.get("selector", "")
            
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            # Execute JavaScript to scroll
            if direction == "to" and selector:
                script = f"""
                const element = document.querySelector('{selector}');
                if (element) {{
                    element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    return {{ success: true, message: 'Scrolled to element' }};
                }} else {{
                    return {{ success: false, error: 'Element not found' }};
                }}
                """
            else:
                scroll_map = {
                    "up": f"window.scrollBy(0, -{amount})",
                    "down": f"window.scrollBy(0, {amount})",
                    "left": f"window.scrollBy(-{amount}, 0)",
                    "right": f"window.scrollBy({amount}, 0)"
                }
                
                scroll_command = scroll_map.get(direction, f"window.scrollBy(0, {amount})")
                script = f"{scroll_command}; return {{ success: true, message: 'Scrolled {direction}' }};"
            
            result = sync_execute_javascript(script)
            return result
            
    except Exception as e:
        logger.error(f"Browser scroll page error: {e}")
        return {"success": False, "error": str(e)}

def browser_highlight_element_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for highlighting elements."""
    try:
        if tool_name == "highlight_element":
            selector = payload.get("selector", "")
            color = payload.get("color", "red")
            duration = payload.get("duration", 3000)
            
            if not selector:
                return {"success": False, "error": "selector parameter is required"}
            
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            # Execute JavaScript to highlight element
            script = f"""
            const selector = arguments[0];
            const color = arguments[1];
            const duration = arguments[2];
            
            const element = document.querySelector(selector);
            if (!element) {{
                return {{ success: false, error: 'Element not found' }};
            }}
            
            const originalOutline = element.style.outline;
            const originalBackground = element.style.backgroundColor;
            
            element.style.outline = `3px solid ${{color}}`;
            element.style.backgroundColor = `${{color}}20`;
            
            setTimeout(() => {{
                element.style.outline = originalOutline;
                element.style.backgroundColor = originalBackground;
            }}, duration);
            
            return {{ success: true, message: 'Element highlighted' }};
            """
            
            result = sync_execute_javascript(script, selector, color, duration)
            return result
            
    except Exception as e:
        logger.error(f"Browser highlight element error: {e}")
        return {"success": False, "error": str(e)}

def browser_wait_for_page_load_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor for waiting for page load."""
    try:
        if tool_name == "wait_for_page_load":
            timeout = payload.get("timeout", 30)
            
            # Check if browser is accessible
            result = browser_client.connect_to_browser()
            if not result.get("success"):
                return {"success": False, "error": "Browser not accessible. Make sure browser is available."}
            
            # Execute JavaScript to wait for page load
            script = """
            return new Promise((resolve) => {
                if (document.readyState === 'complete') {
                    resolve({ success: true, message: 'Page already loaded' });
                } else {
                    window.addEventListener('load', () => {
                        resolve({ success: true, message: 'Page loaded' });
                    });
                    
                    setTimeout(() => {
                        resolve({ success: true, message: 'Timeout reached, page may still be loading' });
                    }, arguments[0] * 1000);
                }
            });
            """
            
            result = sync_execute_javascript(script, timeout)
            return result
            
    except Exception as e:
        logger.error(f"Browser wait for page load error: {e}")
        return {"success": False, "error": str(e)}

def register_browser_tools(registry):
    """Register all browser control tools."""
    
    # Simple navigation tool - this is what the LLM should use for basic navigation
    registry.register(ToolMetadata(
        name="open_website",
        description="Open a website in a new tab in the browser. This tool always opens websites in a new tab, never in the current tab. Just provide the URL or website name.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[
            ToolParameter("url", "string", "The website URL or name (e.g., 'google.com', 'https://example.com')", required=True)
        ],
        executor=browser_open_website_executor,
        result_formatter=format_browser_result
    ))
    
    # Tab information tool - helps LLM understand what's currently open
    registry.register(ToolMetadata(
        name="get_tabs_info",
        description="Get detailed information about all open tabs including URLs, titles, and content summaries. Use this to understand what's currently visible on screen.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[],
        executor=browser_get_tabs_info_executor,
        result_formatter=format_browser_result
    ))
    
    # Basic navigation tools
    registry.register(ToolMetadata(
        name="navigate_to_url",
        description="Navigate to a URL in the browser. Defaults to opening in a new tab. Can be configured to use existing tab if needed.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[
            ToolParameter("url", "string", "The URL to navigate to", required=True),
            ToolParameter("tab_index", "integer", "Tab index to use (0-based)", required=False),
            ToolParameter("new_tab", "boolean", "Whether to open in a new tab (defaults to true)", required=False)
        ],
        executor=browser_navigate_executor,
        result_formatter=format_browser_result
    ))
    
    registry.register(ToolMetadata(
        name="open_url_in_new_tab",
        description="Open a URL in a new tab in the browser.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[
            ToolParameter("url", "string", "The URL to open in a new tab", required=True)
        ],
        executor=browser_open_new_tab_executor,
        result_formatter=format_browser_result
    ))
    
    # Element interaction tools
    registry.register(ToolMetadata(
        name="click_element",
        description="Click on an element on the current page using CSS selector, XPath, or text.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[
            ToolParameter("selector", "string", "Element selector (CSS, XPath, or text)", required=True),
            ToolParameter("selector_type", "string", "Type of selector: 'css', 'xpath', or 'text'", required=False)
        ],
        executor=browser_click_executor,
        result_formatter=format_browser_result
    ))
    
    registry.register(ToolMetadata(
        name="type_text",
        description="Type text into an input field or element on the page.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[
            ToolParameter("selector", "string", "Element selector (CSS, XPath, or text)", required=True),
            ToolParameter("text", "string", "Text to type", required=True),
            ToolParameter("selector_type", "string", "Type of selector: 'css', 'xpath', or 'text'", required=False)
        ],
        executor=browser_type_executor,
        result_formatter=format_browser_result
    ))
    
    registry.register(ToolMetadata(
        name="fill_form",
        description="Fill multiple form fields with data. Provide a dictionary where keys are CSS selectors and values are the text to fill.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[
            ToolParameter("form_data", "object", "Dictionary mapping field selectors to values", required=True)
        ],
        executor=browser_fill_form_executor,
        result_formatter=format_browser_result
    ))
    
    registry.register(ToolMetadata(
        name="press_key",
        description="Press a keyboard key (enter, tab, escape, space, arrow keys, etc.). Use this to submit forms, navigate, or interact with page elements.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[
            ToolParameter("key", "string", "Key to press (enter, tab, escape, space, arrow_up, etc.)", required=True)
        ],
        executor=browser_press_key_executor,
        result_formatter=format_browser_result
    ))
    
    # Page content and information tools
    registry.register(ToolMetadata(
        name="get_page_content",
        description="Get the text content of the current page.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[],
        executor=browser_get_content_executor,
        result_formatter=format_browser_result
    ))
    
    registry.register(ToolMetadata(
        name="get_page_fonts",
        description="Get detailed font information from the current page including font families, sizes, weights, usage statistics, and CSS @font-face rules. This analyzes the DOM to find all fonts actually being used on the page.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[],
        executor=browser_get_fonts_executor,
        result_formatter=format_font_result
    ))
    

    
    registry.register(ToolMetadata(
        name="get_element_info",
        description="Get detailed information about an element on the page including tag name, attributes, text content, and visibility status.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[
            ToolParameter("selector", "string", "Element selector (CSS, XPath, or text)", required=True),
            ToolParameter("selector_type", "string", "Type of selector: 'css', 'xpath', or 'text'", required=False)
        ],
        executor=browser_get_element_info_executor,
        result_formatter=format_browser_result
    ))
    
    registry.register(ToolMetadata(
        name="get_all_links",
        description="Get all links on the current page with their text, URLs, and visibility status. Useful for finding navigation options or clickable elements.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[],
        executor=browser_get_all_links_executor,
        result_formatter=format_browser_result
    ))
    
    registry.register(ToolMetadata(
        name="get_page_metadata",
        description="Get comprehensive page metadata including title, description, meta tags, Open Graph data, and SEO information.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[],
        executor=browser_get_page_metadata_executor,
        result_formatter=format_browser_result
    ))
    
    # Tab management tools
    registry.register(ToolMetadata(
        name="get_tabs",
        description="Get list of all open tabs in the browser.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[],
        executor=browser_get_tabs_executor,
        result_formatter=format_browser_result
    ))
    
    registry.register(ToolMetadata(
        name="switch_to_tab",
        description="Switch to a specific tab by index.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[
            ToolParameter("tab_index", "integer", "Tab index to switch to (0-based)", required=True)
        ],
        executor=browser_switch_to_tab_executor,
        result_formatter=format_browser_result
    ))
    
    registry.register(ToolMetadata(
        name="close_current_tab",
        description="Close the current tab.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[],
        executor=browser_close_current_tab_executor,
        result_formatter=format_browser_result
    ))
    
    # Page interaction tools
    registry.register(ToolMetadata(
        name="scroll_page",
        description="Scroll the page up, down, or to a specific position.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[
            ToolParameter("direction", "string", "Scroll direction: 'up', 'down', 'left', 'right', or 'to'", required=False),
            ToolParameter("amount", "integer", "Scroll amount in pixels", required=False),
            ToolParameter("selector", "string", "Element selector to scroll to (when direction is 'to')", required=False)
        ],
        executor=browser_scroll_page_executor,
        result_formatter=format_browser_result
    ))
    
    registry.register(ToolMetadata(
        name="highlight_element",
        description="Highlight an element on the page for debugging purposes.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[
            ToolParameter("selector", "string", "Element selector to highlight", required=True),
            ToolParameter("color", "string", "Highlight color", required=False),
            ToolParameter("duration", "integer", "Highlight duration in milliseconds", required=False)
        ],
        executor=browser_highlight_element_executor,
        result_formatter=format_browser_result
    ))
    
    # Page management tools
    registry.register(ToolMetadata(
        name="wait_for_page_load",
        description="Wait for the page to fully load.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[
            ToolParameter("timeout", "integer", "Timeout in seconds", required=False)
        ],
        executor=browser_wait_for_page_load_executor,
        result_formatter=format_browser_result
    ))
    
    registry.register(ToolMetadata(
        name="execute_javascript",
        description="Execute custom JavaScript code on the current page.",
        category=ToolCategory.BROWSER,
        server_path="browser_control",
        requires_auth=False,
        parameters=[
            ToolParameter("script", "string", "JavaScript code to execute", required=True)
        ],
        executor=browser_execute_javascript_executor,
        result_formatter=format_browser_result
    ))
    
    print("✅ Browser control tools registered successfully!") 