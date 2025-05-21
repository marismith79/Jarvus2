from flask import Blueprint, render_template, request, jsonify
from ..services.mcp_service import mcp_service

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/')
def chat_page():
    """Render the chatbot interface."""
    return render_template('chatbot.html')

@chatbot_bp.route('/send', methods=['POST'])
def send_message():
    """Process a user message and return the response."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing message in request'
        }), 400
    
    result = mcp_service.process_with_azure_openai(data['message'])
    return jsonify(result) 