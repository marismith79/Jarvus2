"""
HTTP Client for Browser Control
Replaces direct Playwright calls with HTTP requests to Electron's Browser API server.
"""

import logging
import requests
import json
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class BrowserHTTPClient:
    """HTTP client for communicating with Electron's Browser API server."""
    
    def __init__(self, base_url: str = "http://localhost:3001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make HTTP request to browser API server."""
        try:
            url = f"{self.base_url}{endpoint}"
            logger.debug(f"Making {method} request to {url}")
            
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            else:
                return {"success": False, "error": f"Unsupported HTTP method: {method}"}
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to browser API server")
            return {"success": False, "error": "Browser API server not available"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {"success": False, "error": str(e)}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {"success": False, "error": f"Invalid JSON response: {e}"}
    
    def health_check(self) -> Dict[str, Any]:
        """Check if browser API server is healthy."""
        return self._make_request('GET', '/api/browser/health')
    
    def connect_to_browser(self) -> Dict[str, Any]:
        """Connect to browser."""
        return self._make_request('POST', '/api/browser/connect')
    
    def navigate_to_url(self, url: str, new_tab: bool = True) -> Dict[str, Any]:
        """Navigate to URL."""
        data = {"url": url, "new_tab": new_tab}
        return self._make_request('POST', '/api/browser/navigate', data)
    
    def click_element(self, selector: str, selector_type: str = "css") -> Dict[str, Any]:
        """Click element."""
        data = {"selector": selector, "selector_type": selector_type}
        return self._make_request('POST', '/api/browser/click', data)
    
    def type_text(self, selector: str, text: str, selector_type: str = "css") -> Dict[str, Any]:
        """Type text into element."""
        data = {"selector": selector, "text": text, "selector_type": selector_type}
        return self._make_request('POST', '/api/browser/type', data)
    
    def get_page_content(self) -> Dict[str, Any]:
        """Get page content."""
        return self._make_request('GET', '/api/browser/content')
    
    def get_tabs(self) -> Dict[str, Any]:
        """Get tabs information."""
        return self._make_request('GET', '/api/browser/tabs')
    
    def switch_to_tab(self, tab_index: int) -> Dict[str, Any]:
        """Switch to tab."""
        data = {"tab_index": tab_index}
        return self._make_request('POST', '/api/browser/switch-tab', data)
    
    def close_current_tab(self) -> Dict[str, Any]:
        """Close current tab."""
        return self._make_request('POST', '/api/browser/close-tab')
    
    def execute_javascript(self, script: str) -> Dict[str, Any]:
        """Execute JavaScript."""
        data = {"script": script}
        return self._make_request('POST', '/api/browser/execute-js', data)
    
    def take_screenshot(self, path: str = None) -> Dict[str, Any]:
        """Take screenshot."""
        data = {"path": path} if path else {}
        return self._make_request('POST', '/api/browser/screenshot', data)
    
    def take_screenshot_auto(self) -> Dict[str, Any]:
        """Take automatic screenshot and return base64 data."""
        return self._make_request('POST', '/api/browser/screenshot-auto', {})
    
    def get_fonts(self) -> Dict[str, Any]:
        """Get fonts from page."""
        return self._make_request('GET', '/api/browser/fonts')
    
    def fill_form(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Fill form fields."""
        data = {"form_data": form_data}
        return self._make_request('POST', '/api/browser/fill-form', data)
    
    def press_key(self, key: str) -> Dict[str, Any]:
        """Press key."""
        data = {"key": key}
        return self._make_request('POST', '/api/browser/press-key', data)
    
    def get_element_info(self, selector: str, selector_type: str = "css") -> Dict[str, Any]:
        """Get element information."""
        data = {"selector": selector, "selector_type": selector_type}
        return self._make_request('POST', '/api/browser/element-info', data)
    
    def get_all_links(self) -> Dict[str, Any]:
        """Get all links on page."""
        return self._make_request('GET', '/api/browser/links')
    
    def get_page_metadata(self) -> Dict[str, Any]:
        """Get page metadata."""
        return self._make_request('GET', '/api/browser/metadata')
    
    def scroll_page(self, direction: str = "down", amount: int = 500, selector: str = "") -> Dict[str, Any]:
        """Scroll page."""
        data = {"direction": direction, "amount": amount}
        if selector:
            data["selector"] = selector
        return self._make_request('POST', '/api/browser/scroll', data)
    
    def highlight_element(self, selector: str, color: str = "red", duration: int = 3000) -> Dict[str, Any]:
        """Highlight element."""
        data = {"selector": selector, "color": color, "duration": duration}
        return self._make_request('POST', '/api/browser/highlight', data)
    
    def wait_for_page_load(self, timeout: int = 30) -> Dict[str, Any]:
        """Wait for page load."""
        data = {"timeout": timeout}
        return self._make_request('POST', '/api/browser/wait-load', data)

# Global instance
browser_client = BrowserHTTPClient()

# Convenience functions that match the old sync interface
def sync_navigate_to_url(url: str, tab_index: int = 0, new_tab: bool = True) -> Dict[str, Any]:
    """Synchronously navigate to URL."""
    return browser_client.navigate_to_url(url, new_tab)

def sync_open_url_in_new_tab(url: str) -> Dict[str, Any]:
    """Synchronously open URL in new tab."""
    return browser_client.navigate_to_url(url, new_tab=True)

def sync_click_element(selector: str, selector_type: str = "css") -> Dict[str, Any]:
    """Synchronously click element."""
    return browser_client.click_element(selector, selector_type)

def sync_type_text(selector: str, text: str, selector_type: str = "css") -> Dict[str, Any]:
    """Synchronously type text into element."""
    return browser_client.type_text(selector, text, selector_type)

def sync_get_page_content() -> Dict[str, Any]:
    """Synchronously get current page content."""
    return browser_client.get_page_content()

def sync_get_tabs() -> List[Dict[str, Any]]:
    """Synchronously get information about all tabs."""
    result = browser_client.get_tabs()
    if result.get("success"):
        return result.get("tabs", [])
    return []

def sync_switch_to_tab(tab_index: int) -> Dict[str, Any]:
    """Synchronously switch to specified tab."""
    return browser_client.switch_to_tab(tab_index)

def sync_close_current_tab() -> Dict[str, Any]:
    """Synchronously close current tab."""
    return browser_client.close_current_tab()

def sync_take_screenshot(path: str = None) -> Dict[str, Any]:
    """Synchronously take screenshot of current page."""
    return browser_client.take_screenshot(path)

def sync_take_screenshot_auto() -> Dict[str, Any]:
    """Synchronously take automatic screenshot and return base64 data."""
    return browser_client.take_screenshot_auto()

def sync_execute_javascript(script: str) -> Dict[str, Any]:
    """Synchronously execute JavaScript on current page."""
    return browser_client.execute_javascript(script)

def sync_get_fonts() -> Dict[str, Any]:
    """Synchronously get fonts from current page."""
    return browser_client.get_fonts()

def sync_launch_browser(profile_name: str = None) -> bool:
    """Synchronously connect to existing browser (launching is handled by desktop app)."""
    result = browser_client.connect_to_browser()
    return result.get("success", False) 