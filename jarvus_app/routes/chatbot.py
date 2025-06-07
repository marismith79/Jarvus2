from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from ..services.mcp_service import mcp_service
from ..llm.client import OpenAIClient
import requests

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/')
def chat_page():
    """Render the chatbot interface."""
    user = session.get('user')
    if not user:
        return redirect(url_for('auth.signin'))
    return render_template('chatbot.html', user=user)

@chatbot_bp.route('/send', methods=['POST'])
def send_message():
    """Process a user message and return the response."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing message in request'
        }), 400
    
    # Fetch the user's available tools
    tools_response = requests.get('http://localhost:5001/api/get_user_tools')
    if tools_response.status_code != 200:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch user tools'
        }), 500
    tools = tools_response.json()
    
    # Use the LLM client to generate a response
    llm_client = OpenAIClient()
    messages = [
        llm_client.format_message("system", "You are a helpful assistant."),
        llm_client.format_message("user", data['message'])
    ]
    response = llm_client.create_chat_completion(messages, tools=tools)
    
    return jsonify({
        'success': True,
        'reply': response.choices[0].message.content
    }) 