"""
Chatbot routes for handling chat interactions.
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_login import login_required, current_user
from typing import Any, Dict, List, Optional
import time
import logging
import json
import re

from ..llm.client import JarvusAIClient
from ..services.tool_registry import tool_registry
from flask_login import login_required, current_user
from flask import Blueprint, jsonify, request, session
from ..utils.tool_permissions import check_tool_access, get_user_tools
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
from ..services.agent_service import get_agent, get_agent_tools, get_agent_history, get_agent_interaction_history, append_message, create_agent, delete_agent, save_interaction
from ..services.enhanced_agent_service import enhanced_agent_service
from ..utils.token_utils import get_valid_jwt_token
from ..services.pipedream_auth_service import pipedream_auth_service
from ..services.pipedream_tool_registry import pipedream_tool_service


jarvus_ai = JarvusAIClient()

chatbot_bp = Blueprint('chatbot', __name__)
logger = logging.getLogger(__name__)
tool_choice = 'required'

@chatbot_bp.route('/tools', methods=['GET'])
@login_required
def get_available_tools():
    """Return only the definitions the user has toggled on."""
    # all of your definitions:
    all_defs = pipedream_tool_service.get_sdk_tools()

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
    interaction_history = get_agent_interaction_history(agent)
    return jsonify({'history': interaction_history})

@chatbot_bp.route('/send', methods=['POST'])
@login_required
def handle_chat_message():
    """Handle chat message (now always uses enhanced memory and tool orchestration)"""
    return handle_chat_message_enhanced()

def orchestrate_tool_calls(messages, allowed_tools, user_id, agent_id, tool_choice, web_search_enabled, pipedream_auth_service, logger, sdk_tools=None):
    """Orchestrate tool calling logic for both legacy and enhanced chat handlers."""
    new_messages = []
    if sdk_tools is None:
        sdk_tools = tool_registry.get_sdk_tools_by_modules(allowed_tools)
    try:
        while True:
            logger.info("Calling Azure AI for completion (orchestrate_tool_calls)")
            response: ChatCompletions = jarvus_ai.client.complete(
                messages=messages,
                model=jarvus_ai.deployment_name,
                tools=sdk_tools,
                stream=False,
                tool_choice=tool_choice
            )
            logger.info("Received response from Azure AI (orchestrate_tool_calls)")
            choice = response.choices[0]
            msg = choice.message
            assistant_msg = AssistantMessage(content=msg.content if msg.content is not None else "", tool_calls=msg.tool_calls)
            messages.append(assistant_msg)
            new_messages.append({'role': 'assistant', 'content': assistant_msg.content})
            if not msg.tool_calls:
                logger.info("No tool calls in response - conversation complete (orchestrate_tool_calls)")
                break
            logger.info(f"Processing {len(msg.tool_calls)} tool calls (orchestrate_tool_calls)")
            for call in msg.tool_calls:
                retries = 0
                max_retries = 3
                current_call = call
                while retries < max_retries:
                    tool_name = current_call.function.name
                    tool_args = json.loads(current_call.function.arguments) if current_call.function.arguments else {}
                    logger.info(f"Executing tool: {tool_name} with args: {tool_args} (orchestrate_tool_calls)")
                    try:
                        app_slug = "google_docs"  # TODO: Dynamically determine app_slug if needed
                        external_user_id = str(user_id)
                        tool_result = pipedream_auth_service.execute_tool(
                            external_user_id=external_user_id,
                            app_slug=app_slug,
                            tool_name=tool_name,
                            tool_args=tool_args
                        )
                        tool_msg = ToolMessage(content=json.dumps(tool_result), tool_call_id=current_call.id)
                        messages.append(tool_msg)
                        logger.info("Prompting LLM for final response after tool execution (orchestrate_tool_calls)")
                        response = jarvus_ai.client.complete(
                            messages=messages,
                            model=jarvus_ai.deployment_name,
                            stream=False,
                        )
                        choice = response.choices[0]
                        msg = choice.message
                        assistant_msg = AssistantMessage(content=msg.content if msg.content is not None else "", tool_calls=msg.tool_calls)
                        messages.append(assistant_msg)
                        new_messages.append({'role': 'assistant', 'content': assistant_msg.content})
                        break
                    except Exception as e:
                        error_msg = f"Tool call '{tool_name}' failed with error: {str(e)}"
                        logger.error(error_msg)
                        tool_msg = ToolMessage(content=json.dumps({"error": error_msg}), tool_call_id=current_call.id)
                        messages.append(tool_msg)
                        messages.append(UserMessage(content=f"{error_msg}. Please analyze the error and try a different tool or fix the arguments and call a tool again. Do not just suggest alternatives in text—actually call a tool."))
                        messages.append(SystemMessage(content="When you see an error message, you must analyze it and try a different tool or fix the arguments and call a tool again. Do not just suggest alternatives in text—actually call a tool."))
                        retries += 1
                        if retries >= max_retries:
                            logger.error(f"Max retries reached for tool call '{tool_name}'. Moving on. (orchestrate_tool_calls)")
                            break
                        logger.info("Prompting LLM again after tool call failure (orchestrate_tool_calls)")
                        response = jarvus_ai.client.complete(
                            messages=messages,
                            model=jarvus_ai.deployment_name,
                            tools=sdk_tools,
                            stream=False,
                            tool_choice="required"
                        )
                        logger.info("Received response from Azure AI (retry, orchestrate_tool_calls)")
                        choice = response.choices[0]
                        msg = choice.message
                        assistant_msg = AssistantMessage(content=msg.content if msg.content is not None else "", tool_calls=msg.tool_calls)
                        messages.append(assistant_msg)
                        new_messages.append({'role': 'assistant', 'content': assistant_msg.content})
                        logger.info(f"Assistant message (retry, orchestrate_tool_calls): {assistant_msg}")
                        if not msg.tool_calls:
                            logger.info("No tool calls in response after retry - conversation complete (orchestrate_tool_calls)")
                            break
                        current_call = msg.tool_calls[0]
        return new_messages, messages
    except Exception as e:
        logger.error(f"Error in orchestrate_tool_calls: {str(e)}", exc_info=True)
        raise

def handle_chat_message_enhanced():
    """Handle incoming chat messages with enhanced memory management and tool orchestration."""
    try:
        data = request.get_json() or {}
        user_text = data.get('message', '').strip()
        agent_id = data.get('agent_id')
        thread_id = data.get('thread_id')  # Optional thread ID for memory
        tool_choice = data.get('tool_choice', 'auto')
        web_search_enabled = data.get('web_search_enabled', True)
        if not all([user_text, agent_id]):
            return jsonify({'error': 'Message and agent_id are required.'}), 400
        # Prepare memory-augmented context and allowed tools
        # --- Begin replacement for prepare_message_with_memory ---
        agent = enhanced_agent_service.get_agent(agent_id, current_user.id)
        allowed_tools = set(enhanced_agent_service.get_agent_tools(agent))
        if web_search_enabled:
            allowed_tools.add('web')
        allowed_tools = list(allowed_tools)
        # Build messages with memory context
        # Use similar logic as process_message_with_memory, but do not call LLM yet
        from jarvus_app.services.memory_service import memory_service
        from datetime import datetime
        memory_context = memory_service.get_context_for_conversation(
            user_id=current_user.id,
            thread_id=thread_id,
            current_message=user_text
        )
        current_state = memory_service.get_latest_state(thread_id, current_user.id)
        if not current_state:
            current_state = {
                'messages': [],
                'agent_id': agent_id,
                'user_id': current_user.id,
                'thread_id': thread_id
            }
        current_state['messages'].append({
            'role': 'user',
            'content': user_text,
            'timestamp': datetime.utcnow().isoformat()
        })
        messages = []
        system_message = f"""You are a helpful AI assistant with access to user memories and conversation history.\n\n{memory_context if memory_context else 'No specific memories or context available.'}\n\nPlease be helpful, accurate, and remember important information about the user when appropriate."""
        messages.append({'role': 'system', 'content': system_message})
        conversation_messages = current_state['messages'][-10:]
        for msg in conversation_messages:
            if msg.get('content'):
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        memory_info = {
            'thread_id': thread_id,
            'memory_context_used': bool(memory_context)
        }
        # --- End replacement ---
        new_messages, updated_messages = orchestrate_tool_calls(
            messages=messages,
            allowed_tools=allowed_tools,
            user_id=current_user.id,
            agent_id=agent_id,
            tool_choice=tool_choice,
            web_search_enabled=web_search_enabled,
            pipedream_auth_service=pipedream_auth_service,
            logger=logger
        )
        final_assistant_message = ""
        if new_messages:
            for msg in reversed(new_messages):
                if msg.get('role') == 'assistant' and msg.get('content'):
                    final_assistant_message = msg.get('content')
                    break
        return jsonify({
            'response': final_assistant_message,
            'memory_info': memory_info,
            'thread_id': memory_info.get('thread_id')
        }), 200
    except Exception as e:
        logger.error(f"Error processing message with memory: {str(e)}", exc_info=True)
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