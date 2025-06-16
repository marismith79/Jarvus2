"""
Chatbot routes for handling chat interactions.
"""

from flask import Blueprint, jsonify, request, Response, stream_with_context, session, current_app
from flask_login import login_required, current_user
from ..services.tool_registry import tool_registry
from ..services.mcp_client import mcp_client, ToolExecutionError
from ..utils.tool_permissions import check_tool_access
from ..llm.client import JarvusAIClient
import json
import logging

chatbot_bp = Blueprint('chatbot', __name__)
logger = logging.getLogger(__name__)

def handle_tool_execution(function_call, messages, jwt_token):
    """Handle a single tool execution and return the updated messages."""
    tool_name = function_call['name']
    try:
        tool_args = json.loads(function_call['arguments'])
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse tool arguments: {str(e)}"
        logger.error(f"JSON decode error: {str(e)}")
        return messages, error_msg

    try:
        logger.info("=== Tool Execution Debug ===")
        logger.info(f"Tool name: {tool_name}")
        logger.info(f"Tool arguments: {tool_args}")
        logger.info(f"JWT Token being passed: {jwt_token}")
        logger.info("=========================")
        
        result = tool_registry.execute_tool(
            tool_name=tool_name,
            parameters=tool_args,
            jwt_token=jwt_token
        )
        
        logger.info("=== Tool Result Debug ===")
        logger.info(f"Tool result type: {type(result)}")
        logger.info(f"Tool result content: {result}")
        
        # Step 1: Add the assistant message with tool_calls
        assistant_message = {
            "role": "assistant",
            "tool_calls": [{
                "id": function_call["id"],
                "function": {
                    "name": function_call["name"],
                    "arguments": function_call["arguments"]
                },
                "type": "function"
            }]
        }
        
        # Step 2: Add the tool response message
        tool_message = {
            "role": "tool",
            "tool_call_id": function_call["id"],
            "content": str(result)
        }
        
        messages.append(assistant_message)
        messages.append(tool_message)
        
        logger.info("=== Message Sequence Debug ===")
        logger.info(f"Assistant message: {assistant_message}")
        logger.info(f"Tool message: {tool_message}")
        logger.info("===========================")
        
        return messages, None
    except ToolExecutionError as e:
        error_msg = f"Error executing {tool_name}: {str(e)}"
        logger.error(f"Tool execution error: {str(e)}")
        return messages, error_msg

def stream_llm_response(messages, llm_client, available_tools, jwt_token, tool_choice):
    """Stream LLM responses without tool calls."""
    try:
        for chunk in llm_client.create_chat_completion(
            messages, 
            tools=available_tools, 
            jwt_token=jwt_token,
            tool_choice=tool_choice
        ):
            if isinstance(chunk, str):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            else:
                yield f"data: {json.dumps(chunk)}\n\n"
    except Exception as e:
        logger.error(f"LLM streaming error: {str(e)}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

def stream_tool_response(function_call, messages, llm_client, available_tools, jwt_token, tool_choice):
    """Stream responses for a tool call and its result."""
    try:
        messages, error = handle_tool_execution(function_call, messages, jwt_token)
        if error:
            yield f"data: {json.dumps({'error': error})}\n\n"
            return

        for response in llm_client.create_chat_completion(
            messages, 
            tools=available_tools, 
            jwt_token=jwt_token,
            tool_choice=tool_choice
        ):
            if isinstance(response, str):
                yield f"data: {json.dumps({'content': response})}\n\n"
            else:
                yield f"data: {json.dumps(response)}\n\n"
    except Exception as e:
        logger.error(f"Tool response streaming error: {str(e)}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@chatbot_bp.route('/tools', methods=['GET'])
@login_required
def get_available_tools():
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
    logger.info("=== Starting chat message handling ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Current user: {current_user.id}")
    logger.info(f"Session ID: {session.sid if hasattr(session, 'sid') else 'No session ID'}")
    logger.info(f"Session contents: {dict(session)}")
    
    message = request.args.get('message') if request.method == 'GET' else request.json.get('message')
    tool_choice = request.args.get('tool_choice') if request.method == 'GET' else (request.json.get('tool_choice') if request.json else None)
    selected_tool = request.args.get('tool') if request.method == 'GET' else (request.json.get('tool') if request.json else None)

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # Get available tools based on user permissions
        available_tools = [
            tool.openai_schema 
            for tool in tool_registry.get_active_tools() 
            if check_tool_access(current_user.id, tool.name)
        ]

        # If a specific tool is selected, filter available tools to only include that tool
        if selected_tool:
            available_tools = [
                tool for tool in available_tools 
                if tool["function"]["name"] == selected_tool
            ]
            if not available_tools:
                return jsonify({'error': f'Selected tool {selected_tool} is not available'}), 400

        jwt_token = session.get('jwt_token')
        logger.info("=== JWT Token Debug ===")
        logger.info(f"Current user ID: {current_user.id}")
        logger.info(f"JWT Token from session: {jwt_token}")
        logger.info(f"JWT Token type: {type(jwt_token)}")
        logger.info("=====================")

        if not jwt_token:
            logger.error("No JWT token found in session")
            return jsonify({'error': 'Authentication token not found. Please log in again.'}), 401

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

        # Set default tool_choice to 'required' if not specified or invalid
        if not tool_choice or tool_choice.lower() not in ['auto', 'required']:
            logger.info(f"Invalid or missing tool_choice '{tool_choice}', defaulting to 'required'")
            tool_choice = 'required'

        def generate():
            nonlocal messages
            try:
                for chunk in llm_client.create_chat_completion(
                    messages, 
                    tools=available_tools, 
                    jwt_token=jwt_token, 
                    tool_choice=tool_choice
                ):
                    logger.info(f"\n=== Chunk Debug ===")
                    logger.info(f"Chunk type: {type(chunk)}")
                    logger.info(f"Chunk content: {chunk}")
                    logger.info("=================\n")

                    # Handle tool calls
                    if isinstance(chunk, str):
                        try:
                            data = json.loads(chunk)
                            if "tool_call" in data:
                                # Execute the tool call
                                function_call = data["tool_call"]
                                messages, error = handle_tool_execution(function_call, messages, jwt_token)
                                if error:
                                    yield f"data: {json.dumps({'error': error})}\n\n"
                                    return
                                
                                # Get the model's response to the tool result
                                for response in llm_client.create_chat_completion(
                                    messages,
                                    tools=available_tools,
                                    jwt_token=jwt_token,
                                    tool_choice=tool_choice
                                ):
                                    if isinstance(response, str):
                                        yield f"data: {response}\n\n"
                            else:
                                # Regular content response
                                yield f"data: {chunk}\n\n"
                        except json.JSONDecodeError:
                            # If it's not JSON, treat it as regular content
                            yield f"data: {json.dumps({'content': chunk})}\n\n"
                    else:
                        yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                logger.error(f"Generate error: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                yield ""

        return Response(stream_with_context(generate()), mimetype='text/event-stream')

    except Exception as e:
        logger.error(f"Route error: {str(e)}")
        return jsonify({'error': str(e)}), 500
