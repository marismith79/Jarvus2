# app/routes/web_pages.py
from datetime import datetime

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from sqlalchemy.exc import ProgrammingError

from ..models.oauth import OAuthCredentials
from .chatbot import handle_chat_message

web = Blueprint("web", __name__)


@web.route("/")
def landing():
    return render_template("landing.html")


@web.route("/profile")
@login_required
def profile():
    try:
        gmail_connected = (
            OAuthCredentials.get_credentials(current_user.id, "gmail")
            is not None
        )
        notion_connected = (
            OAuthCredentials.get_credentials(current_user.id, "notion")
            is not None
        )
        slack_connected = (
            OAuthCredentials.get_credentials(current_user.id, "slack")
            is not None
        )
        zoom_connected = (
            OAuthCredentials.get_credentials(current_user.id, "zoom")
            is not None
        )
    except ProgrammingError:
        # If the table doesn't exist yet, assume no services are connected
        gmail_connected = False
        notion_connected = False
        slack_connected = False
        zoom_connected = False

    return render_template(
        "profile.html",
        gmail_connected=gmail_connected,
        notion_connected=notion_connected,
        slack_connected=slack_connected,
        zoom_connected=zoom_connected,
    )


@web.route("/chatbot", strict_slashes=False)
@login_required
def chatbot():
    # Get connection status for each tool
    gmail_connected = (
        OAuthCredentials.get_credentials(current_user.id, "gmail") is not None
    )
    notion_connected = (
        OAuthCredentials.get_credentials(current_user.id, "notion") is not None
    )
    slack_connected = (
        OAuthCredentials.get_credentials(current_user.id, "slack") is not None
    )
    zoom_connected = (
        OAuthCredentials.get_credentials(current_user.id, "zoom") is not None
    )

    return render_template(
        "chatbot.html",
        gmail_connected=gmail_connected,
        notion_connected=notion_connected,
        slack_connected=slack_connected,
        zoom_connected=zoom_connected,
    )


@web.route("/chatbot/send", methods=["POST"])
@login_required
def send_chat_message():
    return handle_chat_message()


# @web.route("/flow-builder")
# @login_required
# def flow_builder():
#     return render_template("flow_builder.html")

# @web.route("/dashboard")
# @login_required
# def dashboard():
#     return render_template("dashboard.html")


@web.route("/privacy-policy")
def privacy_policy():
    """Render the privacy policy page"""
    return render_template(
        "privacy_policy.html",
        last_updated=datetime.now().strftime("%B %d, %Y"),
    )
