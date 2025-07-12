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
from jarvus_app.config import ALL_PIPEDREAM_APPS

SERVICES = [app["slug"] for app in ALL_PIPEDREAM_APPS]


oauth_bp = Blueprint("oauth", __name__)

# Create a session for connection reuse
oauth_session = requests.Session()
oauth_session.headers.update({
    'Accept': 'application/json',
    'User-Agent': 'Jarvus-App/1.0'
})

# Debug environment variables
# print("\nDEBUG: Environment Variables:")

def _handle_pipedream_response(response: requests.Response) -> dict:
    """Enhanced response handling for Pipedream API calls"""
    # print(f"Response status code: {response.status_code}")
    # print(f"Response headers: {dict(response.headers)}")
    
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
    if service in SERVICES:
        return connect_pipedream_service(service)
    else:
        return redirect(url_for("profile.profile"))


@oauth_bp.route("/disconnect/<service>", methods=["POST"])
@login_required
def disconnect_service(service):
    """Disconnect the specified service, including Pipedream API revocation"""
    from ..services.pipedream_auth_service import pipedream_auth_service
    # print(f"[DEBUG] Disconnect requested for service: {service}, user: {current_user.id}")
    if service in SERVICES:
        success = True
        error = None
        project_id = os.getenv("PIPEDREAM_PROJECT_ID")
        environment = os.getenv("PIPEDREAM_ENVIRONMENT", "development")
        access_token = pipedream_auth_service.get_token_from_session()
        user_id = current_user.id

        if project_id and access_token:
            # 1. List all accounts for this user and app
            list_url = f"https://api.pipedream.com/v1/connect/{project_id}/accounts?external_user_id={user_id}&app={service}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "X-PD-Environment": environment
            }
            try:
                resp = requests.get(list_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    accounts = resp.json().get("data", [])
                    if accounts:
                        account_id = accounts[0].get("id")
                        # 2. Delete the account by account_id
                        del_url = f"https://api.pipedream.com/v1/connect/{project_id}/accounts/{account_id}"
                        del_headers = {
                            "Authorization": f"Bearer {access_token}",
                            "X-PD-Environment": environment,
                            "Content-Type": "application/json"
                        }
                        del_resp = requests.delete(del_url, headers=del_headers)
                        # print(f"[DEBUG] Pipedream disconnect response: {del_resp.status_code} {del_resp.text}")
                        if del_resp.status_code != 204:
                            success = False
                            error = del_resp.text
                    else:
                        # print("[DEBUG] No connected account found for this app/user.")
                        success = False
                        error = "No connected account found for this app/user."
                else:
                    # print(f"[DEBUG] Failed to list accounts: {resp.status_code} {resp.text}")
                    success = False
                    error = resp.text
            except Exception as e:
                # print(f"[DEBUG] Exception during Pipedream disconnect: {e}")
                success = False
                error = str(e)
        else:
            # print(f"[DEBUG] Missing project_id or access_token for disconnect")
            success = False
            error = "Missing project_id or access_token"
        
        # Remove OAuth credentials from database (set status to NULL)
        creds_removed = OAuthCredentials.remove_credentials(current_user.id, service)
        # print(f"[DEBUG] OAuth credentials removal result for {service}: {creds_removed}")
        
        # Deactivate UserTool record
        try:
            from ..models.user_tool import UserTool
            user_tool = UserTool.query.filter_by(user_id=current_user.id, tool_name=service).first()
            if user_tool:
                user_tool.is_active = False
                db.session.commit()
                # print(f"[DEBUG] Deactivated UserTool for {service}")
        except Exception as e:
            # print(f"[DEBUG] Failed to deactivate UserTool: {e}")
            success = False
        
        # Revoke all tool permissions
        try:
            from ..models.tool_permission import ToolPermission
            permissions = ToolPermission.query.filter_by(user_id=current_user.id, tool_name=service).all()
            for permission in permissions:
                permission.is_granted = False
            db.session.commit()
            # print(f"[DEBUG] Revoked {len(permissions)} tool permissions for {service}")
        except Exception as e:
            # print(f"[DEBUG] Failed to revoke tool permissions: {e}")
            success = False
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": error or "Failed to disconnect"}), 400
    
    # print(f"[DEBUG] Invalid service disconnect attempted: {service}")
    return jsonify({"success": False, "error": "Invalid service"})


@oauth_bp.route("/pipedream/callback/<service>")
@login_required
def pipedream_callback(service):
    """Handle Pipedream OAuth callback after they complete the OAuth flow for any service"""
    # print(f"\nDEBUG: Received Pipedream callback for service: {service}")
    # print(f"DEBUG: Callback URL: {request.url}")
    # print(f"DEBUG: Current user: {getattr(current_user, 'id', None)}")
    # print(f"DEBUG: All query parameters: {dict(request.args)}")
    
    # Log all headers for debugging
    # print(f"DEBUG: All headers: {dict(request.headers)}")
    
    # Validate service
    if service not in SERVICES:
        # print(f"ERROR: Invalid service: {service}")
        return redirect(url_for("profile.profile"))
    
    # Check for errors
    error = request.args.get('error')
    if error:
        # print(f"ERROR: Pipedream returned error: {error}")
        return redirect(url_for("profile.profile"))
    

    # Get state from callback
    state = request.args.get('state')
    
    # print(f"DEBUG: Received state: {state}")
    # print(f"DEBUG: Expected state: {session.get('oauth_state')}")
    
    # Verify state parameter
    expected_state = session.get('oauth_state')
    if not expected_state or state != expected_state:
        # print("ERROR: State parameter mismatch")
        return redirect(url_for("profile.profile"))
    

    try:
        # Store the connection status in database (status=1 for connected)
        OAuthCredentials.store_credentials(
            current_user.id,
            service,
            state=state
        )
        # print(f"DEBUG: Stored connection status in database for {service}")
        
        # Grant tool permissions after successful OAuth
        try:
            grant_tool_access(
                user_id=current_user.id,
                tool_name=service
            )
            # print(f"DEBUG: Granted {service} tool permissions to user")
        except Exception as e:
            # print(f"ERROR: Failed to grant tool permissions: {e}")
            pass
        
        # Ensure UserTool record exists
        try:
            user_tool = UserTool.query.filter_by(user_id=current_user.id, tool_name=service).first()
            if not user_tool:
                user_tool = UserTool(user_id=current_user.id, tool_name=service, is_active=True)
                db.session.add(user_tool)
                db.session.commit()
                # print(f"DEBUG: Created UserTool for {service}")
            else:
                # print(f"DEBUG: UserTool for {service} already exists")
                pass
        except Exception as e:
            # print(f"ERROR: Failed to create UserTool: {e}")
            pass
        
        # Clear the state from session
        session.pop('oauth_state', None)
        
        return redirect(url_for("profile.profile"))
        
    except Exception as e:
        # print(f"ERROR: Failed to process Pipedream callback for {service}: {str(e)}")
        # print(f"ERROR: Full error details: {repr(e)}")
        return redirect(url_for("profile.profile"))

def connect_pipedream_service(service):
    """Initiate OAuth flow for any Pipedream service using Connect Link API with proper two-step authentication"""
    # print(f"\nDEBUG: Starting {service} OAuth flow via Pipedream Connect Link API")
    
    pipedream_api_client_id = os.getenv("PIPEDREAM_API_CLIENT_ID")
    pipedream_api_client_secret = os.getenv("PIPEDREAM_API_CLIENT_SECRET")
    pipedream_project_id = os.getenv("PIPEDREAM_PROJECT_ID")
    
    if not all([pipedream_api_client_id, pipedream_api_client_secret, pipedream_project_id]):
        # print("ERROR: Pipedream API credentials not configured")
        return redirect(url_for("profile.profile"))
    
    redirect_uri = os.getenv("PIPEDREAM_REDIRECT_URI")
    # print(f"DEBUG: This is the redirect URI: {redirect_uri}")
    if not redirect_uri:
        # print(f"ERROR: PIPEDREAM_REDIRECT_URI not configured")
        return redirect(url_for("profile.profile"))
    
    oauth_app_id_var = f"PIPEDREAM_{service.upper()}_APP_ID"
    oauth_app_id = os.getenv(oauth_app_id_var)
    if not oauth_app_id:
        # print(f"ERROR: {oauth_app_id_var} not configured for {service}")
        return redirect(url_for("profile.profile"))
    
    import secrets
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    
    environment = os.getenv("PIPEDREAM_ENVIRONMENT", "development")
    
    # print("DEBUG: PIPEDREAM_PROJECT_ID =", os.getenv("PIPEDREAM_PROJECT_ID"))
    # print("DEBUG: OAUTH_APP_ID =", os.getenv(f"PIPEDREAM_{service.upper()}_OAUTH_APP_ID"))
    
    try:
        # Step 1: Get Bearer token using client credentials
        # print("=== STEP 1: GETTING BEARER TOKEN ===")
        
        # Step 1: Get Bearer token
        token_data = {
            "grant_type": "client_credentials",
            "client_id": pipedream_api_client_id,
            "client_secret": pipedream_api_client_secret,
            "project_id": pipedream_project_id
        }
        
        # print("Token Request URL:", "https://api.pipedream.com/v1/oauth/token")
        # print("Token Request Payload:", json.dumps(token_data, indent=2))
        
        token_response = oauth_session.post(
            "https://api.pipedream.com/v1/oauth/token",
            headers={
                "X-PD-Environment": environment
            },
            data=token_data,
            timeout=30
        )
        
        # print("=== TOKEN RESPONSE ===")
        # print("Status:", token_response.status_code)
        # print("Headers:", dict(token_response.headers))
        # print("Body:", token_response.text)
        # print("===============================")
        
        token_info = _handle_pipedream_response(token_response)
        bearer_token = token_info.get("access_token")
        
        if not bearer_token:
            # print("ERROR: No access_token in token response!")
            return redirect(url_for("profile.profile"))
        
        # print("✅ Successfully obtained Bearer token!")
        
        # Step 2: Use Bearer token to create connect token
        # print("\n=== STEP 2: CREATING CONNECT TOKEN ===")
        
        external_user_id = str(current_user.id)
        # print(f"[OAUTH DEBUG] Sending external_user_id to Pipedream: {external_user_id}")
        # print(f"[OAUTH DEBUG] Current user ID: {current_user.id}")
        
        connect_token_data = {
            "external_user_id": external_user_id,
            "app": {
                "id": oauth_app_id,
                "name": service
            },
            "project_id": pipedream_project_id,
            "success_redirect_uri": f"{redirect_uri}/{service}?state={state}",
            "error_redirect_uri": f"{redirect_uri}/{service}?state={state}",
            "allowed_origins": ["http://localhost:5001"],
        }

        # print("Connect Token Request URL:", f"https://api.pipedream.com/v1/connect/{pipedream_project_id}/tokens")
        # print("Connect Token Request Payload:", json.dumps(connect_token_data, indent=2))

        response = oauth_session.post(
            f"https://api.pipedream.com/v1/connect/{pipedream_project_id}/tokens",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {bearer_token}",
                "X-PD-Environment": environment
            },
            json=connect_token_data,
            timeout=30
        )
        
        # print("=== CONNECT TOKEN RESPONSE ===")
        # print("Status:", response.status_code)
        # print("Headers:", dict(response.headers))
        # print("Body:", response.text)
        # print("===============================")
        
        connect_data = _handle_pipedream_response(response)
        connect_link_url = connect_data.get("connect_link_url")
        
        if not connect_link_url:
            # print("ERROR: No connect_link_url received from Pipedream")
            return redirect(url_for("profile.profile"))
        
        # Add app parameter to the connect_link_url
        separator = "&" if "?" in connect_link_url else "?"
        connect_link_url_with_app = f"{connect_link_url}{separator}app={service}"

        # print(f"DEBUG: Generated Pipedream connect link: {connect_link_url_with_app}")
        return redirect(connect_link_url_with_app)
        
    except Exception as e:
        # print(f"ERROR: Failed to create Pipedream connect token: {str(e)}")
        return redirect(url_for("profile.profile"))