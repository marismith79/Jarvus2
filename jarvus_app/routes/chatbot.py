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
from ..services.agent_service import agent_service
from ..utils.token_utils import get_valid_jwt_token
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

    agent = agent_service.create_agent(current_user.id, agent_name, tools, description)
    return jsonify({
        'id': agent.id,
        'name': agent.name,
        'description': agent.description,
        'tools': agent.tools or []
    }), 201

@chatbot_bp.route('/agents/<int:agent_id>/history', methods=['GET'])
@login_required
def get_agent_history_route(agent_id):
    agent = agent_service.get_agent(agent_id, current_user.id)
    interaction_history = agent_service.get_agent_interaction_history(agent)
    return jsonify({'history': interaction_history})

@chatbot_bp.route('/send', methods=['POST'])
@login_required
def handle_chat_message():
    """Handle incoming chat messages with enhanced memory management and tool orchestration."""
    try:
        data = request.get_json() or {}
        user_text = data.get('message', '').strip()
        agent_id = data.get('agent_id')
        thread_id = data.get('thread_id')  # Optional thread ID for memory
        tool_choice = data.get('tool_choice', 'required')
        web_search_enabled = data.get('web_search_enabled', True)
        if not all([user_text, agent_id]):
            return jsonify({'error': 'Message and agent_id are required.'}), 400
        final_assistant_message, memory_info = agent_service.process_message(
            agent_id=agent_id,
            user_id=current_user.id,
            user_message=user_text,
            thread_id=thread_id,
            tool_choice=tool_choice,
            web_search_enabled=web_search_enabled,
            logger=logger
        )
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
        success = agent_service.delete_agent(agent_id, current_user.id)
        if success:
            return jsonify({'message': 'Agent deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete agent'}), 500
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@chatbot_bp.route('/agents/most-recent', methods=['GET'])
@login_required
def get_most_recent_agent():
    """Get the most recent agent for the current user."""
    try:
        # Get the most recent agent by creation date
        most_recent_agent = History.query.filter_by(user_id=current_user.id).order_by(History.created_at.desc()).first()
        
        if most_recent_agent:
            return jsonify({
                'id': most_recent_agent.id,
                'name': most_recent_agent.name,
                'description': most_recent_agent.description,
                'tools': most_recent_agent.tools or []
            }), 200
        else:
            return jsonify({'error': 'No agents found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting most recent agent: {str(e)}")
        return jsonify({'error': str(e)}), 500