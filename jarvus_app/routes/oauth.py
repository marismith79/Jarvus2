from flask import Blueprint, redirect, request, url_for, current_app, session, jsonify
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from ..models.oauth import OAuthCredentials  # Uncommented
from flask_login import current_user, login_required
import json
import os

oauth_bp = Blueprint('oauth', __name__)

# Debug environment variables
print("\nDEBUG: Environment Variables:")
print(f"GOOGLE_REDIRECT_URI from env: {os.getenv('GOOGLE_REDIRECT_URI')}")
print(f"GOOGLE_CLIENT_ID from env: {os.getenv('GOOGLE_CLIENT_ID')}")

# OAuth 2.0 configuration
GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uri": os.getenv('GOOGLE_REDIRECT_URI'),
        "scopes": [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.modify"
        ]
    }
}

# Print debug info about OAuth configuration
print("\nDEBUG: OAuth Configuration:")
print(f"DEBUG: GOOGLE_CLIENT_ID: {os.getenv('GOOGLE_CLIENT_ID')}")
print(f"DEBUG: GOOGLE_REDIRECT_URI: {os.getenv('GOOGLE_REDIRECT_URI')}")
print(f"DEBUG: Full GOOGLE_CLIENT_CONFIG: {json.dumps(GOOGLE_CLIENT_CONFIG, indent=2)}")

NOTION_CLIENT_CONFIG = {
    "client_id": os.getenv('NOTION_CLIENT_ID'),
    "client_secret": os.getenv('NOTION_CLIENT_SECRET'),
    "redirect_uri": os.getenv('NOTION_REDIRECT_URI'),
    "scopes": ["read_user", "write_user"]
}

SLACK_CLIENT_CONFIG = {
    "client_id": os.getenv('SLACK_CLIENT_ID'),
    "client_secret": os.getenv('SLACK_CLIENT_SECRET'),
    "redirect_uri": os.getenv('SLACK_REDIRECT_URI'),
    "scopes": ["chat:write", "channels:read", "groups:read"]
}

ZOOM_CLIENT_CONFIG = {
    "client_id": os.getenv('ZOOM_CLIENT_ID'),
    "client_secret": os.getenv('ZOOM_CLIENT_SECRET'),
    "redirect_uri": os.getenv('ZOOM_REDIRECT_URI'),
    "scopes": ["user:read", "meeting:write"]
}

@oauth_bp.route('/connect/<service>')
@login_required
def connect_service(service):
    """Initiate OAuth flow for the specified service"""
    if service == 'gmail':
        return connect_gmail()
    elif service == 'notion':
        return connect_notion()
    elif service == 'slack':
        return connect_slack()
    elif service == 'zoom':
        return connect_zoom()
    else:
        return redirect(url_for('web.profile'))

@oauth_bp.route('/disconnect/<service>', methods=['POST'])
@login_required
def disconnect_service(service):
    """Disconnect the specified service"""
    if service in ['gmail', 'notion', 'slack', 'zoom']:
        success = OAuthCredentials.remove_credentials(current_user.id, service)
        return jsonify({'success': success})
    return jsonify({'success': False, 'error': 'Invalid service'})

def connect_gmail():
    """Initiate Gmail OAuth flow"""
    print("\nDEBUG: Starting Gmail OAuth flow")
    redirect_uri = GOOGLE_CLIENT_CONFIG['web']['redirect_uris'][0]
    print(f"DEBUG: Using redirect URI: {redirect_uri}")
    print(f"DEBUG: Full GOOGLE_CLIENT_CONFIG: {json.dumps(GOOGLE_CLIENT_CONFIG, indent=2)}")
    
    flow = Flow.from_client_config(
        GOOGLE_CLIENT_CONFIG,
        scopes=GOOGLE_CLIENT_CONFIG['web']['scopes'],
        redirect_uri=redirect_uri
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    print(f"DEBUG: Generated authorization URL: {authorization_url}")
    session['oauth_state'] = state
    return redirect(authorization_url)

@oauth_bp.route('/oauth2callback')
@login_required
def oauth2callback():
    """Handle OAuth 2.0 callback"""
    print("\nDEBUG: Received OAuth callback")
    print(f"DEBUG: Callback URL: {request.url}")
    print(f"DEBUG: Expected redirect URI: {GOOGLE_CLIENT_CONFIG['web']['redirect_uris'][0]}")
    
    try:
        flow = Flow.from_client_config(
            GOOGLE_CLIENT_CONFIG,
            scopes=GOOGLE_CLIENT_CONFIG['web']['scopes'],
            redirect_uri=GOOGLE_CLIENT_CONFIG['web']['redirect_uris'][0],
            state=session.get('oauth_state')
        )
        
        print("DEBUG: Fetching token from callback")
        flow.fetch_token(
            authorization_response=request.url,
            include_granted_scopes='true'
        )
        
        credentials = flow.credentials
        print("DEBUG: Successfully obtained credentials")
        
        # Store credentials in database
        OAuthCredentials.store_credentials(
            current_user.id,
            'gmail',
            credentials.to_json()
        )
        print("DEBUG: Stored credentials in database")
        
        return redirect(url_for('web.profile'))
    except Exception as e:
        print(f"ERROR: Failed to process OAuth callback: {str(e)}")
        print(f"ERROR: Full error details: {repr(e)}")
        return redirect(url_for('web.profile'))

def connect_notion():
    """Initiate Notion OAuth flow"""
    auth_url = f"https://api.notion.com/v1/oauth/authorize?client_id={NOTION_CLIENT_CONFIG['client_id']}&response_type=code&owner=user&redirect_uri={NOTION_CLIENT_CONFIG['redirect_uri']}"
    return redirect(auth_url)

def connect_slack():
    """Initiate Slack OAuth flow"""
    auth_url = f"https://slack.com/oauth/v2/authorize?client_id={SLACK_CLIENT_CONFIG['client_id']}&scope={','.join(SLACK_CLIENT_CONFIG['scopes'])}&redirect_uri={SLACK_CLIENT_CONFIG['redirect_uri']}"
    return redirect(auth_url)

def connect_zoom():
    """Initiate Zoom OAuth flow"""
    auth_url = f"https://zoom.us/oauth/authorize?response_type=code&client_id={ZOOM_CLIENT_CONFIG['client_id']}&redirect_uri={ZOOM_CLIENT_CONFIG['redirect_uri']}&scope={','.join(ZOOM_CLIENT_CONFIG['scopes'])}"
    return redirect(auth_url) 