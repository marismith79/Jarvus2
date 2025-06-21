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
from ..utils.tool_permissions import check_tool_access, get_user_oauth_scopes
import logging
from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolMessage,
    ChatCompletions
)
from ..config import Config
from jarvus_app.models.history import History
from ..db import db

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
    import sys
    logger.info("=== Starting chat message handling ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request args: {dict(request.args)}")
    logger.info(f"Request form: {dict(request.form)}")
    logger.info(f"Request json: {request.get_json(silent=True)}")
    logger.info(f"Current user: {current_user.id}")
    logger.info(f"Session ID: {session.sid if hasattr(session, 'sid') else 'No session ID'}")

    # Log session size and key details
    session_total_size = 0
    logger.info("=== Session Key Size Debug ===")
    for k, v in session.items():
        try:
            if isinstance(v, (str, bytes)):
                size = len(v)
            else:
                import json
                size = len(json.dumps(v))
        except Exception as e:
            size = -1
        session_total_size += size if size > 0 else 0
        logger.info(f"Session key: {k} | type: {type(v).__name__} | size: {size} bytes")
    logger.info(f"Total session size (approx): {session_total_size} bytes")
    logger.info("====================================")
    
    # Use session.sid as the session_id
    session_id = getattr(session, 'sid', None)
    if not session_id:
        # Fallback: use _id if sid is not available
        session_id = session.get('_id')
    if not session_id:
        # Fallback: use user id (not ideal for multi-device)
        session_id = str(current_user.id)

    # POST: process new user message
    logger.info("Processing POST request - handling new message")
    data = request.get_json() or {}
    user_text = data.get('message', '')
    tool_choice = data.get('tool_choice', 'auto')
    jwt_token = session.get('jwt_token')
    
    logger.info(f"Received message: {user_text}")
    logger.info(f"Tool choice: {tool_choice}")
    logger.info(f"JWT token present: {bool(jwt_token)}")

    # Load or initialize conversation
    # history_obj = History.query.filter_by(session_id=session_id).first()
    # if history_obj and history_obj.messages:
    #     messages = [SystemMessage(content=Config.CHATBOT_SYSTEM_PROMPT)]
    #     for m in history_obj.messages:
    #         if m['role'] == 'user':
    #             messages.append(UserMessage(content=m['content']))
    #         elif m['role'] == 'assistant':
    #             messages.append(AssistantMessage(content=m['content']))
    #         elif m['role'] == 'tool':
    #             messages.append(ToolMessage(content=m['content'], tool_call_id=m.get('tool_call_id')))
    #     logger.info(f"Loaded existing conversation with {len(history_obj.messages)} messages from DB")
    # else:
        # logger.info("No existing conversation - initializing with system prompt")
    messages = [SystemMessage(content=Config.CHATBOT_SYSTEM_PROMPT)]

    # Append user message
    user_msg = UserMessage(content=user_text)
    messages.append(user_msg)
    logger.info("Added user message to conversation")

    # Prepare tool definitions - FILTER BASED ON USER SELECTION
    selected_tools = session.get('selected_tools', [])
    user_scopes = get_user_oauth_scopes(current_user.id, "google-workspace")

    if selected_tools:
        # Get tools only for selected services
        sdk_tools = tool_registry.get_sdk_tools_by_modules(selected_tools, user_scopes)
        logger.info(f"Loaded {len(sdk_tools)} tools for selected services: {selected_tools}")
    else:
        # If no services selected, send empty list
        sdk_tools = []
        logger.info("No services selected - sending empty tool list")

    try:
        # Recursive tool calling loop
        while True:
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
            logger.info(f"Assistant message: {assistant_msg}")

            # If no tool calls, we're done
            if not msg.tool_calls:
                logger.info("No tool calls in response - conversation complete")
                break

            # Handle function/tool calls if present
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

                # Append ToolMessage
                tool_msg = ToolMessage(
                    content=json.dumps(result),
                    tool_call_id=call.id,
                )
                messages.append(tool_msg)
                logger.info(f"Added tool result to conversation")

        # Save updated messages to DB
        history_data = [
            {
                "role": m.role, 
                "content": getattr(m, "content", ""), 
                **({"tool_call_id": m.tool_call_id} if hasattr(m, "tool_call_id") and m.tool_call_id else {})
            } 
            for m in messages
        ]
        
        # if history_obj:
        #     history_obj.messages = history_data
        # else:
        history_obj = History(session_id=session_id, messages=history_data)
        db.session.add(history_obj)
        db.session.commit()

        # Build minimal history for frontend
        filtered_history = [
            {"role": m.role, "content": getattr(m, "content", "")}
            for m in messages
            if m.role not in ['tool'] and getattr(m, "content", None)
        ]
        logger.info(f"Returning response with {len(filtered_history)} messages in history")
        logger.info(f"filtered_history: {filtered_history}")

        return jsonify(
            {
                "history": filtered_history,  # Return the complete history
            }
        )

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
