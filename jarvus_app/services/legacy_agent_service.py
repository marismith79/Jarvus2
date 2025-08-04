from jarvus_app.models.history import History, InteractionHistory
from flask_login import current_user
from flask import abort
from ..db import db
import logging

logger = logging.getLogger(__name__)

# --- Legacy Agent Service Functions ---

def get_agent(agent_id, user_id):
    agent = History.query.filter_by(id=agent_id, user_id=user_id).first_or_404()
    # Refresh the specific object to ensure we have the latest data
    try:
        db.session.refresh(agent)
    except:
        # If refresh fails, the object might not be in the session, which is fine
        pass
    return agent

def get_agent_tools(agent):
    return agent.tools or []

def get_agent_history(agent):
    """Get the conversation history for an agent"""
    messages = []
    
    # logger.info(f"[DEBUG] get_agent_history called with agent.messages: {agent.messages}")
    
    # logger.info(f"[DEBUG] Total messages in agent: {len(messages)}")
    
    for msg in agent.messages:
        if msg.get('role') in ['user', 'assistant']:
            messages.append({
                'role': msg.get('role'),
                'content': msg.get('content', '')
            })
            # logger.info(f"[DEBUG] Added message: {msg.get('role')} - {msg.get('content', '')[:50]}...")
    
    filtered = [msg for msg in messages if msg.get('content', '').strip()]
    # logger.info(f"[DEBUG] get_agent_history filtered result: {filtered}")
    
    return filtered

def get_agent_interaction_history(agent):
    """Get only user input and final assistant responses for frontend display"""
    interactions = InteractionHistory.query.filter_by(
        history_id=agent.id, 
        user_id=agent.user_id
    ).order_by(InteractionHistory.created_at.asc()).all()
    
    history = []
    for interaction in interactions:
        history.append({
            'role': 'user',
            'content': interaction.user_message
        })
        history.append({
            'role': 'assistant', 
            'content': interaction.assistant_message
        })
    
    return history

def get_agent_full_history(agent):
    """Get full conversation history including tool messages for LLM processing"""
    return agent.messages or []

def append_message(agent, message):
    agent.messages.append(message)
    return agent

def save_interaction(agent, user_message, assistant_message):
    """Save a user-assistant interaction pair to InteractionHistory"""
    interaction = InteractionHistory(
        history_id=agent.id,
        user_id=agent.user_id,
        user_message=user_message,
        assistant_message=assistant_message
    )
    db.session.add(interaction)
    db.session.commit()
    return interaction

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

def delete_agent(agent_id, user_id):
    """Delete an agent and all its associated data from the database."""
    agent = get_agent(agent_id, user_id)  # This will 404 if agent doesn't exist or doesn't belong to user
    
    try:
        # Delete the agent
        db.session.delete(agent)
        db.session.commit()
        logger.info(f"Successfully deleted agent {agent_id} for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete agent {agent_id}: {str(e)}")
        return False 