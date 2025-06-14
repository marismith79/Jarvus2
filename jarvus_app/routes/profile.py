from flask import Blueprint, render_template
from flask_login import current_user, login_required

from ..utils.tool_permissions import get_connected_services

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def profile():
    # Get connected services using centralized function
    connected_services = get_connected_services(current_user.id)

    return render_template(
        "profile.html",
        user=current_user,
        gmail_connected=connected_services["gmail"],
        notion_connected=connected_services["notion"],
        slack_connected=connected_services["slack"],
        zoom_connected=connected_services["zoom"],
    )
