from flask import Blueprint, request, jsonify
# from jarvus_app.middleware.validate_intent import is_valid_intent
# from jarvus_app.middleware.route_intent import dispatch_intent
from jarvus_app.models.email_signup import EmailSignup

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
    
    # Save the email
    success = EmailSignup.save_email(email)
    
    if success:
        return jsonify({"success": True, "message": "Email registered successfully"})
    else:
        return jsonify({"success": False, "message": "Email already registered"})

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
