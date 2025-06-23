import os
import time
from flask import session, redirect, url_for
import msal

CLIENT_ID = os.getenv("B2C_CLIENT_ID")
CLIENT_SECRET = os.getenv("B2C_CLIENT_SECRET")
TENANT_NAME = os.getenv("B2C_TENANT_NAME")
TENANT_DOMAIN = os.getenv("B2C_TENANT_DOMAIN")
SIGNIN_FLOW = os.getenv("B2C_SIGNIN_FLOW")
SIGNIN_AUTHORITY = f"https://{TENANT_NAME}.b2clogin.com/{TENANT_DOMAIN}/{SIGNIN_FLOW}"
SCOPE = [os.getenv("B2C_SCOPE")]


def get_valid_jwt_token():
    """
    Checks if the JWT token in the session is valid. If expired, attempts to refresh it.
    Returns a valid JWT token, or None if unable to refresh (user should re-login).
    """
    jwt_token = session.get("jwt_token")
    refresh_token = session.get("refresh_token")
    expires_at = session.get("expires_at")
    now = int(time.time())

    # If token is valid for at least 1 minute, return it
    if jwt_token and expires_at and int(expires_at) > now + 60:
        return jwt_token

    # Try to refresh if we have a refresh token
    if refresh_token:
        msal_app = msal.ConfidentialClientApplication(
            CLIENT_ID, authority=SIGNIN_AUTHORITY, client_credential=CLIENT_SECRET
        )
        try:
            result = msal_app.acquire_token_by_refresh_token(
                refresh_token, scopes=SCOPE
            )
            if "id_token" in result:
                session["jwt_token"] = result["id_token"]
                session["refresh_token"] = result.get("refresh_token", refresh_token)
                if result.get("expires_in"):
                    session["expires_at"] = int(time.time()) + int(result["expires_in"])
                else:
                    session["expires_at"] = None
                return session["jwt_token"]
            else:
                # Refresh failed, clear session tokens
                session.pop("jwt_token", None)
                session.pop("refresh_token", None)
                session.pop("expires_at", None)
                return None
        except Exception as e:
            # On any error, clear session tokens
            session.pop("jwt_token", None)
            session.pop("refresh_token", None)
            session.pop("expires_at", None)
            return None
    # No valid token and no refresh token
    return None
