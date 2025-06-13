import json
import os

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from ..models.oauth import OAuthCredentials  # Uncommented

oauth_bp = Blueprint("oauth", __name__)

# Debug environment variables
print("\nDEBUG: Environment Variables:")
print(f"GOOGLE_REDIRECT_URI from env: {os.getenv('GOOGLE_REDIRECT_URI')}")
print(f"GOOGLE_CLIENT_ID from env: {os.getenv('GOOGLE_CLIENT_ID')}")

# OAuth 2.0 configuration
GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")],
        "scopes": [
            "https://www.googleapis.com/auth/gmail.readonly", # View your email messages and settings
            "https://www.googleapis.com/auth/gmail.compose", # Manage drafts and send emails
            "https://www.googleapis.com/auth/gmail.modify", # Read, compose and send emails from your Gmail account
            "https://www.googleapis.com/auth/spreadsheets", # See, edit, create and delete all your Google Sheets spreadsheets
            "https://www.googleapis.com/auth/presentations", # See, edit, create and delete all your Google Slides presentations
            "https://www.googleapis.com/auth/drive.install", # Connect itself to your Google Drive
            "https://www.googleapis.com/auth/activity", # View the activity history of your Google apps
            "https://www.googleapis.com/auth/docs", # See, edit, create and delete all of your Google Drive files
            "https://www.googleapis.com/auth/drive", # See, edit, create and delete all of your Google Drive files
            "https://www.googleapis.com/auth/documents", # See, edit, create and delete all your Google Docs documents
            "https://www.googleapis.com/auth/calendar", # See, edit, share and permanently delete all the calendars that you can access using Google Calendar
            "https://www.googleapis.com/auth/meetings.space.created", # Create, edit and see information about your Google Meet conferences created by the app.	
            "https://www.googleapis.com/meetings.space.settings", # Edit and see settings for all of your Google Meet calls. 
            "https://www.googleapis.com/auth/meetings.space.readonly", # Read information about any of your Google Meet conferences
            "https://www.googleapis.com/auth/meetings.space.created", # Create, edit and see information about your Google Meet conferences created by the app.	
            "https://www.googleapis.com/auth/meetings.space.readonly", # Read information about any of your Google Meet conferences
        ],
    }
}

# Print debug info about OAuth configuration
print("\nDEBUG: OAuth Configuration:")
print(f"DEBUG: GOOGLE_CLIENT_ID: {os.getenv('GOOGLE_CLIENT_ID')}")
print(f"DEBUG: GOOGLE_REDIRECT_URI: {os.getenv('GOOGLE_REDIRECT_URI')}")
print(
    f"DEBUG: Full GOOGLE_CLIENT_CONFIG: {json.dumps(GOOGLE_CLIENT_CONFIG, indent=2)}"
)

NOTION_CLIENT_CONFIG = {
    "client_id": os.getenv("NOTION_CLIENT_ID"),
    "client_secret": os.getenv("NOTION_CLIENT_SECRET"),
    "redirect_uri": os.getenv("NOTION_REDIRECT_URI"),
    "scopes": ["read_user", "write_user"],
}

SLACK_CLIENT_CONFIG = {
    "client_id": os.getenv("SLACK_CLIENT_ID"),
    "client_secret": os.getenv("SLACK_CLIENT_SECRET"),
    "redirect_uri": os.getenv("SLACK_REDIRECT_URI"),
    "scopes": ["chat:write", "channels:read", "groups:read"],
}

ZOOM_CLIENT_CONFIG = {
    "client_id": os.getenv("ZOOM_CLIENT_ID"),
    "client_secret": os.getenv("ZOOM_CLIENT_SECRET"),
    "redirect_uri": os.getenv("ZOOM_REDIRECT_URI"),
    "scopes": ["user:read", "meeting:write"],
}


@oauth_bp.route("/connect/<service>")
@login_required
def connect_service(service):
    """Initiate OAuth flow for the specified service"""
    if service == "google-workspace":
        return connect_google_workspace()
    elif service == "notion":
        return connect_notion()
    elif service == "slack":
        return connect_slack()
    elif service == "zoom":
        return connect_zoom()
    else:
        return redirect(url_for("web.profile"))


