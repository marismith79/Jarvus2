from flask import Blueprint, redirect, request, url_for, current_app, session, jsonify
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from ..models.oauth import OAuthCredentials  # Uncommented
from flask_login import current_user, login_required
import json
import os

oauth_bp = Blueprint('oauth', __name__)

# OAuth 2.0 configuration
GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [os.getenv('GOOGLE_REDIRECT_URI')],
        "scopes": [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.modify"
        ]
    }
}

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
        return redirect(url_for('profile'))

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
    flow = Flow.from_client_config(
        GOOGLE_CLIENT_CONFIG,
        scopes=GOOGLE_CLIENT_CONFIG['web']['scopes'],
        redirect_uri=GOOGLE_CLIENT_CONFIG['web']['redirect_uris'][0]
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    session['oauth_state'] = state
    return redirect(authorization_url)

@oauth_bp.route('/oauth2callback')
@login_required
def oauth2callback():
    """Handle OAuth 2.0 callback"""
    flow = Flow.from_client_config(
        GOOGLE_CLIENT_CONFIG,
        scopes=GOOGLE_CLIENT_CONFIG['web']['scopes'],
        redirect_uri=GOOGLE_CLIENT_CONFIG['web']['redirect_uris'][0],
        state=session['oauth_state']
    )
    
    flow.fetch_token(
        authorization_response=request.url,
        include_granted_scopes='true'
    )
    
    credentials = flow.credentials
    # Store credentials in database
    OAuthCredentials.store_credentials(
        current_user.id,
        'gmail',
        credentials.to_json()
    )
    
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