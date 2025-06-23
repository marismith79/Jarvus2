"""
Chatbot routes for handling chat interactions.
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_login import login_required, current_user
from typing import Any, Dict, List, Optional
import time
import logging
import json

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
from ..services.agent_service import get_agent, get_agent_tools, get_agent_history, append_message, create_agent, delete_agent
from ..utils.token_utils import get_valid_jwt_token

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

@chatbot_bp.route('/agents', methods=['POST'])
@login_required
def create_agent_route():
    """Creates a new, named agent in the database."""
    data = request.get_json() or {}
    agent_name = data.get('name')
    tools = data.get('tools', [])
    description = data.get('description', '')

    agent = create_agent(current_user.id, agent_name, tools, description)
    return jsonify({
        'id': agent.id,
        'name': agent.name,
        'description': agent.description,
        'tools': agent.tools or []
    }), 201

@chatbot_bp.route('/agents/<int:agent_id>/history', methods=['GET'])
@login_required
def get_agent_history_route(agent_id):
    agent = get_agent(agent_id, current_user.id)
    filtered_history = get_agent_history(agent)
    return jsonify({'history': filtered_history})

@chatbot_bp.route('/send', methods=['POST'])
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

    data = request.get_json() or {}
    user_text = data.get('message', '')
    agent_id = data.get('agent_id')
    tool_choice = data.get('tool_choice', 'auto')
    jwt_token = get_valid_jwt_token()
    if not jwt_token:
        # Token refresh failed, force re-login
        return redirect(url_for("auth.signin"))
    logger.info(f"Received message: {user_text}")
    logger.info(f"Agent ID: {agent_id}")
    logger.info(f"Tool choice: {tool_choice}")
    logger.info(f"JWT token present: {bool(jwt_token)}")

    if not all([user_text, agent_id]):
        return jsonify({'error': 'Message and agent_id are required.'}), 400

    agent = get_agent(agent_id, current_user.id)
    messages = []
    for m in (agent.messages or []):
        role = m.get('role')
        if role == 'user':
            messages.append(UserMessage(content=m.get('content', '')))
        elif role == 'assistant':
            messages.append(AssistantMessage(content=m.get('content', ''), tool_calls=None))
        elif role == 'system':
            messages.append(SystemMessage(content=m.get('content', '')))
        else:
            messages.append(UserMessage(content=m.get('content', '')))
    messages.append(UserMessage(content=user_text))

    selected_tools = get_agent_tools(agent)
    user_scopes = get_user_oauth_scopes(current_user.id, "google-workspace")

    if selected_tools:
        sdk_tools = tool_registry.get_sdk_tools_by_modules(selected_tools, user_scopes)
        logger.info(f"Loaded {len(sdk_tools)} tools for agent {agent_id}: {selected_tools}")
    else:
        sdk_tools = []
        logger.info("No tools selected for agent - sending empty tool list")

    try:
        new_messages = []
        # Recursive tool calling loop
        while True:
            logger.info("Calling Azure AI for completion")
            response: ChatCompletions = jarvus_ai.client.complete(
                messages=messages,
                model=jarvus_ai.deployment_name,
                tools=sdk_tools,
                stream=False,
                tool_choice=tool_choice
            )
            logger.info("Received response from Azure AI")

            choice = response.choices[0]
            msg = choice.message
            # Always ensure content is a string
            assistant_msg = AssistantMessage(content=msg.content if msg.content is not None else "", tool_calls=msg.tool_calls)
            messages.append(assistant_msg)
            new_messages.append({'role': 'assistant', 'content': assistant_msg.content})
            logger.info(f"Assistant message: {assistant_msg}")
            if not msg.tool_calls:
                logger.info("No tool calls in response - conversation complete")
                break

            logger.info(f"Processing {len(msg.tool_calls)} tool calls")
            for call in msg.tool_calls:
                tool_name = call.function.name
                tool_args = json.loads(call.function.arguments) if call.function.arguments else {}
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                result = tool_registry.execute_tool(
                    tool_name=tool_name,
                    parameters=tool_args,
                    jwt_token=jwt_token
                )
                # ToolMessage must immediately follow the assistant message with tool_calls
                tool_msg = ToolMessage(content=json.dumps(result), tool_call_id=call.id)
                messages.append(tool_msg)
                logger.info(f"Added tool result to conversation")
        # Save updated messages to DB (as dicts)
        agent.messages = []
        for m in messages:
            if isinstance(m, UserMessage):
                agent.messages.append({'role': 'user', 'content': m.content})
            elif isinstance(m, AssistantMessage):
                agent.messages.append({'role': 'assistant', 'content': m.content})
            elif isinstance(m, SystemMessage):
                agent.messages.append({'role': 'system', 'content': m.content})
            else:
                agent.messages.append({'role': 'user', 'content': getattr(m, 'content', '')})
        db.session.commit()
        agent = get_agent(agent_id, current_user.id)  # Re-fetch from DB
        return jsonify({"new_messages": new_messages})

    except Exception as e:
        logger.error(f"Error processing message for agent {agent_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@chatbot_bp.route('/agents/<int:agent_id>', methods=['DELETE'])
@login_required
def delete_agent_route(agent_id):
    """Delete an agent and all its associated data."""
    try:
        success = delete_agent(agent_id, current_user.id)
        if success:
            return jsonify({'message': 'Agent deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete agent'}), 500
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
