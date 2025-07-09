# app/routes/auth.py

import os
import sys
import logging
import time

import msal
from dotenv import load_dotenv
from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_user, logout_user
from ..services.pipedream_auth_service import pipedream_auth_service
from ..services.pipedream_tool_registry import pipedream_tool_service
from jarvus_app.models.user import User

from ..db import db

load_dotenv()

auth = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)

# Load B2C config from env
CLIENT_ID = os.getenv("B2C_CLIENT_ID")
CLIENT_SECRET = os.getenv("B2C_CLIENT_SECRET")
SIGNIN_FLOW = os.getenv("B2C_SIGNIN_FLOW")
PASSWORDRESET_FLOW = os.getenv("B2C_PASSWORDRESET_FLOW")
REDIRECT_URI = os.getenv("B2C_REDIRECT_URI")
SCOPE = [os.getenv("B2C_SCOPE")]
TENANT_NAME = os.getenv("B2C_TENANT_NAME")
TENANT_DOMAIN = os.getenv("B2C_TENANT_DOMAIN")
SIGNIN_AUTHORITY = (
    f"https://{TENANT_NAME}.b2clogin.com/{TENANT_DOMAIN}/{SIGNIN_FLOW}"
)
RESET_AUTHORITY = (
    f"https://{TENANT_NAME}.b2clogin.com/{TENANT_DOMAIN}/{PASSWORDRESET_FLOW}"
)

print("DEBUG: Auth module initialized with config:", flush=True)
print(f"DEBUG: CLIENT_ID: {CLIENT_ID}", flush=True)
print(f"DEBUG: SIGNIN_AUTHORITY: {SIGNIN_AUTHORITY}", flush=True)
print(f"DEBUG: REDIRECT_URI: {REDIRECT_URI}", flush=True)
print(f"DEBUG: SCOPE: {SCOPE}", flush=True)


@auth.route("/signin")
def signin():
    """Redirect to Azure B2C for authentication."""
    print("DEBUG: Starting signin process", flush=True)
    next_url = request.args.get("next")
    if next_url:
        session["next_url"] = next_url
    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=SIGNIN_AUTHORITY, client_credential=CLIENT_SECRET
    )
    auth_url = msal_app.get_authorization_request_url(
        scopes=SCOPE, redirect_uri=REDIRECT_URI
    )
    print(f"DEBUG: Redirecting to auth URL: {auth_url}", flush=True)
    return redirect(auth_url)


