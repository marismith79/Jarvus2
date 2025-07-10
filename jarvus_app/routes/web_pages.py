# app/routes/web_pages.py
from datetime import datetime

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from sqlalchemy.exc import ProgrammingError

from ..utils.tool_permissions import get_connected_services
from .chatbot import handle_chat_message
from ..models.history import History

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

    return render_template(
        "chatbot.html",
        agents=agents,
        most_recent_agent=most_recent_agent,
        docs_connected=connected_services["google_docs"],
        sheets_connected=connected_services["google_sheets"],
        slides_connected=connected_services["google_slides"],
        drive_connected=connected_services["google_drive"],
        calendar_connected=connected_services["google_calendar"],
        gmail_connected=connected_services["gmail"],
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
