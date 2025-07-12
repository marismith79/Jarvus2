"""
Pipedream MCP Authentication Service
Handles authentication with Pipedream MCP API for token management.
"""

import os
import time
import logging
import requests
import json
from typing import Optional, Dict, Any, List
from flask import session
from flask_login import current_user

logger = logging.getLogger(__name__)


class PipedreamAuthService:
    """Service for managing Pipedream MCP authentication tokens."""
    
    def __init__(self):
        """Initialize the Pipedream authentication service."""
        self.base_url = "https://api.pipedream.com"
        self.auth_endpoint = f"{self.base_url}/v1/oauth/token"
        self.mcp_base_url = "https://remote.mcp.pipedream.net"
        
        # Load configuration from environment
        self.client_id = os.getenv("PIPEDREAM_API_CLIENT_ID")
        # print(f"PIPEDREAM_API_CLIENT_ID: {self.client_id}")
        self.client_secret = os.getenv("PIPEDREAM_API_CLIENT_SECRET")
        # print(f"PIPEDREAM_API_CLIENT_SECRET: {self.client_secret}")
        self.project_id = os.getenv("PIPEDREAM_PROJECT_ID")
        self.environment = os.getenv("PIPEDREAM_ENVIRONMENT", "development")
        self.refresh_threshold = int("3600")  # 10 minutes default
        # Don't set external_user_id during initialization - it should be passed as parameter
        
        if not self.client_id or not self.client_secret:
            logger.warning("Pipedream credentials not configured. MCP features will be disabled.")
    
    def get_access_token(self) -> Optional[str]:
        """
        Fetch initial access token from Pipedream using client credentials.
        
        Returns:
            Optional[str]: Access token if successful, None otherwise
        """
        if not self.client_id or not self.client_secret:
            logger.error("Pipedream credentials not configured")
            return None
        
        try:
            # logger.info("Fetching initial Pipedream access token")
            
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = requests.post(
                self.auth_endpoint,
                data=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3599)  # Default 1 hour
                
                # print(f"DEBUG: Token data: {token_data}")
                # print(f"DEBUG: Access token: {access_token}")
                # print(f"DEBUG: Expires in: {expires_in}")
                
                if access_token:
                    # Store token in session
                    self._store_token_in_session(access_token, expires_in)
                    # print("[DEBUG] Successfully acquired Pipedream access token")
                    return access_token
                else:
                    # print("No access_token in Pipedream response")
                    return None
            else:
                # print(f"Failed to acquire Pipedream token. Status: {response.status_code}, Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            # print(f"Request error acquiring Pipedream token: {str(e)}")
            return None
        except Exception as e:
            # print(f"Unexpected error acquiring Pipedream token: {str(e)}")
            return None
    
    def refresh_access_token(self) -> Optional[str]:
        """
        Get a new access token using client credentials (no refresh token needed).
        
        Returns:
            Optional[str]: New access token if successful, None otherwise
        """
        # logger.info("Getting new Pipedream access token using client credentials")
        return self.get_access_token()
    
    def get_token_from_session(self) -> Optional[str]:
        """
        Retrieve cached access token from session, getting new one if necessary.
        
        Returns:
            Optional[str]: Valid access token if available, None otherwise
        """
        # Check if we have a valid token in session
        if self.is_token_valid():
            access_token = session.get("pipedream_access_token")
            logger.debug("Using cached Pipedream access token")
            return access_token
        
        # Token is expired or missing, get a new one
        logger.info("Pipedream token expired or missing, getting new token")
        return self.refresh_access_token()
    
    def is_token_valid(self) -> bool:
        """
        Check if the current access token is valid and not expired.
        
        Returns:
            bool: True if token is valid, False otherwise
        """
        access_token = session.get("pipedream_access_token")
        expires_at = session.get("pipedream_token_expires_at")
        
        if not access_token or not expires_at:
            return False
        
        # Check if token is expired (with refresh threshold)
        current_time = int(time.time())
        refresh_time = expires_at - self.refresh_threshold
        
        if current_time >= refresh_time:
            logger.debug(f"Pipedream token expired or near expiry. Current: {current_time}, Expires: {expires_at}")
            return False
        
        return True
    
    def _store_token_in_session(self, access_token: str, expires_in: int) -> None:
        """
        Store token information in Flask session.
        
        Args:
            access_token: The access token string
            expires_in: Token expiration time in seconds
        """
        current_time = int(time.time())
        expires_at = current_time + expires_in
        
        session["pipedream_access_token"] = access_token
        session["pipedream_token_expires_at"] = expires_at
        session["pipedream_token_created_at"] = current_time
        
        logger.debug(f"Stored Pipedream token in session. Expires at: {expires_at}")
    
    def clear_session_tokens(self) -> None:
        """Clear all Pipedream tokens from the session."""
        session_keys = [
            "pipedream_access_token",
            "pipedream_token_expires_at", 
            "pipedream_token_created_at"
        ]
        
        for key in session_keys:
            session.pop(key, None)
        
        logger.info("Cleared Pipedream tokens")
    
    def get_auth_headers(self) -> Optional[Dict[str, str]]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Optional[Dict[str, str]]: Headers with Bearer token if available, None otherwise
        """
        token = self.get_token_from_session()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return None
    
    def get_mcp_auth_headers(self, external_user_id: str = None, app_slug: str = None, oauth_app_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Get authentication headers for MCP server requests.
        
        Args:
            external_user_id: The user's ID in your system (if None, uses current_user.id from session)
            app_slug: The app slug (e.g., 'notion', 'gmail', 'slack')
            oauth_app_id: Optional OAuth app ID for custom OAuth clients
            
        Returns:
            Optional[Dict[str, str]]: Headers for MCP requests if token available, None otherwise
        """
        token = self.get_token_from_session()
        if not token:
            logger.error("No Pipedream access token available for MCP request")
            return None
        
        # Use current_user.id from session if external_user_id is not provided
        if external_user_id is None:
            if current_user.is_authenticated:
                external_user_id = str(current_user.id)
            else:
                logger.error("No external_user_id provided and no authenticated user in session")
                return None
        
        headers = {
            "Authorization": f"Bearer {token}",
            "x-pd-project-id": self.project_id,
            "x-pd-environment": self.environment,
            "x-pd-external-user-id": external_user_id,
            "x-pd-app-slug": app_slug,
            "x-pd-tool-mode": "tools-only",
            "x-pd-oauth-app-id": oauth_app_id
        }
        
        return headers
    
    def discover_available_apps(self) -> Optional[Dict[str, Any]]:
        """
        Discover all available apps from Pipedream.
        
        Returns:
            Optional[Dict[str, Any]]: Available apps data if successful, None otherwise
        """
        if not self.project_id:
            logger.error("PIPEDREAM_PROJECT_ID not configured")
            return None
        
        try:
            logger.info("Discovering available Pipedream apps")
            
            headers = self.get_auth_headers()
            if not headers:
                return None
            
            response = requests.get(
                f"{self.base_url}/v1/apps",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                apps_data = response.json()
                logger.info(f"Successfully discovered {len(apps_data.get('data', []))} available apps")
                return apps_data
            else:
                logger.error(f"Failed to discover apps. Status: {response.status_code}, Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error discovering apps: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error discovering apps: {str(e)}")
            return None


# Create singleton instance
pipedream_auth_service = PipedreamAuthService() 