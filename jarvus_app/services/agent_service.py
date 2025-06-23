from jarvus_app.models.history import History
from flask_login import current_user
from flask import abort
from ..db import db

# --- Agent Service Functions ---

def get_agent(agent_id, user_id):
    return History.query.filter_by(id=agent_id, user_id=user_id).first_or_404()

def get_agent_tools(agent):
    return agent.tools or []

def get_agent_history(agent):
    return [msg for msg in agent.messages if msg.get('role') in ['user', 'assistant'] and msg.get('content')]

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