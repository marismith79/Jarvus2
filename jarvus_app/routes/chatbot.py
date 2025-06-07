from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from ..services.mcp_service import mcp_service
from ..llm.client import OpenAIClient
from ..models.user_tool import UserTool

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/send', methods=['POST'])
@login_required
def handle_chat_message():
    """Process a user message and return the response."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing message in request'
        }), 400
    
    try:
        # Get the user's available tools directly from the database
        user_tools = UserTool.query.filter_by(user_id=current_user.id, is_active=True).all()
        tools = [tool.tool_name for tool in user_tools]
        
        # Use the LLM client to generate a response
        llm_client = OpenAIClient()
        messages = [
            llm_client.format_message("system", "You are a helpful assistant."),
            llm_client.format_message("user", data['message'])
        ]
        
        # Only pass tools if we have any
        response = llm_client.create_chat_completion(
            messages,
            tools=tools if tools else None
        )
        
        return jsonify({
            'success': True,
            'reply': response.choices[0].message.content
        })
    except Exception as e:
        print(f"Error in handle_chat_message: {str(e)}")  # Add logging
        return jsonify({
            'success': False,
            'error': f'Error processing message: {str(e)}'
        }), 500 