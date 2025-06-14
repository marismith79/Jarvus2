"""
MCP Client for communicating with the Google Workspace MCP server.
Provides functions to call MCP endpoints for Gmail and Calendar tools.
"""

import os
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import RequestException

# Get MCP server URL from environment variable, default to localhost for development
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
print(f"\nMCP Server URL set to: {MCP_SERVER_URL}")


class MCPError(Exception):
    """Base exception for MCP client errors."""
    pass


class AuthenticationError(MCPError):
    """Raised when authentication fails."""
    pass


class PermissionError(MCPError):
    """Raised when user lacks required permissions."""
    pass


class RateLimitError(MCPError):
    """Raised when rate limit is exceeded."""
    pass


class MCPClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or MCP_SERVER_URL
        print(
            f"\nMCP Client initialized with URL: {self.base_url}"
        )  # Debug log

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle HTTP response and raise appropriate exceptions."""
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code == 403:
            raise PermissionError("Permission denied")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        response.raise_for_status()
        return response.json()

    def list_emails(
        self, max_results: int = 5, query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        print(
            f"\nCalling list_emails with max_results={max_results}, query={query}"
        )  # Debug log
        print(
            f"Making request to: {self.base_url}/gmail/list_emails"
        )  # Debug log
        payload = {"maxResults": max_results}
        if query:
            payload["query"] = query
        try:
            resp = requests.post(
                f"{self.base_url}/gmail/list_emails", json=payload
            )
            return self._handle_response(resp)
        except requests.exceptions.RequestException as e:
            print(f"\nError making request: {str(e)}")
            print(f"Request URL: {self.base_url}/gmail/list_emails")
            print(f"Request payload: {payload}")
            raise

    def search_emails(
        self, query: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        print(
            f"\nCalling search_emails with query={query}, max_results={max_results}"
        )  # Debug log
        print(
            f"Making request to: {self.base_url}/gmail/search_emails"
        )  # Debug log
        payload = {"query": query, "maxResults": max_results}
        try:
            resp = requests.post(
                f"{self.base_url}/gmail/search_emails", json=payload
            )
            return self._handle_response(resp)
        except requests.exceptions.RequestException as e:
            print(f"\nError making request: {str(e)}")
            print(f"Request URL: {self.base_url}/gmail/search_emails")
            print(f"Request payload: {payload}")
            raise

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {"to": to, "subject": subject, "body": body}
        if cc:
            payload["cc"] = cc
        if bcc:
            payload["bcc"] = bcc
        resp = requests.post(f"{self.base_url}/gmail/send_email", json=payload)
        return self._handle_response(resp)

    def list_events(
        self,
        max_results: int = 10,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        payload = {"maxResults": max_results}
        if time_min:
            payload["timeMin"] = time_min
        if time_max:
            payload["timeMax"] = time_max
        resp = requests.post(
            f"{self.base_url}/calendar/list_events", json=payload
        )
        return self._handle_response(resp)

    def create_event(
        self,
        summary: str,
        start: str,
        end: str,
        location: Optional[str] = None,
        description: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        payload = {"summary": summary, "start": start, "end": end}
        if location:
            payload["location"] = location
        if description:
            payload["description"] = description
        if attendees:
            payload["attendees"] = attendees
        resp = requests.post(
            f"{self.base_url}/calendar/create_event", json=payload
        )
        return self._handle_response(resp)


# Singleton instance
mcp_client = MCPClient()
