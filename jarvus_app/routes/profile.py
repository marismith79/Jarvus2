from flask import Blueprint, render_template, session
from flask_login import current_user, login_required
import logging

from ..utils.tool_permissions import get_connected_services

profile_bp = Blueprint("profile", __name__)
logger = logging.getLogger(__name__)


@profile_bp.route("/profile")
@login_required
def profile():
    # Debug session state
    logger.info("=== Profile Route Session Debug ===")
    logger.info(f"Current user ID: {current_user.id}")
    logger.info(f"Session ID: {session.sid if hasattr(session, 'sid') else 'No session ID'}")
    logger.info(f"Session contents: {dict(session)}")
    logger.info(f"JWT Token in session: {session.get('jwt_token')}")
    logger.info("=================================")

    # Get connected services using centralized function
    connected_services = get_connected_services(current_user.id)

    return render_template(
        "profile.html",
        user=current_user,
        google_workspace_connected=connected_services["google-workspace"],
        notion_connected=connected_services["notion"],
        slack_connected=connected_services["slack"],
        zoom_connected=connected_services["zoom"],
    )
