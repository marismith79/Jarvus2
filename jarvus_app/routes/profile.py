from flask import Blueprint, render_template, session, redirect, url_for
from flask_login import current_user, login_required
import logging

from ..utils.tool_permissions import get_connected_services
from ..utils.token_utils import get_valid_jwt_token

profile_bp = Blueprint("profile", __name__)
logger = logging.getLogger(__name__)


@profile_bp.route("/profile")
@login_required
def profile():
    jwt_token = get_valid_jwt_token()
    if not jwt_token:
        return redirect(url_for("auth.signin"))
    # Debug session state
    logger.info("=== Profile Route Session Debug ===")
    logger.info(f"Current user ID: {current_user.id}")
    logger.info(f"Session ID: {session.sid if hasattr(session, 'sid') else 'No session ID'}")
    logger.info(f"Session contents: {dict(session)}")
    logger.info(f"JWT Token in session: {jwt_token}")
    logger.info("=================================")

    # Get connected services using centralized function
    connected_services = get_connected_services(current_user.id)

    # Add all Google services for template context
    return render_template(
        "profile.html",
        user=current_user,
        docs_connected=connected_services.get("google_docs", False),
        notion_connected=connected_services.get("notion", False),
        slack_connected=connected_services.get("slack", False),
        zoom_connected=connected_services.get("zoom", False),
        gmail_connected=connected_services.get("gmail", False),
        drive_connected=connected_services.get("google_drive", False),
        sheets_connected=connected_services.get("google_sheets", False),
        slides_connected=connected_services.get("google_slides", False),
        calendar_connected=connected_services.get("google_calendar", False),
    )
