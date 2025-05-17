# app/routes/auth.py

import os
from flask import Blueprint, session, redirect, url_for, request, render_template
from dotenv import load_dotenv
import msal

load_dotenv()

auth = Blueprint("auth", __name__)

# Load B2C config from env
CLIENT_ID     = os.getenv("B2C_CLIENT_ID")
CLIENT_SECRET = os.getenv("B2C_CLIENT_SECRET")
SIGNIN_FLOW   = os.getenv("B2C_SIGNIN_FLOW")
REDIRECT_URI  = os.getenv("B2C_REDIRECT_URI")
SCOPE         = [ os.getenv("B2C_SCOPE") ]
TENANT_NAME   = os.getenv("B2C_TENANT_NAME")
TENANT_DOMAIN = os.getenv("B2C_TENANT_DOMAIN")
AUTHORITY     = f"https://{TENANT_NAME}.b2clogin.com/{TENANT_DOMAIN}/{SIGNIN_FLOW}"


print("→ AUTHORITY:", AUTHORITY)
print("→ REDIRECT_URI:", REDIRECT_URI)
print("→ SCOPE:", SCOPE)

@auth.route("/signin")
def signin():
    """Redirect to Azure B2C for authentication."""
    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )
    auth_url = msal_app.get_authorization_request_url(
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI
    )
    return redirect(auth_url)

@auth.route("/getAToken")
def authorized():
    """Callback endpoint for B2C to redirect back with code."""
    code = request.args.get("code")
    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )
    result = msal_app.acquire_token_by_authorization_code(
        code, scopes=SCOPE, redirect_uri=REDIRECT_URI
    )

    if "id_token_claims" in result:
        session["user"] = result["id_token_claims"]  # store the token claims
        return redirect(url_for("web.home"))

    # on error, show the sign‑in page with an error message
    error = result.get("error_description") or result.get("error")
    return render_template("signin.html", error=error)

@auth.route("/logout")
def logout():
    session.clear()

    post_logout = url_for("web.landing", _external=True)
    logout_url = (
        f"https://{TENANT_NAME}.b2clogin.com/{TENANT_DOMAIN}/{SIGNIN_FLOW}"
        "/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri={post_logout}"
    )
    return redirect(logout_url)

