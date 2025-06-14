"""
Chatbot routes for handling chat interactions.
"""

from flask import Blueprint, jsonify, request, Response, stream_with_context
from flask_login import login_required, current_user
from ..services.tool_registry import tool_registry
from ..services.mcp_client import mcp_client
from ..utils.tool_permissions import check_tool_access
from ..llm.client import JarvusAIClient
import json

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/tools', methods=['GET'])
@login_required
def get_available_tools():
    """Get list of available tools for the chatbot."""
    tools = []
    for tool in tool_registry.get_active_tools():
        if check_tool_access(current_user.id, tool.name):
            tools.append({
                'name': tool.name,
                'description': tool.description,
                'category': tool.category.value
            })
    return jsonify(tools)

@chatbot_bp.route('/send', methods=['GET', 'POST'])
@login_required
def handle_chat_message():
    """Handle a chat message and return a response."""
    # Support both GET (for SSE) and POST methods
    message = request.args.get('message') if request.method == 'GET' else request.json.get('message')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # Get available tools and their schemas
        available_tools = []
        for tool in tool_registry.get_active_tools():
            if check_tool_access(current_user.id, tool.name):
                available_tools.append(tool.openai_schema)

        # Initialize LLM client
        llm_client = JarvusAIClient()
        
        # Format system message with available tools
        system_message = f"""You are a helpful AI assistant made for task automation.
        When interacting with users:
        1. Be concise and clear in your responses
        2. Use the available tools when appropriate
        3. If you need to use a tool, explain what you're going to do first
        4. If you can't help with something, be honest about it

        Available tools:
        {json.dumps(available_tools, indent=2)}

        When using tools:
        1. Explain what you're doing before using a tool
        2. Format tool results in a clear, readable way
        3. Provide context and insights about the results
        4. Handle errors gracefully and inform the user if something goes wrong"""

        # Format messages for the LLM
        messages = [
            llm_client.format_message("system", system_message),
            llm_client.format_message("user", message)
        ]

        def generate():
            try:
                for chunk in llm_client.create_chat_completion(
                    messages, tools=available_tools
                ):
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
            except Exception as e:
                print(f"Error in generate: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        print(f"Error in handle_chat_message: {str(e)}")
        return jsonify({'error': str(e)}), 500
