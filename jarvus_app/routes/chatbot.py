from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from ..services.mcp_service import mcp_service
from ..models.oauth import OAuthCredentials
from flask_login import current_user, login_required

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/')
@login_required
def chat_page():
    """Render the chatbot interface."""
    # Check which services are connected
    gmail_connected = OAuthCredentials.get_credentials(current_user.id, 'gmail') is not None
    notion_connected = OAuthCredentials.get_credentials(current_user.id, 'notion') is not None
    slack_connected = OAuthCredentials.get_credentials(current_user.id, 'slack') is not None
    zoom_connected = OAuthCredentials.get_credentials(current_user.id, 'zoom') is not None
    
    return render_template('chatbot.html',
                         gmail_connected=gmail_connected,
                         notion_connected=notion_connected,
                         slack_connected=slack_connected,
                         zoom_connected=zoom_connected)

# @chatbot_bp.route('/send', methods=['POST'])
# def send_message():
#     """Process a user message and return the response."""
#     data = request.get_json()
#     if not data or 'message' not in data:
#         return jsonify({
#             'success': False,
#             'error': 'Missing message in request'
#         }), 400
    
#     result = mcp_service.process_with_azure_openai(data['message'])
#     return jsonify(result) 