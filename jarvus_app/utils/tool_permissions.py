"""
Utility functions for managing tool permissions.
"""

from datetime import datetime, timedelta

from ..models.oauth import OAuthCredentials
from ..models.tool_permission import ToolPermission

# Define available tools and their descriptions
TOOLS = {
    "google-workspace": "Access to Google Workspace functionality through MCP server",
    "notion": "Access to Notion functionality through MCP server",
    "slack": "Access to Slack functionality through MCP server",
    "zoom": "Access to Zoom functionality through MCP server",
    "web": "Access to web browsing functionality through a web browsing agent",
}

def grant_tool_access(user_id, tool_name, duration_days=None):
    """
    Grant access to a tool.

    Args:
        user_id (str): The user's ID
        tool_name (str): The name of the tool (e.g., 'google-workspace')
        duration_days (int, optional): Number of days until permission expires
    """
    if tool_name not in TOOLS:
        raise ValueError(
            f"Invalid tool name. Must be one of: {list(TOOLS.keys())}"
        )

    expires_at = None
    if duration_days:
        expires_at = datetime.utcnow() + timedelta(days=duration_days)

    permission = ToolPermission.grant_permission(
        user_id=user_id,
        tool_name=tool_name,
        permission_type="access",
        feature=tool_name,
        expires_at=expires_at,
    )
    return permission

def revoke_tool_access(user_id, tool_name):
    """
    Revoke access to a tool.

    Args:
        user_id (str): The user's ID
        tool_name (str): The name of the tool
    """
    if tool_name not in TOOLS:
        raise ValueError(
            f"Invalid tool name. Must be one of: {list(TOOLS.keys())}"
        )

    ToolPermission.revoke_permission(
        user_id=user_id,
        tool_name=tool_name,
        permission_type="access",
        feature=tool_name,
    )

def check_tool_access(user_id, tool_name):
    """
    Check if a user has access to a tool.

    Args:
        user_id (str): The user's ID
        tool_name (str): The name of the tool

    Returns:
        bool: True if the user has access
    """
    return ToolPermission.has_permission(
        user_id=user_id,
        tool_name=tool_name,
        permission_type="access",
        feature=tool_name,
    )

def get_user_tools(user_id):
    """
    Get all tools a user has access to.

    Args:
        user_id (str): The user's ID

    Returns:
        list: List of tool names the user has access to
    """
    permissions = ToolPermission.get_user_permissions(user_id)
    return [p.tool_name for p in permissions]

def get_connected_services(user_id):
    """Get a dictionary of connected services for a user."""
    services = {}
    for service in TOOLS.keys():
        if service == "google-workspace":
            # Check if user has OAuth credentials for this service
            creds = OAuthCredentials.get_credentials(user_id, service)
            
            # Debug: Print what we find
            print(f"DEBUG: Checking OAuth credentials for user {user_id}, service {service}")
            print(f"DEBUG: OAuth credentials found: {creds is not None}")
            
            # Consider connected if OAuth credentials exist
            services[service] = creds is not None
            print(f"DEBUG: Final result for {service}: {services[service]}")
        elif service == "web":
            # Web tools don't require OAuth - always available
            services[service] = True
        else:
            # Mark other services as not connected (coming soon)
            services[service] = False
    return services

def get_user_oauth_scopes(user_id: str, service: str) -> list:
    """Get the OAuth scopes granted by a user for a specific service."""
    creds = OAuthCredentials.get_credentials(user_id, service)
    if creds and creds.scopes:
        return creds.scopes.split(" ")
    return []
