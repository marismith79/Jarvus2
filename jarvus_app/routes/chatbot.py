"""
Chatbot routes for handling chat interactions.
"""

from flask import Blueprint, jsonify, request, Response, stream_with_context, session, current_app
from flask_login import login_required, current_user
from ..services.tool_registry import tool_registry
from ..services.mcp_client import mcp_client
from ..utils.tool_permissions import check_tool_access
from ..llm.client import JarvusAIClient
import json
import logging

chatbot_bp = Blueprint('chatbot', __name__)
logger = logging.getLogger(__name__)

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
    logger.info("=== Starting chat message handling ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Current user: {current_user.id}")
    logger.info(f"Session ID: {session.sid if hasattr(session, 'sid') else 'No session ID'}")
    logger.info(f"Session contents: {dict(session)}")
    
    message = request.args.get('message') if request.method == 'GET' else request.json.get('message')
    if not message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # Get available tools and their schemas
        available_tools = [
            tool.openai_schema 
            for tool in tool_registry.get_active_tools() 
            if check_tool_access(current_user.id, tool.name)
        ]

        # Get JWT token from session with error handling
        jwt_token = session.get('jwt_token')
        logger.info("=== JWT Token Debug ===")
        logger.info(f"Current user ID: {current_user.id}")
        logger.info(f"JWT Token from session: {jwt_token}")
        logger.info(f"JWT Token type: {type(jwt_token)}")
        logger.info("=====================")
        
        if not jwt_token:
            logger.error("No JWT token found in session")
            return jsonify({'error': 'Authentication token not found. Please log in again.'}), 401

        # Initialize LLM client and format messages
        llm_client = JarvusAIClient()
        messages = [
            llm_client.format_message("system", """You are a helpful AI assistant made for task automation.
            When using tools:
            1. Explain what you're doing before using a tool
            2. Make the tool call
            3. Explain the results to the user
            4. If there's an error, explain it and suggest alternatives"""),
            llm_client.format_message("user", message)
        ]

        def generate():
            try:
                for chunk in llm_client.create_chat_completion(messages, tools=available_tools, jwt_token=jwt_token):
                    # Handle both string and dictionary responses
                    if isinstance(chunk, dict) and chunk.get('tool_calls'):
                        # Handle tool execution
                        tool_call = chunk['tool_calls'][0]
                        tool_name = tool_call['function']['name']
                        try:
                            tool_args = json.loads(tool_call['function']['arguments'])
                        except json.JSONDecodeError as e:
                            error_msg = f"Failed to parse tool arguments: {str(e)}"
                            logger.error(f"JSON decode error: {str(e)}")
                            yield f"data: {json.dumps({'error': error_msg})}\n\n"
                            continue
                        
                        try:
                            logger.info("=== Tool Execution Debug ===")
                            logger.info(f"Tool name: {tool_name}")
                            logger.info(f"Tool arguments: {tool_args}")
                            logger.info(f"JWT Token being passed: {jwt_token}")
                            logger.info("=========================")
                            
                            # Execute tool and get result
                            result = tool_registry.execute_tool(
                                tool_name=tool_name,
                                parameters=tool_args.get('parameters', {}),
                                jwt_token=jwt_token
                            )
                            
                            # Add tool call and result to conversation
                            messages.extend([
                                {"role": "assistant", "content": None, "tool_calls": [tool_call]},
                                {"role": "tool", "tool_call_id": tool_call['id'], "content": json.dumps(result)}
                            ])
                            
                            # Get model's response to the result
                            for response in llm_client.create_chat_completion(messages, tools=available_tools, jwt_token=jwt_token):
                                if isinstance(response, str):
                                    yield f"data: {json.dumps({'content': response})}\n\n"
                                else:
                                    yield f"data: {json.dumps(response)}\n\n"
                                
                        except Exception as e:
                            error_msg = f"Error executing {tool_name}: {str(e)}"
                            logger.error(f"Tool execution error: {str(e)}")
                            yield f"data: {json.dumps({'error': error_msg})}\n\n"
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call['id'],
                                "content": error_msg
                            })
                    else:
                        # Handle regular message chunk (string or dict)
                        if isinstance(chunk, str):
                            yield f"data: {json.dumps({'content': chunk})}\n\n"
                        else:
                            yield f"data: {json.dumps(chunk)}\n\n"
                        
            except Exception as e:
                logger.error(f"Generate error: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream')

    except Exception as e:
        logger.error(f"Route error: {str(e)}")
        return jsonify({'error': str(e)}), 500
