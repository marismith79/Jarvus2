from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.relative_locator import locate_with
import logging
import json
from typing import Dict, Any, Optional
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserService:
    def __init__(self):
        self.drivers: Dict[str, webdriver.Chrome] = {}
        self.performance_metrics: Dict[str, Dict[str, float]] = {}

    def create_driver(self, session_id: str) -> webdriver.Chrome:
        """Create a new Chromium WebDriver instance in headless mode"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1280,1024')
        driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            options=chrome_options
        )
        self.drivers[session_id] = driver
        return driver

    def get_driver(self, session_id: str) -> Optional[webdriver.Chrome]:
        """Get an existing WebDriver instance"""
        return self.drivers.get(session_id)

    def execute_action(self, session_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a browser action"""
        driver = self.get_driver(session_id)
        if not driver:
            raise ValueError(f"No active driver for session {session_id}")

        action_type = action.get('type')
        params = action.get('params', {})

        try:
            # Navigation
            if action_type == 'navigate':
                driver.get(params.get('url'))
                return {'status': 'success', 'url': driver.current_url}
            elif action_type == 'back':
                driver.back()
                return {'status': 'success'}
            elif action_type == 'forward':
                driver.forward()
                return {'status': 'success'}
            elif action_type == 'refresh':
                driver.refresh()
                return {'status': 'success'}

            # Element finding
            elif action_type == 'find_element':
                by = params.get('by', 'css')
                value = params.get('value')
                element = self._find_element(driver, by, value)
                return {'status': 'success', 'element': str(element)}
            elif action_type == 'find_elements':
                by = params.get('by', 'css')
                value = params.get('value')
                elements = self._find_elements(driver, by, value)
                return {'status': 'success', 'count': len(elements)}

            # Element interaction
            elif action_type == 'click':
                element = self._find_element(driver, params.get('by', 'css'), params.get('selector'))
                element.click()
                return {'status': 'success'}
            elif action_type == 'type':
                element = self._find_element(driver, params.get('by', 'css'), params.get('selector'))
                element.clear()
                element.send_keys(params.get('text', ''))
                return {'status': 'success'}
            elif action_type == 'clear':
                element = self._find_element(driver, params.get('by', 'css'), params.get('selector'))
                element.clear()
                return {'status': 'success'}
            elif action_type == 'submit':
                element = self._find_element(driver, params.get('by', 'css'), params.get('selector'))
                element.submit()
                return {'status': 'success'}

            # Mouse and keyboard actions
            elif action_type == 'hover':
                from selenium.webdriver.common.action_chains import ActionChains
                element = self._find_element(driver, params.get('by', 'css'), params.get('selector'))
                ActionChains(driver).move_to_element(element).perform()
                return {'status': 'success'}
            elif action_type == 'double_click':
                from selenium.webdriver.common.action_chains import ActionChains
                element = self._find_element(driver, params.get('by', 'css'), params.get('selector'))
                ActionChains(driver).double_click(element).perform()
                return {'status': 'success'}
            elif action_type == 'right_click':
                from selenium.webdriver.common.action_chains import ActionChains
                element = self._find_element(driver, params.get('by', 'css'), params.get('selector'))
                ActionChains(driver).context_click(element).perform()
                return {'status': 'success'}
            elif action_type == 'drag_and_drop':
                from selenium.webdriver.common.action_chains import ActionChains
                source = self._find_element(driver, params.get('by', 'css'), params.get('source'))
                target = self._find_element(driver, params.get('by', 'css'), params.get('target'))
                ActionChains(driver).drag_and_drop(source, target).perform()
                return {'status': 'success'}
            elif action_type == 'send_keys':
                from selenium.webdriver.common.keys import Keys
                element = self._find_element(driver, params.get('by', 'css'), params.get('selector'))
                keys = params.get('keys', '')
                element.send_keys(getattr(Keys, keys, keys))
                return {'status': 'success'}

            # Window and frame management
            elif action_type == 'switch_to_window':
                driver.switch_to.window(params.get('handle'))
                return {'status': 'success'}
            elif action_type == 'switch_to_frame':
                driver.switch_to.frame(params.get('frame'))
                return {'status': 'success'}
            elif action_type == 'switch_to_default_content':
                driver.switch_to.default_content()
                return {'status': 'success'}
            elif action_type == 'maximize_window':
                driver.maximize_window()
                return {'status': 'success'}
            elif action_type == 'minimize_window':
                driver.minimize_window()
                return {'status': 'success'}
            elif action_type == 'resize_window':
                width = params.get('width')
                height = params.get('height')
                driver.set_window_size(width, height)
                return {'status': 'success'}

            # JavaScript execution
            elif action_type == 'execute_script':
                result = driver.execute_script(params.get('script'), *params.get('args', []))
                return {'status': 'success', 'result': result}

            # Cookie management
            elif action_type == 'get_cookies':
                cookies = driver.get_cookies()
                return {'status': 'success', 'cookies': cookies}
            elif action_type == 'add_cookie':
                driver.add_cookie(params.get('cookie'))
                return {'status': 'success'}
            elif action_type == 'delete_cookie':
                driver.delete_cookie(params.get('name'))
                return {'status': 'success'}
            elif action_type == 'delete_all_cookies':
                driver.delete_all_cookies()
                return {'status': 'success'}

            # Alert/modal handling
            elif action_type == 'accept_alert':
                driver.switch_to.alert.accept()
                return {'status': 'success'}
            elif action_type == 'dismiss_alert':
                driver.switch_to.alert.dismiss()
                return {'status': 'success'}
            elif action_type == 'get_alert_text':
                text = driver.switch_to.alert.text
                return {'status': 'success', 'text': text}
            elif action_type == 'send_alert_text':
                driver.switch_to.alert.send_keys(params.get('text', ''))
                return {'status': 'success'}

            # File upload
            elif action_type == 'upload_file':
                element = self._find_element(driver, params.get('by', 'css'), params.get('selector'))
                element.send_keys(params.get('file_path'))
                return {'status': 'success'}

            # Tab management
            elif action_type == 'new_tab':
                driver.execute_script('window.open("");')
                return {'status': 'success'}
            elif action_type == 'close_tab':
                driver.close()
                return {'status': 'success'}
            elif action_type == 'get_window_handles':
                handles = driver.window_handles
                return {'status': 'success', 'handles': handles}
            elif action_type == 'get_current_window_handle':
                handle = driver.current_window_handle
                return {'status': 'success', 'handle': handle}

            # Scrolling
            elif action_type == 'scroll_to':
                x = params.get('x', 0)
                y = params.get('y', 0)
                driver.execute_script(f'window.scrollTo({x}, {y});')
                return {'status': 'success'}
            elif action_type == 'scroll_element_into_view':
                element = self._find_element(driver, params.get('by', 'css'), params.get('selector'))
                driver.execute_script('arguments[0].scrollIntoView(true);', element)
                return {'status': 'success'}

            # Storage
            elif action_type == 'get_local_storage':
                result = driver.execute_script('return window.localStorage;')
                return {'status': 'success', 'localStorage': result}
            elif action_type == 'set_local_storage':
                key = params.get('key')
                value = params.get('value')
                driver.execute_script(f'window.localStorage.setItem("{key}", "{value}");')
                return {'status': 'success'}
            elif action_type == 'get_session_storage':
                result = driver.execute_script('return window.sessionStorage;')
                return {'status': 'success', 'sessionStorage': result}
            elif action_type == 'set_session_storage':
                key = params.get('key')
                value = params.get('value')
                driver.execute_script(f'window.sessionStorage.setItem("{key}", "{value}");')
                return {'status': 'success'}

            # Page info
            elif action_type == 'get_page_source':
                return {'status': 'success', 'source': driver.page_source}
            elif action_type == 'get_title':
                return {'status': 'success', 'title': driver.title}
            elif action_type == 'get_url':
                return {'status': 'success', 'url': driver.current_url}
            elif action_type == 'screenshot':
                screenshot = driver.get_screenshot_as_base64()
                return {'status': 'success', 'screenshot': screenshot}

            # Relative Locators
            elif action_type == 'find_element_relative':
                base_element = self._find_element(driver, params.get('base_by', 'css'), params.get('base_value'))
                position = params.get('position')
                target_by = params.get('target_by', 'css')
                target_value = params.get('target_value')

                if position == 'above':
                    element = driver.find_element(By.CSS_SELECTOR, f"{target_value}").find_element(locate_with(By.CSS_SELECTOR, target_value).above(base_element))
                elif position == 'below':
                    element = driver.find_element(By.CSS_SELECTOR, f"{target_value}").find_element(locate_with(By.CSS_SELECTOR, target_value).below(base_element))
                elif position == 'to_left_of':
                    element = driver.find_element(By.CSS_SELECTOR, f"{target_value}").find_element(locate_with(By.CSS_SELECTOR, target_value).to_left_of(base_element))
                elif position == 'to_right_of':
                    element = driver.find_element(By.CSS_SELECTOR, f"{target_value}").find_element(locate_with(By.CSS_SELECTOR, target_value).to_right_of(base_element))
                elif position == 'near':
                    element = driver.find_element(By.CSS_SELECTOR, f"{target_value}").find_element(locate_with(By.CSS_SELECTOR, target_value).near(base_element))
                else:
                    raise ValueError(f"Invalid relative position: {position}")

                return {'status': 'success', 'element': str(element)}

            # Performance Monitoring
            elif action_type == 'start_performance_monitoring':
                self.performance_metrics[session_id] = {
                    'start_time': time.time(),
                    'metrics': {}
                }
                return {'status': 'success', 'message': 'Performance monitoring started'}

            elif action_type == 'get_performance_metrics':
                if session_id not in self.performance_metrics:
                    return {'status': 'error', 'message': 'Performance monitoring not started'}

                metrics = self.performance_metrics[session_id]
                metrics['end_time'] = time.time()
                metrics['duration'] = metrics['end_time'] - metrics['start_time']

                # Get navigation timing metrics
                navigation_timing = driver.execute_script("""
                    var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {};
                    var timing = performance.timing || {};
                    return {
                        'navigationStart': timing.navigationStart,
                        'loadEventEnd': timing.loadEventEnd,
                        'domComplete': timing.domComplete,
                        'domInteractive': timing.domInteractive,
                        'responseEnd': timing.responseEnd,
                        'responseStart': timing.responseStart,
                        'requestStart': timing.requestStart,
                        'connectEnd': timing.connectEnd,
                        'connectStart': timing.connectStart,
                        'domainLookupEnd': timing.domainLookupEnd,
                        'domainLookupStart': timing.domainLookupStart
                    };
                """)

                metrics['navigation_timing'] = navigation_timing
                return {'status': 'success', 'metrics': metrics}

            # Network Conditions
            elif action_type == 'set_network_conditions':
                # Use CDP (Chrome DevTools Protocol) through execute_cdp_cmd
                driver.execute_cdp_cmd('Network.enable', {})
                driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
                    'offline': params.get('offline', False),
                    'latency': params.get('latency', 0),
                    'downloadThroughput': params.get('download_throughput', -1),
                    'uploadThroughput': params.get('upload_throughput', -1),
                    'connectionType': params.get('connection_type', 'none')
                })
                return {'status': 'success', 'message': 'Network conditions set'}

            else:
                raise ValueError(f"Unknown action type: {action_type}")

        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return {'status': 'error', 'message': str(e)}

    def _find_element(self, driver, by, value):
        if by == 'css':
            return driver.find_element(By.CSS_SELECTOR, value)
        elif by == 'xpath':
            return driver.find_element(By.XPATH, value)
        elif by == 'id':
            return driver.find_element(By.ID, value)
        elif by == 'name':
            return driver.find_element(By.NAME, value)
        elif by == 'class':
            return driver.find_element(By.CLASS_NAME, value)
        elif by == 'tag':
            return driver.find_element(By.TAG_NAME, value)
        elif by == 'link_text':
            return driver.find_element(By.LINK_TEXT, value)
        elif by == 'partial_link_text':
            return driver.find_element(By.PARTIAL_LINK_TEXT, value)
        else:
            raise ValueError(f"Unknown locator strategy: {by}")

    def _find_elements(self, driver, by, value):
        if by == 'css':
            return driver.find_elements(By.CSS_SELECTOR, value)
        elif by == 'xpath':
            return driver.find_elements(By.XPATH, value)
        elif by == 'id':
            return driver.find_elements(By.ID, value)
        elif by == 'name':
            return driver.find_elements(By.NAME, value)
        elif by == 'class':
            return driver.find_elements(By.CLASS_NAME, value)
        elif by == 'tag':
            return driver.find_elements(By.TAG_NAME, value)
        elif by == 'link_text':
            return driver.find_elements(By.LINK_TEXT, value)
        elif by == 'partial_link_text':
            return driver.find_elements(By.PARTIAL_LINK_TEXT, value)
        else:
            raise ValueError(f"Unknown locator strategy: {by}")

    def cleanup(self, session_id: str):
        """Clean up a browser session"""
        if session_id in self.drivers:
            try:
                self.drivers[session_id].quit()
                del self.drivers[session_id]
            except Exception as e:
                logger.error(f"Error cleaning up driver: {e}")
                raise 