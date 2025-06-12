# app/routes/auth.py

import os
import sys
from flask import Blueprint, session, redirect, url_for, request, render_template
from dotenv import load_dotenv
import msal
from flask_login import login_user, logout_user
from jarvus_app.models.user import User
from ..db import db

# Force immediate log flushing
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

load_dotenv()

auth = Blueprint("auth", __name__)

# Load B2C config from env
CLIENT_ID     = os.getenv("B2C_CLIENT_ID")
CLIENT_SECRET = os.getenv("B2C_CLIENT_SECRET")
SIGNIN_FLOW   = os.getenv("B2C_SIGNIN_FLOW")
PASSWORDRESET_FLOW = os.getenv("B2C_PASSWORDRESET_FLOW")
REDIRECT_URI  = os.getenv("B2C_REDIRECT_URI")
SCOPE         = [ os.getenv("B2C_SCOPE") ]
TENANT_NAME   = os.getenv("B2C_TENANT_NAME")
TENANT_DOMAIN = os.getenv("B2C_TENANT_DOMAIN")
SIGNIN_AUTHORITY     = f"https://{TENANT_NAME}.b2clogin.com/{TENANT_DOMAIN}/{SIGNIN_FLOW}"
RESET_AUTHORITY = f"https://{TENANT_NAME}.b2clogin.com/{TENANT_DOMAIN}/{PASSWORDRESET_FLOW}"

print("DEBUG: Auth module initialized with config:", flush=True)
print(f"DEBUG: CLIENT_ID: {CLIENT_ID}", flush=True)
print(f"DEBUG: SIGNIN_AUTHORITY: {SIGNIN_AUTHORITY}", flush=True)
print(f"DEBUG: REDIRECT_URI: {REDIRECT_URI}", flush=True)
print(f"DEBUG: SCOPE: {SCOPE}", flush=True)

@auth.route("/signin")
def signin():
    """Redirect to Azure B2C for authentication."""
    print("DEBUG: Starting signin process", flush=True)
    next_url = request.args.get('next')
    if next_url:
        session['next_url'] = next_url
    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=SIGNIN_AUTHORITY, client_credential=CLIENT_SECRET
    )
    auth_url = msal_app.get_authorization_request_url(
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI
    )
    print(f"DEBUG: Redirecting to auth URL: {auth_url}", flush=True)
    return redirect(auth_url)

@auth.route("/getAToken")
def authorized():
    """Callback endpoint for B2C to redirect back with code."""
    print("DEBUG: Starting authorized callback", flush=True)
    error = request.args.get("error")
    error_description = request.args.get("error_description")
    print(f"DEBUG: Error params - error: {error}, description: {error_description}", flush=True)

    # Handle "forgot password" error from B2C
    if error == "access_denied" and error_description and "AADB2C90118" in error_description:
        return redirect(url_for("auth.forgot_password"))

    code = request.args.get("code")
    print(f"DEBUG: Received code: {code}", flush=True)
    if not code:
        print("DEBUG: No code received, redirecting to signin", flush=True)
        return redirect(url_for("auth.signin"))

    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=SIGNIN_AUTHORITY, client_credential=CLIENT_SECRET
    )
    print("DEBUG: Acquiring token with code", flush=True)
    result = msal_app.acquire_token_by_authorization_code(
        code, scopes=SCOPE, redirect_uri=REDIRECT_URI
    )
    print(f"DEBUG: Token acquisition result: {result}", flush=True)

    if "id_token_claims" in result:
        claims = result["id_token_claims"]
        print(f"DEBUG: Full result from Azure B2C: {result}", flush=True)
        print(f"DEBUG: Claims from Azure B2C: {claims}", flush=True)
        user_id = claims.get("sub")
        print(f"DEBUG: User ID (sub): {user_id}", flush=True)

        if not user_id:
            print("DEBUG: No user ID (sub) found in claims", flush=True)
            return render_template("signin.html", error="User ID not found in authentication response. Please try signing in again.")

        # Find user in DB or create a new one
        user = User.query.get(user_id)
        print(f"DEBUG: Existing user found: {user}", flush=True)
        
        if not user:
            print("DEBUG: No existing user found, creating new user", flush=True)
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
                
                user = User(
                    id=user_id,
                    name=name,
                    email=email
                )
                db.session.add(user)
                db.session.commit()
                print(f"DEBUG: Created new user: {user.id}, {user.name}, {user.email}", flush=True)
            except Exception as e:
                print(f"DEBUG: Error creating user: {str(e)}", flush=True)
                db.session.rollback()
                return render_template("signin.html", error="Error creating user account. Please try signing in again.")

        # Store all user claims by user_id in the session for compatibility
        user_claims = session.get("user_claims", {})
        user_claims[user_id] = claims
        session["user_claims"] = user_claims

        if user:
            login_user(user, remember=True)
            print(f"DEBUG: User logged in successfully: {user.id}", flush=True)
            next_url = session.pop('next_url', None)
            return redirect(next_url or url_for("web.landing"))
        else:
            print("DEBUG: User object is None after creation/retrieval", flush=True)
            return render_template("signin.html", error="Failed to create or retrieve user account. Please try signing in again.")

    # on error, show the sign‑in page with an error message
    error = result.get("error_description") or result.get("error")
    print(f"DEBUG: Authentication error: {error}", flush=True)
    return render_template("signin.html", error=error)

@auth.route("/logout")
def logout():
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
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI
    )
    return redirect(auth_url)