@oauth_bp.route("/disconnect/<service>", methods=["POST"])
@login_required
def disconnect_service(service):
    """Disconnect the specified service"""
    print(
        f"[DEBUG] Disconnect requested for service: {service}, user: {current_user.id}"
    )
    if service in ["google-workspace", "notion", "slack", "zoom"]:
        success = OAuthCredentials.remove_credentials(current_user.id, service)
        print(f"[DEBUG] Removal result for {service}: {success}")
        return jsonify({"success": success})
    print(f"[DEBUG] Invalid service disconnect attempted: {service}")
    return jsonify({"success": False, "error": "Invalid service"})


def connect_google_workspace():
    """Initiate Google Workspace OAuth flow"""
    print("\nDEBUG: Starting Google Workspace OAuth flow")
    redirect_uri = GOOGLE_CLIENT_CONFIG["web"]["redirect_uris"][0]
    print(f"DEBUG: Using redirect URI: {redirect_uri}")
    print(
        f"DEBUG: Full GOOGLE_CLIENT_CONFIG: {json.dumps(GOOGLE_CLIENT_CONFIG, indent=2)}"
    )

    flow = Flow.from_client_config(
        GOOGLE_CLIENT_CONFIG,
        scopes=GOOGLE_CLIENT_CONFIG["web"]["scopes"],
        redirect_uri=redirect_uri,
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )

    print(f"DEBUG: Generated authorization URL: {authorization_url}")
    session["oauth_state"] = state
    return redirect(authorization_url)


@oauth_bp.route("/oauth2callback")
@login_required
def oauth2callback():
    """Handle OAuth 2.0 callback"""
    print("\nDEBUG: Received OAuth callback")
    print(f"DEBUG: Callback URL: {request.url}")
    print(
        f"DEBUG: Expected redirect URI: {GOOGLE_CLIENT_CONFIG['web']['redirect_uris'][0]}"
    )

    try:
        flow = Flow.from_client_config(
            GOOGLE_CLIENT_CONFIG,
            scopes=GOOGLE_CLIENT_CONFIG["web"]["scopes"],
            redirect_uri=GOOGLE_CLIENT_CONFIG["web"]["redirect_uris"][0],
            state=session.get("oauth_state"),
        )

        print("DEBUG: Fetching token from callback")
        flow.fetch_token(
            authorization_response=request.url, include_granted_scopes="true"
        )

        credentials = flow.credentials
        print("DEBUG: Successfully obtained credentials")

        # Store credentials in database
        OAuthCredentials.store_credentials(
            current_user.id, "google-workspace", credentials.to_json()
        )
        print("DEBUG: Stored credentials in database")

        return redirect(url_for("web.profile"))
    except Exception as e:
        print(f"ERROR: Failed to process OAuth callback: {str(e)}")
        print(f"ERROR: Full error details: {repr(e)}")
        return redirect(url_for("web.profile"))


def connect_notion():
    """Initiate Notion OAuth flow"""
    auth_url = (
        f"https://api.notion.com/v1/oauth/authorize?"
        f"client_id={NOTION_CLIENT_CONFIG['client_id']}&"
        f"response_type=code&owner=user&"
        f"redirect_uri={NOTION_CLIENT_CONFIG['redirect_uri']}"
    )
    return redirect(auth_url)


def connect_slack():
    """Initiate Slack OAuth flow"""
    auth_url = (
        f"https://slack.com/oauth/v2/authorize?"
        f"client_id={SLACK_CLIENT_CONFIG['client_id']}&"
        f"scope={','.join(SLACK_CLIENT_CONFIG['scopes'])}&"
        f"redirect_uri={SLACK_CLIENT_CONFIG['redirect_uri']}"
    )
    return redirect(auth_url)


def connect_zoom():
    """Initiate Zoom OAuth flow"""
    auth_url = (
        f"https://zoom.us/oauth/authorize?"
        f"response_type=code&"
        f"client_id={ZOOM_CLIENT_CONFIG['client_id']}&"
        f"redirect_uri={ZOOM_CLIENT_CONFIG['redirect_uri']}&"
        f"scope={','.join(ZOOM_CLIENT_CONFIG['scopes'])}"
    )
    return redirect(auth_url)
