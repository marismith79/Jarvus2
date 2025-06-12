from flask import Blueprint, request, jsonify
# from jarvus_app.middleware.validate_intent import is_valid_intent
# from jarvus_app.middleware.route_intent import dispatch_intent
from flask_login import current_user, login_required
from jarvus_app.models.user_tool import UserTool
from jarvus_app.models.user import User
from jarvus_app.db import db

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
    

# @api.route("/api/handle_intent", methods=["POST"])
# def handle_intent():
#     data = request.get_json()
    
#     if not data or not is_valid_intent(data):
#         return jsonify({"error": "Invalid or missing intent"}), 400

#     try:
#         response = dispatch_intent(data)
#         return jsonify({"result": response})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@api.route("/api/get_user_tools")
@login_required
def get_user_tools():
    """Return the list of tools the currently logged-in user is allowed to use."""
    user_tools = UserTool.query.filter_by(user_id=current_user.id, is_active=True).all()
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
        if 'name' in data:
            current_user.name = data['name']
        if 'email' in data:
            current_user.email = data['email']
        
        db.session.commit()
        return jsonify({"success": True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
