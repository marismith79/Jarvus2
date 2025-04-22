from flask import Blueprint, request, jsonify
# from jarvus_app.middleware.validate_intent import is_valid_intent
# from jarvus_app.middleware.route_intent import dispatch_intent

api = Blueprint("api", __name__)

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
