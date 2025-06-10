# app/routes/auth.py

import os
from flask import Blueprint, session, redirect, url_for, request, render_template
from dotenv import load_dotenv
import msal
from flask_login import login_user, logout_user
from jarvus_app.models.user import User
from ..db import db

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

print("→ SIGNIN_AUTHORITY:", SIGNIN_AUTHORITY)
print("→ RESET_AUTHORITY:", RESET_AUTHORITY)
print("→ REDIRECT_URI:", REDIRECT_URI)
print("→ SCOPE:", SCOPE)

@auth.route("/signin")
def signin():
    """Redirect to Azure B2C for authentication."""
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
    return redirect(auth_url)

@auth.route("/getAToken")
def authorized():
    """Callback endpoint for B2C to redirect back with code."""
    error = request.args.get("error")
    error_description = request.args.get("error_description")

    # Handle "forgot password" error from B2C
    if error == "access_denied" and error_description and "AADB2C90118" in error_description:
        return redirect(url_for("auth.forgot_password"))

    code = request.args.get("code")
    if not code:
        # If user cancels or code is missing, redirect to sign-in page
        return redirect(url_for("auth.signin"))

    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=SIGNIN_AUTHORITY, client_credential=CLIENT_SECRET
    )
    result = msal_app.acquire_token_by_authorization_code(
        code, scopes=SCOPE, redirect_uri=REDIRECT_URI
    )

    if "id_token_claims" in result:
        claims = result["id_token_claims"]
        user_id = claims.get("sub")

        # # Find user in DB or create a new one
        # user = User.query.get(user_id)
        # if not user:
        #     # Get name and email from claims, with fallbacks
        #     name = claims.get("name") or claims.get("given_name") or "Unknown User"
        #     email = claims.get("preferred_username") or claims.get("email")
            
        #     # Only create user if we have an email
        #     if email:
        #         user = User(
        #             id=user_id,
        #             name=name,
        #             email=email
        #         )
        #         db.session.add(user)
        #         db.session.commit()
        #     else:
        #         # If no email is available, redirect to sign-in with error
        #         return render_template("signin.html", error="Required user information is missing. Please try signing in again.")

        # Store all user claims by user_id in the session for compatibility
        user_claims = session.get("user_claims", {})
        user_claims[user_id] = claims
        session["user_claims"] = user_claims

        login_user(user, remember=True)
        print("Session after login:", dict(session))
        next_url = session.pop('next_url', None)
        return redirect(next_url or url_for("web.landing"))

    # on error, show the sign‑in page with an error message
    error = result.get("error_description") or result.get("error")
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