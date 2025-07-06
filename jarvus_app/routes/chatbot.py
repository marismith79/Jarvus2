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
from ..utils.tool_permissions import check_tool_access, get_user_oauth_scopes, get_user_tools
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
    history = get_agent_history(agent)
    return jsonify({'history': history})

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
    web_search_enabled = data.get('web_search_enabled', True)
    
    # Force tool choice to 'required' if browser tools are available and user is asking for web actions
    user_text_lower = user_text.lower()
    browser_keywords = ['go to', 'open', 'navigate', 'visit', 'browser', 'website', 'click', 'type', 'fill']
    if any(keyword in user_text_lower for keyword in browser_keywords):
        tool_choice = 'required'
        logger.info(f"🔧 Forcing tool_choice to 'required' due to browser-related request")
    jwt_token = get_valid_jwt_token()
    if not jwt_token:
        # Token refresh failed, check if this is a desktop app request
        user_agent = request.headers.get('User-Agent', '')
        if 'jarvus-desktop' in user_agent:
            # Desktop app - return JSON error
            return jsonify({'error': 'Authentication required', 'auth_required': True}), 401
        else:
            # Web app - redirect to signin
            return redirect(url_for("auth.signin"))
    logger.info(f"Received message: {user_text}")
    logger.info(f"Agent ID: {agent_id}")
    logger.info(f"Tool choice: {tool_choice}")
    logger.info(f"JWT token present: {bool(jwt_token)}")

    if not all([user_text, agent_id]):
        return jsonify({'error': 'Message and agent_id are required.'}), 400

    agent = get_agent(agent_id, current_user.id)
    messages = []
    
    # Add the main system prompt first
    system_prompt = Config.CHATBOT_SYSTEM_PROMPT
    logger.info(f"🔍 SYSTEM PROMPT LENGTH: {len(system_prompt)} characters")
    logger.info(f"🔍 SYSTEM PROMPT CONTAINS 'browser': {'browser' in system_prompt.lower()}")
    logger.info(f"🔍 SYSTEM PROMPT CONTAINS 'open_website': {'open_website' in system_prompt.lower()}")
    messages.append(SystemMessage(content=system_prompt))
    
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

    # Helper: map user_scopes to tool module names
    def scopes_to_tools(user_scopes):
        SCOPE_KEYWORDS = {
            'gmail': ['gmail'],
            'calendar': ['calendar'],
            'drive': ['drive'],
            'docs': ['documents'],
            'sheets': ['spreadsheets'],
            'slides': ['presentations'],
        }
        tool_set = set()
        for tool, keywords in SCOPE_KEYWORDS.items():
            for keyword in keywords:
                if any(keyword in scope for scope in user_scopes):
                    tool_set.add(tool)
        return tool_set

    agent_tools = set(get_agent_tools(agent))
    user_scopes = get_user_oauth_scopes(current_user.id, "google-workspace")
    user_tools = scopes_to_tools(user_scopes)
    allowed_tools = list(agent_tools & user_tools)
    if web_search_enabled:
        allowed_tools.append('web')
        allowed_tools.append('browser')
    print('DEBUG agent_tools', agent_tools)
    print('DEBUG user_tools', user_tools)
    print('DEBUG allowed_tools', allowed_tools)
    print('DEBUG user_scopes', user_scopes)

    # # Get tool categories for allowed tools
    # allowed_tool_objs = [tool_registry.get_tool(t) for t in allowed_tools if tool_registry.get_tool(t)]
    # allowed_categories = list(set([t.category.value for t in allowed_tool_objs if t and hasattr(t, 'category')]))
    # print('DEBUG allowed_tool_objs', allowed_tool_objs)
    # print('DEBUG allowed_categories', allowed_categories)

    # Step 1: Ask LLM which tool/category is needed
    tool_selection_prompt = (
        "Given the following user message and these tool categories, "
        "which tool(s) or tool category(ies) would you use to answer the message? "
        "Respond with a JSON list of tool names or categories. If none, return an empty list."
    )
    tool_selection_messages = [
        {"role": "system", "content": tool_selection_prompt},
        {"role": "user", "content": user_text},
        {"role": "system", "content": f"Available tool categories: {allowed_tools}"}
    ]
    tool_selection_response = jarvus_ai.create_chat_completion(tool_selection_messages)
    # Helper to parse tool names/categories from LLM response
    import re
    import json as pyjson
    def parse_tools_from_response(resp):
        # Try to extract a JSON list from the response
        try:
            if isinstance(resp, dict) and 'assistant' in resp and 'content' in resp['assistant']:
                content = resp['assistant']['content']
            elif isinstance(resp, dict) and 'choices' in resp and resp['choices']:
                content = resp['choices'][0]['message']['content']
            else:
                content = str(resp)
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                return pyjson.loads(match.group(0))
            # fallback: try to parse whole content
            return pyjson.loads(content)
        except Exception:
            return []
    print("DEBUG tool_selection_response", tool_selection_response)
    needed_tools_or_categories = set(parse_tools_from_response(tool_selection_response))

    # Step 2: Filter allowed tools to only those needed
    filtered_tools = [
        t for t in allowed_tools
        if t in needed_tools_or_categories or (hasattr(t, 'category') and t.category.value in needed_tools_or_categories)
    ]
    sdk_tools = tool_registry.get_sdk_tools_by_modules(filtered_tools, user_scopes)
    logger.info(f"Filtered tools for LLM: {filtered_tools}")
    logger.info(f"Number of SDK tools being passed to LLM: {len(sdk_tools)}")
    logger.info(f"Tool choice setting: {tool_choice}")
    
    # Log the first few tools to see what's being passed
    if sdk_tools:
        logger.info(f"First 3 SDK tools: {[tool.function.name for tool in sdk_tools[:3]]}")
        logger.info(f"All SDK tool names: {[tool.function.name for tool in sdk_tools]}")
        
        # Add detailed logging for browser tools
        browser_tools = [tool for tool in sdk_tools if tool.function.name in ['open_website', 'navigate_to_url', 'click_element', 'type_text']]
        if browser_tools:
            logger.info(f"🔍 BROWSER TOOLS FOUND: {len(browser_tools)} tools")
            for tool in browser_tools:
                logger.info(f"🔍 Browser tool: {tool.function.name} - Description: {tool.function.description[:100]}...")
        else:
            logger.warning("❌ NO BROWSER TOOLS FOUND in SDK tools!")
            
    else:
        logger.warning("No SDK tools found - this is the problem!")
    
    # --- END: Two-step tool selection orchestration ---

    try:
        new_messages = []
    
        # Recursive tool calling loop
        while True:
            logger.info("Calling Azure AI for completion")
            logger.info(f"Messages being sent to LLM: {len(messages)} messages")
            logger.info(f"Tools being sent to LLM: {len(sdk_tools)} tools")
            
            # Log the first few messages to see what the LLM is getting
            if messages:
                first_msg = messages[0]
                logger.info(f"🔍 FIRST MESSAGE TYPE: {type(first_msg).__name__}")
                logger.info(f"🔍 FIRST MESSAGE ROLE: {getattr(first_msg, 'role', 'N/A')}")
                logger.info(f"🔍 FIRST MESSAGE CONTENT LENGTH: {len(getattr(first_msg, 'content', ''))}")
                logger.info(f"🔍 FIRST MESSAGE CONTAINS 'browser': {'browser' in getattr(first_msg, 'content', '').lower()}")
            
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
            logger.info(f"Response choice finish_reason: {choice.finish_reason}")
            logger.info(f"Message content: {msg.content}")
            logger.info(f"Message tool_calls: {msg.tool_calls}")
            logger.info(f"Number of tool calls: {len(msg.tool_calls) if msg.tool_calls else 0}")
            
            # Always ensure content is a string
            assistant_msg = AssistantMessage(content=msg.content if msg.content is not None else "", tool_calls=msg.tool_calls)
            messages.append(assistant_msg)
            new_messages.append({'role': 'assistant', 'content': assistant_msg.content})
            logger.info(f"Assistant message: {assistant_msg}")
            if not msg.tool_calls:
                logger.info("No tool calls in response - conversation complete")
                logger.warning("LLM did not call any tools despite having tools available!")
                break

            logger.info(f"Processing {len(msg.tool_calls)} tool calls")
            for call in msg.tool_calls:
                retries = 0
                max_retries = 3
                current_call = call
                while retries < max_retries:
                    tool_name = current_call.function.name
                    tool_args = json.loads(current_call.function.arguments) if current_call.function.arguments else {}
                    logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                    try:
                        tool_result = tool_registry.execute_tool(
                            tool_name=tool_name,
                            parameters=tool_args,
                            jwt_token=jwt_token,
                        )
                        # On success, append a ToolMessage with the result
                        tool_msg = ToolMessage(content=json.dumps(tool_result), tool_call_id=current_call.id)
                        messages.append(tool_msg)
                        # Prompt the LLM again to get the final response after tool execution
                        logger.info("Prompting LLM for final response after tool execution")
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
                        break  # Exit retry loop on success
                    except Exception as e:
                        error_msg = f"Tool call '{tool_name}' failed with error: {str(e)}"
                        logger.error(error_msg)
                        # Insert a ToolMessage with the error for this tool_call_id
                        tool_msg = ToolMessage(content=json.dumps({"error": error_msg}), tool_call_id=current_call.id)
                        messages.append(tool_msg)
                        # Inject a clear, actionable error as a user message for the LLM to see
                        messages.append(UserMessage(content=f"{error_msg}. Please analyze the error and try a different tool or fix the arguments and call a tool again. Do not just suggest alternatives in text—actually call a tool."))
                        # Add a system message to reinforce the instruction
                        messages.append(SystemMessage(content="When you see an error message, you must analyze it and try a different tool or fix the arguments and call a tool again. Do not just suggest alternatives in text—actually call a tool."))
                        retries += 1
                        if retries >= max_retries:
                            logger.error(f"Max retries reached for tool call '{tool_name}'. Moving on.")
                            break
                        # Prompt the LLM again for a new tool call after error
                        logger.info("Prompting LLM again after tool call failure")
                        response = jarvus_ai.client.complete(
                            messages=messages,
                            model=jarvus_ai.deployment_name,
                            tools=sdk_tools,
                            stream=False,
                            tool_choice="required"
                        )
                        logger.info("Received response from Azure AI (retry)")
                        choice = response.choices[0]
                        msg = choice.message
                        assistant_msg = AssistantMessage(content=msg.content if msg.content is not None else "", tool_calls=msg.tool_calls)
                        messages.append(assistant_msg)
                        new_messages.append({'role': 'assistant', 'content': assistant_msg.content})
                        logger.info(f"Assistant message (retry): {assistant_msg}")
                        if not msg.tool_calls:
                            logger.info("No tool calls in response after retry - conversation complete")
                            break
                        # Use the first tool call from the new LLM response
                        current_call = msg.tool_calls[0]

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
        
        # Save the user input and final assistant response to interaction history
        final_assistant_message = ""
        if new_messages:
            # Get the last assistant message from new_messages
            for msg in reversed(new_messages):
                if msg.get('role') == 'assistant' and msg.get('content'):
                    final_assistant_message = msg.get('content')
                    break
        
        if final_assistant_message:
            save_interaction(agent, user_text, final_assistant_message)
        
        agent = get_agent(agent_id, current_user.id)  # Re-fetch from DB
        return jsonify({"new_messages": [final_assistant_message]})

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