from jarvus_app.models.history import History
from flask_login import current_user
from flask import abort
from ..db import db
import logging

logger = logging.getLogger(__name__)

# --- Agent Service Functions ---

def get_agent(agent_id, user_id):
    return History.query.filter_by(id=agent_id, user_id=user_id).first_or_404()

def get_agent_tools(agent):
    return agent.tools or []

def get_agent_history(agent):
    logger.info(f"[DEBUG] get_agent_history called with agent.messages: {agent.messages}")
    filtered = [msg for msg in agent.messages if msg.get('role') in ['user', 'assistant'] and msg.get('content')]
    logger.info(f"[DEBUG] get_agent_history filtered result: {filtered}")
    return filtered

def get_agent_full_history(agent):
    """Get full conversation history including tool messages for LLM processing"""
    return agent.messages or []

def append_message(agent, message):
    agent.messages.append(message)
    return agent

def create_agent(user_id, name, tools=None, description=None):
    if not name:
        abort(400, 'Agent name is required.')
    new_agent = History(
        user_id=user_id,
        name=name,
        tools=tools or [],
        description=description or '',
        messages=[]
    )
    db.session.add(new_agent)
    db.session.commit()
    return new_agent 