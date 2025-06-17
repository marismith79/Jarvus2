from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from jarvus_app.db import db
from jarvus_app.models.user import User
from jarvus_app.models.user_tool import UserTool

api = Blueprint("api", __name__)


@api.route("/api/signup", methods=["POST"])
def handle_signup():
    data = request.get_json()

    if not data or not data.get("email"):
        return jsonify({"error": "Email is required"}), 400

    email = data.get("email")

    # Simple email validation
    if "@" not in email or "." not in email:
        return jsonify({"error": "Invalid email format"}), 400


@api.route("/api/get_user_tools")
@login_required
def get_user_tools():
    """Return the list of tools the currently logged-in user is allowed to use."""
    user_tools = UserTool.query.filter_by(
        user_id=current_user.id, is_active=True
    ).all()
    tools = [tool.tool_name for tool in user_tools]
    return jsonify(tools)


@api.route("/api/update_profile", methods=["POST"])
@login_required
def update_profile():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    try:
        # Update user information
        if "name" in data:
            current_user.name = data["name"]
        if "email" in data:
            current_user.email = data["email"]

        db.session.commit()
        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/api/connect_tool", methods=["POST"])
@login_required
def connect_tool():
    data = request.get_json()
    if not data or "tool_name" not in data:
        return jsonify({"success": False, "error": "Missing tool_name"}), 400
    tool_name = data["tool_name"]
    tool = UserTool.query.filter_by(
        user_id=current_user.id, tool_name=tool_name
    ).first()
    if tool:
        tool.is_active = True
    else:
        tool = UserTool(
            user_id=current_user.id, tool_name=tool_name, is_active=True
        )
        db.session.add(tool)
    db.session.commit()
    return jsonify({"success": True, "tool_name": tool_name})
