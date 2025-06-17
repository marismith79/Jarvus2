"""
Chatbot routes for handling chat interactions.
"""

from flask import Blueprint, request, jsonify, session
from flask_login import login_required
from typing import Any, Dict, List, Optional
import json
import logging

from ..llm.client import JarvusAIClient
from ..services.tool_registry import tool_registry
from flask_login import login_required, current_user
from flask import Blueprint, jsonify, request, session
from ..utils.tool_permissions import check_tool_access
import logging
from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolMessage,
    ChatCompletions
)

SYSTEM_PROMPT = SystemMessage(content="You are a helpful assistant. Before you complete a tool call, say something to the user")
jarvus_ai = JarvusAIClient()

chatbot_bp = Blueprint('chatbot', __name__)
logger = logging.getLogger(__name__)
tool_choice = 'required'


@chatbot_bp.route('/tools', methods=['GET'])
@login_required
def get_available_tools():
    """Return only the definitions the user has toggled on."""
    # all of your definitions:
    all_defs = tool_registry.get_sdk_tools()

    # which names did the user pick?
    selected = session.get('selected_tools', [])
    if selected:
        # case‐insensitive match on the FunctionDefinition.name
        filtered = [
            d for d in all_defs
            if d.function.name.lower() in {s.lower() for s in selected}
        ]
    else:
        # nothing selected yet → show everybody
        filtered = ""

    # JSON‐serialize
    tools = [d.function.as_dict() for d in filtered]
    return jsonify(tools), 200

@chatbot_bp.route('/selected_tools', methods=['POST'])
@login_required
def save_selected_tools():
    data = request.get_json() or {}
    session['selected_tools'] = data.get('tools', [])
    return ('', 204)

@chatbot_bp.route('/send', methods=['GET', 'POST'])
@login_required
def handle_chat_message():
    """Handle incoming chat messages, invoking LLM and tools as needed."""
    
    logger.info("=== Starting chat message handling ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request args: {dict(request.args)}")
    logger.info(f"Request form: {dict(request.form)}")
    logger.info(f"Request json: {request.get_json(silent=True)}")
    logger.info(f"Current user: {current_user.id}")
    logger.info(f"Session ID: {session.sid if hasattr(session, 'sid') else 'No session ID'}")
    # logger.info(f"Session contents: {dict(session)}")
    
    # GET: return current conversation history
    if request.method == 'GET':
        logger.info("Processing GET request - returning conversation history")
        # def get_history():
        #     history = session.get('history', [])
        #     return jsonify(history), 200
        # logger.info(f"Returning history with {len(history)} messages")
        # return jsonify(history), 200
        history = session.get('history', [])
        logger.info(f"Returning history with {len(history)} messages")
        return jsonify(history), 200

    # POST: process new user message
    logger.info("Processing POST request - handling new message")
    data = request.get_json() or {}
    user_text = data.get('message', '')
    tool_choice = data.get('tool_choice')
    jwt_token = session.get('jwt_token')
    
    logger.info(f"Received message: {user_text}")
    logger.info(f"Tool choice: {tool_choice}")
    logger.info(f"JWT token present: {bool(jwt_token)}")

    # Load or initialize conversation
    messages = session.get('messages_objects')
    if not messages:
        logger.info("No existing conversation - initializing with system prompt")
        messages = [SYSTEM_PROMPT]
    else:
        logger.info(f"Loaded existing conversation with {len(messages)} messages")

    # Append user message
    user_msg = UserMessage(content=user_text)
    messages.append(user_msg)
    logger.info("Added user message to conversation")

    # Prepare tool definitions
    sdk_tools = tool_registry.get_sdk_tools()
    logger.info(f"Loaded {len(sdk_tools)} available tools")

    try:
        # Call Azure AI for completion (non-streaming)
        logger.info("Calling Azure AI for completion")
        response: ChatCompletions = jarvus_ai.client.complete(
            messages=messages,
            model=jarvus_ai.deployment_name,
            tools=sdk_tools,
            stream=False,
            tool_choice=tool_choice
        )
        logger.info("Received response from Azure AI")

        choice = response.choices[0]  # ChatChoice
        msg = choice.message           # ChatResponseMessage
        assistant_msg = AssistantMessage(
            content=msg.content,
            tool_calls=msg.tool_calls
            )
        messages.append(assistant_msg)
        logger.info(f"First message: {assistant_msg}")
        assistant_messages: List[Dict[str,str]] = []


        # Handle function/tool calls if present
        if msg.tool_calls:
            logger.info(f"Processing {len(msg.tool_calls)} tool calls")
            for call in msg.tool_calls:
                tool_name = call.function.name
                tool_args = json.loads(call.function.arguments) if call.function.arguments else {}
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                
                # Execute the tool
                result = tool_registry.execute_tool(
                    tool_name=tool_name,
                    parameters=tool_args,
                    jwt_token=jwt_token
                )
                # logger.info(f"Tool execution result: {result}")
                
                # Append ToolMessage
                tool_msg = ToolMessage(
                    content=json.dumps(result),
                    tool_call_id=call.id,
                )
                messages.append(tool_msg)

                # print("tool_msg:", tool_msg)
            # After executing tools, get a follow-up assistant response
            logger.info("Getting follow-up response after tool execution")
            followup: ChatCompletions = jarvus_ai.client.complete(
                messages=messages,
                model=jarvus_ai.deployment_name,
                tools=sdk_tools,
                stream=False,
                tool_choice=tool_choice
            )
            print("followup:", followup)
            choice2 = followup.choices[0]
            msg2 = choice2.message
            print("msg2:", msg2)
            assistant_msg = AssistantMessage(content=msg2.content)
            messages.append(assistant_msg)
            logger.info(f"Followup message: {assistant_msg}")
            assistant_messages.append({'role': assistant_msg.role, 'content': assistant_msg.content})
            final_reply = msg2.content
        else:
            # Plain text reply
            logger.info("Processing plain text reply")
            assistant_msg = AssistantMessage(content=msg.content)
            messages.append(assistant_msg)
            assistant_messages.append({'role': assistant_msg.role, 'content': assistant_msg.content})
            final_reply = msg.content

        # Persist conversation state
        session['history'] = [
            {"role": m.role, "content": getattr(m, "content", "")}
            for m in messages
        ]
        # Build minimal history for frontend
        # history = [ {'role': m.role, 'content': getattr(m, 'content', '')} for m in messages if hasattr(m, 'role') ]
        # Filter out tool messages before sending to frontend
        filtered_history = [
            {"role": m.role, "content": getattr(m, "content", "")}
            for m in messages
            if m.role not in ['tool']  # exclude tool messages
        ]
        logger.info(f"Returning response with {len(history)} messages in history")

        return jsonify({
            'assistant': final_reply,
            'history': filtered_history,
            'tool_responses': assistant_messages
        }), 200

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
