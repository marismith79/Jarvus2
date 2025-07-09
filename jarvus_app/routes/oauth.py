import json
import os
import requests
from datetime import datetime

from flask import (
    Blueprint,
    jsonify,
    redirect,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required

from ..models.oauth import OAuthCredentials  # Uncommented
from ..utils.tool_permissions import grant_tool_access
from ..models.user_tool import UserTool
from ..db import db

GOOGLE_SERVICES = ['gmail', 'google_docs', 'google_sheets', 'google_slides', 'google_drive', 'google_calendar'];


oauth_bp = Blueprint("oauth", __name__)

# Create a session for connection reuse
oauth_session = requests.Session()
oauth_session.headers.update({
    'Accept': 'application/json',
    'User-Agent': 'Jarvus-App/1.0'
})

# Debug environment variables
print("\nDEBUG: Environment Variables:")

def _handle_pipedream_response(response: requests.Response) -> dict:
    """Enhanced response handling for Pipedream API calls"""
    print(f"Response status code: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 401:
        raise ValueError("Authentication failed - check API credentials")
    elif response.status_code == 403:
        raise ValueError("Permission denied - check project access")
    elif response.status_code == 429:
        raise ValueError("Rate limit exceeded - try again later")
    
    response.raise_for_status()
    
    content_type = response.headers.get('content-type', '')
    if 'application/json' in content_type:
        try:
            return response.json()
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response from Pipedream")
    else:
        return {"text": response.text, "status": response.status_code}


@oauth_bp.route("/connect/<service>")
@login_required
def connect_service(service):
    """Initiate OAuth flow for the specified service"""
    if service in GOOGLE_SERVICES:
        return connect_pipedream_service(service)
    else:
        return redirect(url_for("profile.profile"))


@oauth_bp.route("/disconnect/<service>", methods=["POST"])
@login_required
def disconnect_service(service):
    """Disconnect the specified service"""
    print(
        f"[DEBUG] Disconnect requested for service: {service}, user: {current_user.id}"
    )
    if service in GOOGLE_SERVICES:
        success = True
        
        # Remove OAuth credentials from database
        creds_removed = OAuthCredentials.remove_credentials(current_user.id, service)
        print(f"[DEBUG] OAuth credentials removal result for {service}: {creds_removed}")
        
        # Deactivate UserTool record
        try:
            from ..models.user_tool import UserTool
            user_tool = UserTool.query.filter_by(user_id=current_user.id, tool_name=service).first()
            if user_tool:
                user_tool.is_active = False
                db.session.commit()
                print(f"[DEBUG] Deactivated UserTool for {service}")
        except Exception as e:
            print(f"[DEBUG] Failed to deactivate UserTool: {e}")
            success = False
        
        # Revoke all tool permissions
        try:
            from ..models.tool_permission import ToolPermission
            permissions = ToolPermission.query.filter_by(user_id=current_user.id, tool_name=service).all()
            for permission in permissions:
                permission.is_granted = False
            db.session.commit()
            print(f"[DEBUG] Revoked {len(permissions)} tool permissions for {service}")
        except Exception as e:
            print(f"[DEBUG] Failed to revoke tool permissions: {e}")
            success = False
        
        return jsonify({"success": success})
    
    print(f"[DEBUG] Invalid service disconnect attempted: {service}")
    return jsonify({"success": False, "error": "Invalid service"})


@oauth_bp.route("/pipedream/callback/<service>")
@login_required
def pipedream_callback(service):
    """Handle Pipedream OAuth callback after they complete the OAuth flow for any service"""
    print(f"\nDEBUG: Received Pipedream callback for service: {service}")
    print(f"DEBUG: Callback URL: {request.url}")
    print(f"DEBUG: Current user: {getattr(current_user, 'id', None)}")
    print(f"DEBUG: All query parameters: {dict(request.args)}")
    
    # Log all headers for debugging
    print(f"DEBUG: All headers: {dict(request.headers)}")
    
    # Validate service
    if service not in GOOGLE_SERVICES:
        print(f"ERROR: Invalid service: {service}")
        return redirect(url_for("profile.profile"))
    
    # Check for errors
    error = request.args.get('error')
    if error:
        print(f"ERROR: Pipedream returned error: {error}")
        return redirect(url_for("profile.profile"))
    
    # Get connection_id and state from callback (Connect Link API uses connection_id)
    # Print all request arguments for debugging
    print(f"DEBUG: All request arguments: {dict(request.args)}")
    connection_id = (
        request.args.get('connection_id')
        or request.args.get("connect_session_id")
        or request.args.get("id")       
    )
    state = request.args.get('state')
    
    print(f"DEBUG: Received connection_id: {connection_id}")
    print(f"DEBUG: Received state: {state}")
    print(f"DEBUG: Expected state: {session.get('oauth_state')}")
    
    # Verify state parameter
    expected_state = session.get('oauth_state')
    if not expected_state or state != expected_state:
        print("ERROR: State parameter mismatch")
        return redirect(url_for("profile.profile"))
    
    if not connection_id:
        print("ERROR: No connection_id received from Pipedream")
        return redirect(url_for("profile.profile"))
    
    try:
        # Store the connection_id in database
        OAuthCredentials.store_credentials(
            current_user.id,
            service,
            connect_id=connection_id,  # Store as connect_id in our DB
            state=state
        )
        print(f"DEBUG: Stored connection_id in database for {service}")
        
        # Grant tool permissions after successful OAuth
        try:
            grant_tool_access(
                user_id=current_user.id,
                tool_name=service
            )
            print(f"DEBUG: Granted {service} tool permissions to user")
        except Exception as e:
            print(f"ERROR: Failed to grant tool permissions: {e}")
        
        # Ensure UserTool record exists
        try:
            user_tool = UserTool.query.filter_by(user_id=current_user.id, tool_name=service).first()
            if not user_tool:
                user_tool = UserTool(user_id=current_user.id, tool_name=service, is_active=True)
                db.session.add(user_tool)
                db.session.commit()
                print(f"DEBUG: Created UserTool for {service}")
            else:
                print(f"DEBUG: UserTool for {service} already exists")
        except Exception as e:
            print(f"ERROR: Failed to create UserTool: {e}")
        
        # Clear the state from session
        session.pop('oauth_state', None)
        
        return redirect(url_for("profile.profile"))
        
    except Exception as e:
        print(f"ERROR: Failed to process Pipedream callback for {service}: {str(e)}")
        print(f"ERROR: Full error details: {repr(e)}")
        return redirect(url_for("profile.profile"))

def connect_pipedream_service(service):
    """Initiate OAuth flow for any Pipedream service using Connect Link API with proper two-step authentication"""
    print(f"\nDEBUG: Starting {service} OAuth flow via Pipedream Connect Link API")
    
    pipedream_api_client_id = os.getenv("PIPEDREAM_API_CLIENT_ID")
    pipedream_api_client_secret = os.getenv("PIPEDREAM_API_CLIENT_SECRET")
    pipedream_project_id = os.getenv("PIPEDREAM_PROJECT_ID")
    
    if not all([pipedream_api_client_id, pipedream_api_client_secret, pipedream_project_id]):
        print("ERROR: Pipedream API credentials not configured")
        return redirect(url_for("profile.profile"))
    
    redirect_uri = os.getenv("PIPEDREAM_REDIRECT_URI")
    print(f"DEBUG: This is the redirect URI: {redirect_uri}")
    if not redirect_uri:
        print(f"ERROR: PIPEDREAM_REDIRECT_URI not configured")
        return redirect(url_for("profile.profile"))
    
    oauth_app_id_var = f"PIPEDREAM_{service.upper()}_APP_ID"
    oauth_app_id = os.getenv(oauth_app_id_var)
    if not oauth_app_id:
        print(f"ERROR: {oauth_app_id_var} not configured for {service}")
        return redirect(url_for("profile.profile"))
    
    import secrets
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    
    print("DEBUG: PIPEDREAM_PROJECT_ID =", os.getenv("PIPEDREAM_PROJECT_ID"))
    print("DEBUG: OAUTH_APP_ID =", os.getenv(f"PIPEDREAM_{service.upper()}_OAUTH_APP_ID"))
    
    try:
        # Step 1: Get Bearer token using client credentials
        print("=== STEP 1: GETTING BEARER TOKEN ===")
        
        # Step 1: Get Bearer token
        token_data = {
            "grant_type": "client_credentials",
            "client_id": pipedream_api_client_id,
            "client_secret": pipedream_api_client_secret,
            "project_id": pipedream_project_id
        }
        
        print("Token Request URL:", "https://api.pipedream.com/v1/oauth/token")
        print("Token Request Payload:", json.dumps(token_data, indent=2))
        
        token_response = oauth_session.post(
            "https://api.pipedream.com/v1/oauth/token",
            headers={
                "X-PD-Environment": "development"
            },
            data=token_data,
            timeout=30
        )
        
        print("=== TOKEN RESPONSE ===")
        print("Status:", token_response.status_code)
        print("Headers:", dict(token_response.headers))
        print("Body:", token_response.text)
        print("===============================")
        
        token_info = _handle_pipedream_response(token_response)
        bearer_token = token_info.get("access_token")
        
        if not bearer_token:
            print("ERROR: No access_token in token response!")
            return redirect(url_for("profile.profile"))
        
        print("✅ Successfully obtained Bearer token!")
        
        # Step 2: Use Bearer token to create connect token
        print("\n=== STEP 2: CREATING CONNECT TOKEN ===")
        
        connect_token_data = {
            # "external_user_id": str(current_user.id),
            "external_user_id": "b2c6c978-ce23-470e-aa97-f32e2cfb54e8",
            "app": {
                "id": oauth_app_id,
                "name": service
            },
            "project_id": pipedream_project_id,
            "success_redirect_uri": f"{redirect_uri}/{service}?state={state}",
            "error_redirect_uri": f"{redirect_uri}/{service}?state={state}",
            "allowed_origins": ["http://localhost:5001"],
        }

        print("Connect Token Request URL:", f"https://api.pipedream.com/v1/connect/{pipedream_project_id}/tokens")
        print("Connect Token Request Payload:", json.dumps(connect_token_data, indent=2))

        response = oauth_session.post(
            f"https://api.pipedream.com/v1/connect/{pipedream_project_id}/tokens",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {bearer_token}",
                "X-PD-Environment": "development"
            },
            json=connect_token_data,
            timeout=30
        )
        
        print("=== CONNECT TOKEN RESPONSE ===")
        print("Status:", response.status_code)
        print("Headers:", dict(response.headers))
        print("Body:", response.text)
        print("===============================")
        
        connect_data = _handle_pipedream_response(response)
        connect_link_url = connect_data.get("connect_link_url")
        
        if not connect_link_url:
            print("ERROR: No connect_link_url received from Pipedream")
            return redirect(url_for("profile.profile"))
        
        # Add app parameter to the connect_link_url
        separator = "&" if "?" in connect_link_url else "?"
        connect_link_url_with_app = f"{connect_link_url}{separator}app={service}"

        print(f"DEBUG: Generated Pipedream connect link: {connect_link_url_with_app}")
        return redirect(connect_link_url_with_app)
        
    except Exception as e:
        print(f"ERROR: Failed to create Pipedream connect token: {str(e)}")
        return redirect(url_for("profile.profile"))