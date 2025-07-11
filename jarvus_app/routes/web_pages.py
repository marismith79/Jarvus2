# app/routes/web_pages.py
from datetime import datetime

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from sqlalchemy.exc import ProgrammingError

from ..utils.tool_permissions import get_connected_services
from .chatbot import handle_chat_message
from ..models.history import History
from jarvus_app.config import ALL_PIPEDREAM_APPS

web = Blueprint("web", __name__)


@web.route("/")
def landing():
    return render_template("landing.html")


@web.route("/control-bar")
def control_bar():
    """Serve the control bar interface for the Electron desktop app"""
    return render_template("control-bar.html")


@web.route("/chatbot", strict_slashes=False)
@login_required
def chatbot():
    # Get connection status for each tool using centralized function
    connected_services = get_connected_services(current_user.id)
    
    # Add these lines to fetch the agents
    agents = History.query.filter_by(user_id=current_user.id).order_by(History.created_at.desc()).all()
    most_recent_agent = agents[0] if agents else None

    # Build tool_list with a 'connected' property for each tool
    tool_list = []
    for app in ALL_PIPEDREAM_APPS:
        slug = app["slug"]
        tool = app.copy()
        tool["connected"] = connected_services.get(slug, False)
        tool_list.append(tool)
    tool_slugs = [tool["slug"] for tool in tool_list]
    return render_template(
        "chatbot.html",
        tool_list=tool_list,
        tool_slugs=tool_slugs,
        agents=agents,
        most_recent_agent=most_recent_agent
    )

@web.route("/chatbot/send", methods=["POST"])
@login_required
def send_chat_message():
    return handle_chat_message()

@web.route("/privacy-policy")
def privacy_policy():
    """Render the privacy policy page"""
    return render_template(
        "privacy_policy.html",
        last_updated=datetime.now().strftime("%B %d, %Y"),
    )
