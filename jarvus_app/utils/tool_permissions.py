"""
Utility functions for managing tool permissions.
"""

from datetime import datetime, timedelta

from ..models.tool_permission import ToolPermission

# Define available permission types
PERMISSION_TYPES = {
    "read": "Read-only access",
    "write": "Read and write access",
    "admin": "Full administrative access",
}

# Define available features for each tool
TOOL_FEATURES = {
    "gmail": {
        "list_messages": "List and read emails",
        "send_email": "Send new emails",
        "create_draft": "Create email drafts",
        "get_draft": "View email drafts",
        "send_draft": "Send email drafts",
        "get_message": "View specific emails",
        "modify_labels": "Modify email labels",
    },
    "calendar": {
        "events": "Access to calendar events",
        "calendars": "Access to calendar lists",
        "settings": "Access to calendar settings",
    },
}


def grant_tool_access(
    user_id, tool_name, features, permission_type="read", duration_days=None
):
    """
    Grant access to specific features of a tool.

    Args:
        user_id (str): The user's ID
        tool_name (str): The name of the tool (e.g., 'gmail', 'calendar')
        features (list): List of features to grant access to
        permission_type (str): Type of permission ('read', 'write', 'admin')
        duration_days (int, optional): Number of days until permission expires
    """
    if permission_type not in PERMISSION_TYPES:
        raise ValueError(
            f"Invalid permission type. Must be one of: {list(PERMISSION_TYPES.keys())}"
        )

    if tool_name not in TOOL_FEATURES:
        raise ValueError(
            f"Invalid tool name. Must be one of: {list(TOOL_FEATURES.keys())}"
        )

    expires_at = None
    if duration_days:
        expires_at = datetime.utcnow() + timedelta(days=duration_days)

    granted_permissions = []
    for feature in features:
        if feature not in TOOL_FEATURES[tool_name]:
            raise ValueError(
                f"Invalid feature '{feature}' for tool '{tool_name}'"
            )

        permission = ToolPermission.grant_permission(
            user_id=user_id,
            tool_name=tool_name,
            permission_type=permission_type,
            feature=feature,
            expires_at=expires_at,
        )
        granted_permissions.append(permission)

    return granted_permissions


def revoke_tool_access(user_id, tool_name, features=None):
    """
    Revoke access to specific features of a tool.

    Args:
        user_id (str): The user's ID
        tool_name (str): The name of the tool
        features (list, optional): List of features to revoke. If None, revokes all features.
    """
    if features is None:
        # Revoke all permissions for this tool
        permissions = ToolPermission.get_user_permissions(user_id, tool_name)
        for permission in permissions:
            ToolPermission.revoke_permission(
                user_id=user_id,
                tool_name=tool_name,
                permission_type=permission.permission_type,
                feature=permission.feature,
            )
    else:
        # Revoke specific features
        for feature in features:
            if feature not in TOOL_FEATURES[tool_name]:
                raise ValueError(
                    f"Invalid feature '{feature}' for tool '{tool_name}'"
                )

            # Revoke all permission types for this feature
            for permission_type in PERMISSION_TYPES:
                ToolPermission.revoke_permission(
                    user_id=user_id,
                    tool_name=tool_name,
                    permission_type=permission_type,
                    feature=feature,
                )


def check_tool_access(user_id, tool_name, feature, permission_type="read"):
    """
    Check if a user has access to a specific feature of a tool.

    Args:
        user_id (str): The user's ID
        tool_name (str): The name of the tool
        feature (str): The feature to check
        permission_type (str): The type of permission to check

    Returns:
        bool: True if the user has the requested permission
    """
    return ToolPermission.has_permission(
        user_id=user_id,
        tool_name=tool_name,
        permission_type=permission_type,
        feature=feature,
    )


def get_user_tool_permissions(user_id, tool_name=None):
    """
    Get all tool permissions for a user.

    Args:
        user_id (str): The user's ID
        tool_name (str, optional): Filter by specific tool

    Returns:
        list: List of ToolPermission objects
    """
    return ToolPermission.get_user_permissions(user_id, tool_name)
