from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import json
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserService:
    def __init__(self):
        self.drivers: Dict[str, webdriver.Firefox] = {}

    def create_driver(self, session_id: str) -> webdriver.Firefox:
        """Create a new Firefox WebDriver instance"""
        firefox_options = Options()
        firefox_options.add_argument('--headless')
        firefox_options.add_argument('--width=1280')
        firefox_options.add_argument('--height=1024')

        service = Service('/usr/local/bin/geckodriver')
        driver = webdriver.Firefox(service=service, options=firefox_options)
        self.drivers[session_id] = driver
        return driver

    def get_driver(self, session_id: str) -> Optional[webdriver.Firefox]:
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
            if action_type == 'navigate':
                driver.get(params.get('url'))
                return {'status': 'success', 'url': driver.current_url}

            elif action_type == 'click':
                element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, params.get('selector')))
                )
                element.click()
                return {'status': 'success'}

            elif action_type == 'type':
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, params.get('selector')))
                )
                element.clear()
                element.send_keys(params.get('text', ''))
                return {'status': 'success'}

            elif action_type == 'screenshot':
                screenshot = driver.get_screenshot_as_base64()
                return {'status': 'success', 'screenshot': screenshot}

            else:
                raise ValueError(f"Unknown action type: {action_type}")

        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return {'status': 'error', 'message': str(e)}

    def cleanup(self, session_id: str):
        """Clean up a browser session"""
        if session_id in self.drivers:
            try:
                self.drivers[session_id].quit()
                del self.drivers[session_id]
            except Exception as e:
                logger.error(f"Error cleaning up driver: {e}")
                raise 