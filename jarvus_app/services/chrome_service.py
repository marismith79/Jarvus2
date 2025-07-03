# jarvus_app/services/comprehensive_chrome_control.py
"""
Comprehensive Chrome Control Service
Provides complete browser automation using Chrome DevTools Protocol.
All essential Chrome control tools in one place.
"""

import json
import time
import logging
import base64
from typing import Dict, Any, Optional, List, Tuple
import requests
import websocket
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

class ChromeControl:
    """Comprehensive Chrome control using DevTools Protocol."""
    
    def __init__(self, debug_port: int = 9222):
        self.debug_port = debug_port
        self.base_url = f"http://localhost:{debug_port}"
        self.current_tab_id = None
        self.current_ws = None
        self._message_id = 1  # Use a simple incrementing integer for DevTools message IDs
    
    def connect_to_chrome(self) -> bool:
        """Connect to existing Chrome instance with remote debugging enabled."""
        try:
            response = requests.get(f"{self.base_url}/json/version", timeout=5)
            if response.status_code == 200:
                logger.info("Chrome DevTools Protocol is accessible")
                return True
            else:
                logger.error(f"Chrome DevTools Protocol not accessible: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Chrome DevTools Protocol: {e}")
            logger.info("Make sure Chrome is running with: --remote-debugging-port=9222")
            return False
    
    def get_tabs(self) -> List[Dict[str, Any]]:
        """Get list of all open tabs."""
        try:
            response = requests.get(f"{self.base_url}/json/list", timeout=5)
            if response.status_code == 200:
                tabs = response.json()
                return [tab for tab in tabs if tab.get('type') == 'page']
            return []
        except Exception as e:
            logger.error(f"Failed to get tabs: {e}")
            return []
    
    def _get_current_tab_id(self) -> Optional[str]:
        """Get the current active tab ID."""
        if self.current_tab_id:
            return self.current_tab_id
        
        tabs = self.get_tabs()
        if tabs:
            self.current_tab_id = tabs[0]['id']
            return self.current_tab_id
        return None
    
    def _send_devtools_command(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to Chrome DevTools Protocol via WebSocket."""
        tab_id = self._get_current_tab_id()
        if not tab_id:
            logger.error("No active tab ID available")
            return {"success": False, "error": "No active tab"}
        
        # Ensure we have a WebSocket connection
        if not self._ensure_websocket_connection():
            return {"success": False, "error": "Failed to establish WebSocket connection"}
        
        payload = {
            "id": self._message_id,
            "method": method,
            "params": params or {}
        }
        
        logger.info(f"Sending DevTools command: {method} to tab {tab_id}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            # Send command via WebSocket
            self.current_ws.send(json.dumps(payload))
            
            # Get response
            response = self.current_ws.recv()
            logger.debug(f"WebSocket response: {response}")
            
            result = json.loads(response)
            logger.debug(f"Parsed response: {json.dumps(result, indent=2)}")
            
            # Check if there's an error in the response
            if "error" in result:
                logger.error(f"DevTools error: {result['error']}")
                return {"success": False, "error": result["error"].get("message", "DevTools error")}
            
            self._message_id += 1
            return {"success": True, "result": result}
                
        except Exception as e:
            logger.error(f"DevTools command error: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}
    
    def _ensure_websocket_connection(self) -> bool:
        """Ensure WebSocket connection is established for the current tab."""
        try:
            if self.current_ws and self.current_ws.connected:
                return True
            
            # Get WebSocket URL for current tab
            tabs = self.get_tabs()
            current_tab = None
            for tab in tabs:
                if tab.get('id') == self.current_tab_id:
                    current_tab = tab
                    break
            
            if not current_tab:
                logger.error("Current tab not found in tabs list")
                return False
            
            ws_url = current_tab.get('webSocketDebuggerUrl')
            if not ws_url:
                logger.error("No WebSocket URL available for current tab")
                return False
            
            logger.info(f"Connecting to WebSocket: {ws_url}")
            
            # Create WebSocket connection
            self.current_ws = websocket.create_connection(ws_url, timeout=10)
            logger.info("WebSocket connection established")
            return True
            
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {e}")
            return False
    
    def navigate_to_url(self, url: str, tab_index: int = 0, new_tab: bool = False) -> Dict[str, Any]:
        """Navigate to a URL in the specified tab or create a new tab."""
        try:
            if new_tab:
                return self.open_url_in_new_tab(url)
            
            tabs = self.get_tabs()
            if not tabs or tab_index >= len(tabs):
                return {"success": False, "error": "No tabs available or invalid tab index"}
            
            tab = tabs[tab_index]
            self.current_tab_id = tab['id']
            
            result = self._send_devtools_command("Page.navigate", {"url": url})
            if result["success"]:
                return {"success": True, "url": url, "tab_id": self.current_tab_id}
            else:
                return result
                
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return {"success": False, "error": str(e)}
    
    def click_element(self, selector: str, selector_type: str = "css") -> Dict[str, Any]:
        """Click an element on the page using DevTools Protocol."""
        try:
            # First, find the element
            if selector_type == "css":
                find_result = self._send_devtools_command("Runtime.evaluate", {
                    "expression": f"document.querySelector('{selector}')",
                    "returnByValue": False
                })
            elif selector_type == "xpath":
                find_result = self._send_devtools_command("Runtime.evaluate", {
                    "expression": f"document.evaluate('{selector}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue",
                    "returnByValue": False
                })
            else:
                return {"success": False, "error": "Unsupported selector type"}
            
            if not find_result["success"]:
                return find_result
            
            # Check if element was found
            result = find_result["result"]
            if not result.get("result", {}).get("value"):
                return {"success": False, "error": f"Element not found: {selector}"}
            
            # Click the element
            click_result = self._send_devtools_command("Runtime.evaluate", {
                "expression": f"document.querySelector('{selector}').click()",
                "returnByValue": True
            })
            
            if click_result["success"]:
                return {"success": True, "message": f"Clicked element: {selector}"}
            else:
                return click_result
                
        except Exception as e:
            logger.error(f"Click error: {e}")
            return {"success": False, "error": str(e)}
    
    def type_text(self, selector: str, text: str, selector_type: str = "css") -> Dict[str, Any]:
        """Type text into an input element."""
        try:
            # Focus the element first
            focus_result = self._send_devtools_command("Runtime.evaluate", {
                "expression": f"document.querySelector('{selector}').focus()",
                "returnByValue": True
            })
            
            if not focus_result["success"]:
                return focus_result
            
            # Clear existing text
            clear_result = self._send_devtools_command("Runtime.evaluate", {
                "expression": f"document.querySelector('{selector}').value = ''",
                "returnByValue": True
            })
            
            if not clear_result["success"]:
                return clear_result
            
            # Type the text
            type_result = self._send_devtools_command("Runtime.evaluate", {
                "expression": f"document.querySelector('{selector}').value = '{text}'",
                "returnByValue": True
            })
            
            if type_result["success"]:
                return {"success": True, "message": f"Typed text into: {selector}"}
            else:
                return type_result
                
        except Exception as e:
            logger.error(f"Type error: {e}")
            return {"success": False, "error": str(e)}
    
    def scroll_page(self, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        """Scroll the page up or down."""
        try:
            if direction.lower() == "down":
                scroll_script = f"window.scrollBy(0, {amount})"
            elif direction.lower() == "up":
                scroll_script = f"window.scrollBy(0, -{amount})"
            elif direction.lower() == "left":
                scroll_script = f"window.scrollBy(-{amount}, 0)"
            elif direction.lower() == "right":
                scroll_script = f"window.scrollBy({amount}, 0)"
            else:
                return {"success": False, "error": "Invalid direction. Use: up, down, left, right"}
            
            result = self._send_devtools_command("Runtime.evaluate", {
                "expression": scroll_script,
                "returnByValue": True
            })
            
            if result["success"]:
                return {"success": True, "message": f"Scrolled {direction} by {amount}px"}
            else:
                return result
                
        except Exception as e:
            logger.error(f"Scroll error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_element_info(self, selector: str, selector_type: str = "css") -> Dict[str, Any]:
        """Get detailed information about an element."""
        try:
            if selector_type == "css":
                script = f"""
                (function() {{
                    const element = document.querySelector('{selector}');
                    if (!element) return null;
                    
                    const rect = element.getBoundingClientRect();
                    return {{
                        tagName: element.tagName,
                        id: element.id,
                        className: element.className,
                        textContent: element.textContent?.substring(0, 100),
                        value: element.value,
                        href: element.href,
                        src: element.src,
                        position: {{
                            x: rect.left,
                            y: rect.top,
                            width: rect.width,
                            height: rect.height
                        }},
                        isVisible: rect.width > 0 && rect.height > 0,
                        ariaLabel: element.getAttribute('aria-label'),
                        role: element.getAttribute('role')
                    }};
                }})()
                """
            else:
                return {"success": False, "error": "Only CSS selectors supported for now"}
            
            result = self._send_devtools_command("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True
            })
            
            if result["success"]:
                element_info = result["result"].get("result", {}).get("value")
                if element_info:
                    return {"success": True, "element": element_info}
                else:
                    return {"success": False, "error": f"Element not found: {selector}"}
            else:
                return result
                
        except Exception as e:
            logger.error(f"Get element info error: {e}")
            return {"success": False, "error": str(e)}
    
    def wait_for_element(self, selector: str, timeout: int = 10) -> Dict[str, Any]:
        """Wait for an element to appear on the page."""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                result = self.get_element_info(selector)
                if result["success"]:
                    return {"success": True, "message": f"Element found: {selector}"}
                time.sleep(0.5)
            
            return {"success": False, "error": f"Element not found within {timeout} seconds: {selector}"}
            
        except Exception as e:
            logger.error(f"Wait for element error: {e}")
            return {"success": False, "error": str(e)}
    
    def take_screenshot(self, selector: str = None) -> Dict[str, Any]:
        """Take a screenshot of the page or specific element."""
        try:
            if selector:
                # Screenshot specific element
                script = f"""
                (function() {{
                    const element = document.querySelector('{selector}');
                    if (!element) return null;
                    
                    const rect = element.getBoundingClientRect();
                    return {{
                        x: rect.left,
                        y: rect.top,
                        width: rect.width,
                        height: rect.height
                    }};
                }})()
                """
                
                result = self._send_devtools_command("Runtime.evaluate", {
                    "expression": script,
                    "returnByValue": True
                })
                
                if not result["success"]:
                    return result
                
                element_rect = result["result"].get("result", {}).get("value")
                if not element_rect:
                    return {"success": False, "error": f"Element not found: {selector}"}
                
                # Take screenshot of element area
                screenshot_result = self._send_devtools_command("Page.captureScreenshot", {
                    "clip": element_rect,
                    "format": "png"
                })
            else:
                # Screenshot entire page
                screenshot_result = self._send_devtools_command("Page.captureScreenshot", {
                    "format": "png"
                })
            
            if screenshot_result["success"]:
                result_data = screenshot_result["result"]
                if "result" in result_data and "data" in result_data["result"]:
                    return {
                        "success": True,
                        "screenshot_data": result_data["result"]["data"],
                        "element": selector if selector else "full_page"
                    }
            
            return {"success": False, "error": "Screenshot failed"}
            
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_page_content(self) -> Dict[str, Any]:
        """Get the text content of the current page."""
        try:
            script = """
            (function() {
                return {
                    title: document.title,
                    url: window.location.href,
                    textContent: document.body.innerText,
                    htmlContent: document.documentElement.outerHTML.substring(0, 10000) // Limit size
                };
            })()
            """
            
            result = self._send_devtools_command("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True
            })
            
            if result["success"]:
                content = result["result"].get("result", {}).get("value")
                if content:
                    return {
                        "success": True,
                        "content": content
                    }
            
            return {"success": False, "error": "Failed to get page content"}
            
        except Exception as e:
            logger.error(f"Content extraction error: {e}")
            return {"success": False, "error": str(e)}

    def create_new_tab(self, url: str = None) -> Dict[str, Any]:
        """Create a new tab and optionally navigate to a URL."""
        try:
            import platform
            import subprocess
            # First, get current tabs to understand the structure
            tabs = self.get_tabs()
            if not tabs:
                return {"success": False, "error": "No tabs available"}
            
            # Try different methods to create a new tab
            # Method 1: Try Target.createTarget (Chrome DevTools Protocol)
            result = self._send_devtools_command("Target.createTarget", {
                "url": url or "about:blank"
            })
            
            if result["success"]:
                new_tab_id = result["result"].get("targetId")
                if new_tab_id:
                    # Update current tab ID to the new tab
                    self.current_tab_id = new_tab_id
                    return {
                        "success": True, 
                        "tab_id": new_tab_id, 
                        "url": url,
                        "message": "New tab created successfully using Target.createTarget"
                    }
            
            # Method 2: Try using Page.createTarget (alternative method) - only if Method 1 failed
            if not result["success"]:
                result = self._send_devtools_command("Page.createTarget", {
                    "url": url or "about:blank"
                })
                
                if result["success"]:
                    new_tab_id = result["result"].get("targetId")
                    if new_tab_id:
                        self.current_tab_id = new_tab_id
                        return {
                            "success": True, 
                            "tab_id": new_tab_id, 
                            "url": url,
                            "message": "New tab created successfully using Page.createTarget"
                        }
            
            # Method 3: Try using JavaScript to open a new tab - only if previous methods failed
            if not result["success"]:
                script = f"window.open('{url or 'about:blank'}', '_blank');"
                result = self._send_devtools_command("Runtime.evaluate", {
                    "expression": script,
                    "returnByValue": True
                })
                
                if result["success"]:
                    # Get updated tabs list
                    new_tabs = self.get_tabs()
                    if len(new_tabs) > len(tabs):
                        # A new tab was created
                        new_tab = new_tabs[-1]  # Get the last tab (newest)
                        self.current_tab_id = new_tab['id']
                        return {
                            "success": True,
                            "tab_id": new_tab['id'],
                            "url": url,
                            "message": "New tab created successfully using JavaScript window.open"
                        }
            
            # Method 4: AppleScript fallback for macOS - only if all previous methods failed
            if not result["success"] and platform.system() == "Darwin":
                try:
                    applescript = f'''osascript -e 'tell application "Google Chrome" to activate' -e 'tell application "Google Chrome" to tell window 1 to make new tab with properties {{URL:"{url or 'about:blank'}"}}' '''
                    subprocess.run(applescript, shell=True, check=True)
                    return {
                        "success": True,
                        "tab_id": None,
                        "url": url,
                        "message": "New tab created successfully using AppleScript fallback on macOS"
                    }
                except Exception as e:
                    return {"success": False, "error": f"AppleScript fallback failed: {e}"}
            
            # If all methods fail, return detailed error
            return {
                "success": False, 
                "error": "Failed to create new tab using any method (including AppleScript)",
                "debug_info": {
                    "original_tabs_count": len(tabs),
                    "target_create_result": result.get("error", "Unknown"),
                    "available_methods": ["Target.createTarget", "Page.createTarget", "JavaScript window.open", "AppleScript (macOS)"]
                }
            }
                
        except Exception as e:
            logger.error(f"Create new tab error: {e}")
            return {"success": False, "error": str(e)}

    def open_url_in_new_tab(self, url: str) -> Dict[str, Any]:
        """Open a URL in a new tab and ensure it's visible to the user."""
        try:
            # Create a new tab with the URL
            result = self.create_new_tab(url)
            if result["success"]:
                # Get the new tab ID
                new_tab_id = result["tab_id"]
                
                # Ensure the new tab is active and visible
                if new_tab_id:
                    # Switch to the new tab to make it active
                    self.current_tab_id = new_tab_id
                    
                    # Try to activate the tab using DevTools Protocol
                    activate_result = self._send_devtools_command("Target.activateTarget", {
                        "targetId": new_tab_id
                    })
                    
                    if not activate_result["success"]:
                        logger.warning(f"Failed to activate target: {activate_result.get('error')}")
                
                return {
                    "success": True,
                    "url": url,
                    "tab_id": new_tab_id,
                    "message": f"Opened {url} in new tab and made it visible"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Open URL in new tab error: {e}")
            return {"success": False, "error": str(e)}

    def fill_form(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Fill multiple form fields with data."""
        try:
            results = []
            for field_selector, value in form_data.items():
                # Try to fill each field
                result = self.type_text(field_selector, value, "css")
                results.append({
                    "field": field_selector,
                    "value": value,
                    "success": result["success"],
                    "error": result.get("error")
                })
            
            success_count = sum(1 for r in results if r["success"])
            return {
                "success": success_count > 0,
                "filled_fields": success_count,
                "total_fields": len(form_data),
                "results": results,
                "message": f"Filled {success_count}/{len(form_data)} form fields"
            }
            
        except Exception as e:
            logger.error(f"Fill form error: {e}")
            return {"success": False, "error": str(e)}

    def highlight_element(self, selector: str, color: str = "red", duration: int = 3000) -> Dict[str, Any]:
        """Highlight an element on the page for debugging."""
        try:
            script = f"""
            (function() {{
                const element = document.querySelector('{selector}');
                if (!element) return false;
                
                const originalStyle = element.style.cssText;
                element.style.cssText += '; border: 3px solid {color} !important; background-color: rgba(255, 0, 0, 0.2) !important;';
                
                setTimeout(() => {{
                    element.style.cssText = originalStyle;
                }}, {duration});
                
                return true;
            }})()
            """
            
            result = self._send_devtools_command("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True
            })
            
            if result["success"]:
                highlighted = result["result"].get("result", {}).get("value")
                if highlighted:
                    return {
                        "success": True,
                        "message": f"Highlighted element: {selector}",
                        "color": color,
                        "duration": duration
                    }
                else:
                    return {"success": False, "error": f"Element not found: {selector}"}
            
            return result
            
        except Exception as e:
            logger.error(f"Highlight element error: {e}")
            return {"success": False, "error": str(e)}

    def press_key(self, key: str) -> Dict[str, Any]:
        """Press a keyboard key."""
        try:
            # Map common keys to their key codes
            key_map = {
                "enter": "Enter",
                "tab": "Tab",
                "escape": "Escape",
                "space": " ",
                "backspace": "Backspace",
                "delete": "Delete",
                "arrow_up": "ArrowUp",
                "arrow_down": "ArrowDown",
                "arrow_left": "ArrowLeft",
                "arrow_right": "ArrowRight",
                "home": "Home",
                "end": "End",
                "page_up": "PageUp",
                "page_down": "PageDown"
            }
            
            key_code = key_map.get(key.lower(), key)
            
            script = f"""
            (function() {{
                const event = new KeyboardEvent('keydown', {{
                    key: '{key_code}',
                    code: '{key_code}',
                    keyCode: '{key_code}'.charCodeAt(0),
                    which: '{key_code}'.charCodeAt(0),
                    bubbles: true,
                    cancelable: true
                }});
                document.activeElement.dispatchEvent(event);
                return true;
            }})()
            """
            
            result = self._send_devtools_command("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True
            })
            
            if result["success"]:
                return {
                    "success": True,
                    "key": key,
                    "message": f"Pressed key: {key}"
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Press key error: {e}")
            return {"success": False, "error": str(e)}

    def switch_to_tab(self, tab_index: int) -> Dict[str, Any]:
        """Switch to a specific tab by index."""
        try:
            tabs = self.get_tabs()
            if not tabs or tab_index >= len(tabs):
                return {"success": False, "error": f"Invalid tab index: {tab_index}"}
            
            tab = tabs[tab_index]
            self.current_tab_id = tab['id']
            
            # Close existing WebSocket connection
            if self.current_ws:
                try:
                    self.current_ws.close()
                except:
                    pass
                self.current_ws = None
            
            return {
                "success": True,
                "tab_index": tab_index,
                "tab_id": tab['id'],
                "url": tab.get('url', ''),
                "title": tab.get('title', ''),
                "message": f"Switched to tab {tab_index}"
            }
            
        except Exception as e:
            logger.error(f"Switch to tab error: {e}")
            return {"success": False, "error": str(e)}

    def close_current_tab(self) -> Dict[str, Any]:
        """Close the current tab."""
        try:
            if not self.current_tab_id:
                return {"success": False, "error": "No current tab to close"}
            
            # Use JavaScript to close the current tab
            script = "window.close();"
            result = self._send_devtools_command("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True
            })
            
            if result["success"]:
                # Update current tab ID to the first available tab
                tabs = self.get_tabs()
                if tabs:
                    self.current_tab_id = tabs[0]['id']
                
                return {
                    "success": True,
                    "message": "Current tab closed",
                    "new_current_tab": self.current_tab_id
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Close current tab error: {e}")
            return {"success": False, "error": str(e)}

    def get_all_links(self) -> Dict[str, Any]:
        """Get all links on the current page."""
        try:
            script = """
            (function() {
                const links = Array.from(document.querySelectorAll('a[href]'));
                return links.map(link => ({
                    text: link.textContent.trim(),
                    href: link.href,
                    title: link.title || '',
                    visible: link.offsetParent !== null
                })).filter(link => link.href && link.href !== 'javascript:void(0)');
            })()
            """
            
            result = self._send_devtools_command("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True
            })
            
            if result["success"]:
                links = result["result"].get("result", {}).get("value", [])
                return {
                    "success": True,
                    "links": links,
                    "count": len(links),
                    "message": f"Found {len(links)} links on the page"
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Get all links error: {e}")
            return {"success": False, "error": str(e)}

    def wait_for_page_load(self, timeout: int = 30) -> Dict[str, Any]:
        """Wait for the page to fully load."""
        try:
            import time
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                script = """
                (function() {
                    return document.readyState === 'complete';
                })()
                """
                
                result = self._send_devtools_command("Runtime.evaluate", {
                    "expression": script,
                    "returnByValue": True
                })
                
                if result["success"]:
                    is_loaded = result["result"].get("result", {}).get("value")
                    if is_loaded:
                        return {
                            "success": True,
                            "message": "Page loaded successfully",
                            "load_time": time.time() - start_time
                        }
                
                time.sleep(0.5)
            
            return {"success": False, "error": f"Page load timeout after {timeout} seconds"}
            
        except Exception as e:
            logger.error(f"Wait for page load error: {e}")
            return {"success": False, "error": str(e)}

    def execute_javascript(self, script: str) -> Dict[str, Any]:
        """Execute custom JavaScript on the page."""
        try:
            result = self._send_devtools_command("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True
            })
            
            if result["success"]:
                return_value = result["result"].get("result", {}).get("value")
                return {
                    "success": True,
                    "result": return_value,
                    "message": "JavaScript executed successfully"
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Execute JavaScript error: {e}")
            return {"success": False, "error": str(e)}

    def get_page_metadata(self) -> Dict[str, Any]:
        """Get comprehensive page metadata."""
        try:
            script = """
            (function() {
                return {
                    title: document.title,
                    url: window.location.href,
                    description: document.querySelector('meta[name="description"]')?.content || '',
                    keywords: document.querySelector('meta[name="keywords"]')?.content || '',
                    author: document.querySelector('meta[name="author"]')?.content || '',
                    viewport: document.querySelector('meta[name="viewport"]')?.content || '',
                    robots: document.querySelector('meta[name="robots"]')?.content || '',
                    og_title: document.querySelector('meta[property="og:title"]')?.content || '',
                    og_description: document.querySelector('meta[property="og:description"]')?.content || '',
                    og_image: document.querySelector('meta[property="og:image"]')?.content || '',
                    canonical: document.querySelector('link[rel="canonical"]')?.href || '',
                    language: document.documentElement.lang || '',
                    charset: document.characterSet || '',
                    readyState: document.readyState,
                    lastModified: document.lastModified,
                    domain: window.location.hostname,
                    pathname: window.location.pathname,
                    search: window.location.search,
                    hash: window.location.hash
                };
            })()
            """
            
            result = self._send_devtools_command("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True
            })
            
            if result["success"]:
                metadata = result["result"].get("result", {}).get("value", {})
                return {
                    "success": True,
                    "metadata": metadata,
                    "message": "Page metadata retrieved successfully"
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Get page metadata error: {e}")
            return {"success": False, "error": str(e)}

# Global instance
chrome_control = ChromeControl()