@auth.route("/getAToken")
def authorized():
    """Callback endpoint for B2C to redirect back with code."""
    logger.info("=== Starting authorized callback ===")
    error = request.args.get("error")
    error_description = request.args.get("error_description")
    logger.info(f"Error params - error: {error}, description: {error_description}")

    # Handle "forgot password" error from B2C
    if (
        error == "access_denied"
        and error_description
        and "AADB2C90118" in error_description
    ):
        return redirect(url_for("auth.forgot_password"))

    code = request.args.get("code")
    logger.info(f"Received code: {code}")
    if not code:
        logger.info("No code received, redirecting to signin")
        return redirect(url_for("auth.signin"))

    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=SIGNIN_AUTHORITY, client_credential=CLIENT_SECRET
    )
    logger.info("Acquiring token with code")
    result = msal_app.acquire_token_by_authorization_code(
        code, scopes=SCOPE, redirect_uri=REDIRECT_URI
    )
    logger.info(f"Token acquisition result: {result}")

    if "id_token_claims" in result:
        claims = result["id_token_claims"]
        logger.info(f"Full result from Azure B2C: {result}")
        logger.info(f"Claims from Azure B2C: {claims}")
        user_id = claims.get("sub")
        logger.info(f"User ID (sub): {user_id}")

        if not user_id:
            logger.error("No user ID (sub) found in claims")
            return render_template(
                "signin.html",
                error="User ID not found in authentication response. Please try signing in again.",
            )

        # Find user in DB or create a new one
        user = User.query.get(user_id)
        logger.info(f"Existing user found: {user}")

        if not user:
            logger.info("No existing user found, creating new user")
            try:
                # Get email and name from claims if available
                email = claims.get("emails", [None])[0]  # Azure AD provides email in 'emails' array
                name = claims.get("name")  # Azure AD provides name in 'name' claim

                # If email is not available, generate a temporary one
                if not email:
                    email = f"user_{user_id}@temp.jarvus.com"

                # If name is not available, use a generated one
                if not name:
                    name = f"User_{user_id[:8]}"

                user = User(id=user_id, name=name, email=email)
                db.session.add(user)
                db.session.commit()
                logger.info(f"Created new user: {user.id}, {user.name}, {user.email}")
            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                db.session.rollback()
                return render_template(
                    "signin.html",
                    error="Error creating user account. Please try signing in again.",
                )

        # Store all user claims by user_id in the session for compatibility
        user_claims = session.get("user_claims", {})
        user_claims[user_id] = claims
        session["user_claims"] = user_claims

        # Store the JWT token, refresh token, and expiry in the session
        if "id_token" in result:
            session["jwt_token"] = result["id_token"]
            session["refresh_token"] = result.get("refresh_token")
            session["expires_at"] = result.get("expires_in")  # This is seconds from now
            # Convert expires_in to an absolute timestamp
            if result.get("expires_in"):
                session["expires_at"] = int(time.time()) + int(result["expires_in"])
            logger.info("=== Token Storage Debug ===")
            logger.info(f"Stored JWT token in session: {result['id_token'][:10]}...")
            logger.info(f"Stored refresh token in session: {str(result.get('refresh_token'))[:10]}...")
            logger.info(f"Stored expires_at in session: {session['expires_at']}")
            logger.info(f"Session contents after token storage: {dict(session)}")
            logger.info("=========================")
        else:
            logger.error("No id_token found in result")

        if user:
            login_user(user, remember=True)
            logger.info(f"User logged in successfully: {user.id}")
            
            # Trigger Pipedream token acquisition and tool discovery after successful authentication
            try:
                pipedream_token = pipedream_auth_service.get_access_token()
                if pipedream_token:
                    logger.info("Successfully acquired Pipedream token for user authentication")
                    
                    # Discover available tools for the user
                    try:
                        tools_registry = pipedream_tool_service.discover_all_tools(str(user_id))
                        if tools_registry and len(tools_registry._apps) > 0:
                            logger.info(f"Successfully discovered tools for {len(tools_registry._apps)} apps")
                        else:
                            logger.warning("No tools discovered, but token acquisition succeeded")
                    except Exception as tool_error:
                        logger.error(f"Error discovering tools during authentication: {str(tool_error)}")
                        # Don't fail the authentication if tool discovery fails
                else:
                    logger.warning("Failed to acquire Pipedream token, but user authentication succeeded")
            except Exception as e:
                logger.error(f"Error acquiring Pipedream token during authentication: {str(e)}")
                # Don't fail the authentication if Pipedream token acquisition fails
            
            next_url = session.pop("next_url", None)
            return redirect(next_url or url_for("web.landing"))
        else:
            logger.error("User object is None after creation/retrieval")
            return render_template(
                "signin.html",
                error="Failed to create or retrieve user account. Please try signing in again.",
            )

    # on error, show the sign‑in page with an error message
    error = result.get("error_description") or result.get("error")
    logger.error(f"Authentication error: {error}")
    return render_template("signin.html", error=error)


@auth.route("/logout")
def logout():
    # Clear Pipedream tokens before clearing session
    try:
        from ..services.pipedream_auth_service import pipedream_auth_service
        pipedream_auth_service.clear_session_tokens()
        logger.info("Cleared Pipedream tokens during logout")
    except Exception as e:
        logger.error(f"Error clearing Pipedream tokens during logout: {str(e)}")
    
    # Clear the session
    session.clear()

    # Log out from Flask-Login
    logout_user()

    post_logout = url_for("web.landing", _external=True)
    logout_url = (
        f"https://{TENANT_NAME}.b2clogin.com/{TENANT_DOMAIN}/{SIGNIN_FLOW}"
        "/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri={post_logout}"
    )
    return redirect(logout_url)


@auth.route("/forgot_password")
def forgot_password():
    """Redirect to Azure B2C for password reset."""
    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=RESET_AUTHORITY, client_credential=CLIENT_SECRET
    )
    auth_url = msal_app.get_authorization_request_url(
        scopes=SCOPE, redirect_uri=REDIRECT_URI
    )
    return redirect(auth_url)
