"""Helper functions for generating scope descriptions."""

from typing import List

# Map of scope URLs to human-readable descriptions
SCOPE_DESCRIPTIONS = {
    # Gmail scopes
    "https://www.googleapis.com/auth/gmail.readonly": "read emails",
    "https://www.googleapis.com/auth/gmail.send": "send emails",
    "https://www.googleapis.com/auth/gmail.compose": "compose emails",
    "https://mail.google.com/": "full Gmail access",
    
    # Calendar scopes
    "https://www.googleapis.com/auth/calendar.readonly": "read calendar events",
    "https://www.googleapis.com/auth/calendar.events": "manage calendar events",
    "https://www.googleapis.com/auth/calendar": "full calendar access",
    
    # Drive scopes
    "https://www.googleapis.com/auth/drive.readonly": "read Drive files",
    "https://www.googleapis.com/auth/drive.file": "access files created by this app",
    "https://www.googleapis.com/auth/drive": "full Drive access",
    
    # Meet scopes
    "https://www.googleapis.com/auth/meetings.space.created": "create meeting spaces",
    "https://www.googleapis.com/auth/drive.meet.readonly": "access Meet recordings",
    
    # Docs, Sheets, Slides scopes
    "https://www.googleapis.com/auth/documents.readonly": "read Docs",
    "https://www.googleapis.com/auth/documents": "edit Docs",
    "https://www.googleapis.com/auth/spreadsheets.readonly": "read Sheets",
    "https://www.googleapis.com/auth/spreadsheets": "edit Sheets",
    "https://www.googleapis.com/auth/presentations.readonly": "read Slides",
    "https://www.googleapis.com/auth/presentations": "edit Slides",
}

def generate_scope_description(user_scopes: List[str], service_name: str) -> str:
    """
    Generate a human-readable description of the user's granted scopes for a service.
    
    Args:
        user_scopes: List of scope URLs granted by the user
        service_name: Name of the service (e.g., "Calendar", "Gmail", "Drive")
    
    Returns:
        A formatted string describing the granted permissions
    """
    if not user_scopes:
        return f"{service_name} Scopes: No permissions granted"
    
    # Filter scopes relevant to this service
    service_scopes = []
    for scope in user_scopes:
        if scope in SCOPE_DESCRIPTIONS:
            service_scopes.append(SCOPE_DESCRIPTIONS[scope])
    
    if not service_scopes:
        return f"{service_name} Scopes: No relevant permissions granted"
    
    # Create a readable description
    if len(service_scopes) == 1:
        return f"{service_name} Scopes: {service_scopes[0]}"
    else:
        return f"{service_name} Scopes: {', '.join(service_scopes)}" 