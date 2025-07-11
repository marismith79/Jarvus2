from flask import Blueprint, render_template, session, redirect, url_for
from flask_login import current_user, login_required
import logging

from ..utils.tool_permissions import get_connected_services
from ..utils.token_utils import get_valid_jwt_token
from jarvus_app.config import ALL_PIPEDREAM_APPS

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

    # Build tool_list with a 'connected' property for each tool
    tool_list = []
    for app in ALL_PIPEDREAM_APPS:
        slug = app["slug"]
        tool = app.copy()
        tool["connected"] = connected_services.get(slug, False)
        tool_list.append(tool)
    return render_template(
        "profile.html",
        tool_list=tool_list,
        user=current_user
    )
