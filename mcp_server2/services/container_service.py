from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import uuid
import logging
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pydantic import BaseModel
import asyncio
from concurrent.futures import ThreadPoolExecutor
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionResponse(BaseModel):
    session_id: str
    status: str

class StatusResponse(BaseModel):
    status: str

class ContainerManager:
    def __init__(self):
        self.sessions = {}
        self.executor = ThreadPoolExecutor()
        logger.info("ContainerManager initialized")
        
    async def create_session(self, *args, **kwargs):
        """Create a new browser session"""
        session_id = None
        try:
            session_id = str(uuid.uuid4())
            logger.info(f"Starting to create session {session_id}")
            
            # Configure Firefox options
            options = Options()
            options.add_argument('--width=1280')
            options.add_argument('--height=1024')
            options.add_argument('--display=:99')
            options.binary_location = '/usr/bin/firefox'
            logger.info("Firefox options configured")
            
            # Create service with explicit geckodriver path
            service = Service(executable_path='/usr/local/bin/geckodriver')
            logger.info("Firefox service created")
            
            # Create new browser session in a thread pool
            logger.info("Creating new Firefox session...")
            loop = asyncio.get_event_loop()
            
            def create_driver():
                try:
                    driver = webdriver.Firefox(service=service, options=options)
                    logger.info("Firefox WebDriver created successfully")
                    return driver
                except Exception as e:
                    logger.error(f"Error creating Firefox WebDriver: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise
            
            driver = await loop.run_in_executor(self.executor, create_driver)
            
            # Wait for browser to be ready
            wait = WebDriverWait(driver, 10)
            logger.info("Loading about:blank page")
            
            def load_page():
                try:
                    driver.get("about:blank")
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    logger.info("Page loaded successfully")
                except Exception as e:
                    logger.error(f"Error loading page: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise
            
            await loop.run_in_executor(self.executor, load_page)
            
            self.sessions[session_id] = driver
            logger.info(f"Session {session_id} stored in sessions dictionary. Current sessions: {list(self.sessions.keys())}")
            
            return SessionResponse(session_id=session_id, status="created")
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            logger.error(traceback.format_exc())
            if session_id and session_id in self.sessions:
                try:
                    logger.info(f"Attempting to clean up failed session {session_id}")
                    await loop.run_in_executor(
                        self.executor,
                        lambda: self.sessions[session_id].quit()
                    )
                except Exception as cleanup_error:
                    logger.error(f"Error during cleanup: {str(cleanup_error)}")
                    logger.error(traceback.format_exc())
                del self.sessions[session_id]
            raise
        
    async def delete_session(self, session_id):
        """Delete a browser session"""
        try:
            logger.info(f"Attempting to delete session {session_id}. Current sessions: {list(self.sessions.keys())}")
            if session_id in self.sessions:
                driver = self.sessions[session_id]
                loop = asyncio.get_event_loop()
                logger.info(f"Quitting driver for session {session_id}")
                await loop.run_in_executor(
                    self.executor,
                    lambda: driver.quit()
                )
                del self.sessions[session_id]
                logger.info(f"Session {session_id} deleted successfully. Remaining sessions: {list(self.sessions.keys())}")
                return StatusResponse(status="deleted")
            logger.warning(f"Session {session_id} not found")
            return StatusResponse(status="not_found")
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        
    async def get_session(self, session_id):
        """Get a browser session"""
        try:
            logger.info(f"Checking session {session_id}. Current sessions: {list(self.sessions.keys())}")
            session = self.sessions.get(session_id)
            if session:
                logger.info(f"Session {session_id} retrieved successfully")
                return StatusResponse(status="active")
            logger.warning(f"Session {session_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise 