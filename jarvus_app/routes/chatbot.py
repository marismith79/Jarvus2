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
from datetime import datetime, timedelta

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
from jarvus_app.models.todo import Todo
from ..db import db
from ..services.agent_service import agent_service
from ..utils.token_utils import get_valid_jwt_token
from ..services.pipedream_tool_registry import pipedream_tool_service

jarvus_ai = JarvusAIClient()

chatbot_bp = Blueprint('chatbot', __name__)
logger = logging.getLogger(__name__)
tool_choice = 'auto'

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
        tool_choice = data.get('tool_choice', 'auto')
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
        
        # # Add debug logging
        # logger.info(f"Final assistant message type: {type(final_assistant_message)}")
        # logger.info(f"Final assistant message length: {len(str(final_assistant_message)) if final_assistant_message else 0}")
        # logger.info(f"Final assistant message: {final_assistant_message[:200] if final_assistant_message else 'None'}...")
        # logger.info(f"Memory info: {memory_info}")
        
        response_data = {
            'response': final_assistant_message,
            'memory_info': memory_info,
            'thread_id': memory_info.get('thread_id')
        }
        
        # Log response metadata without the full content to avoid base64 spam
        logger.info(f"Sending response - length: {len(str(final_assistant_message)) if final_assistant_message else 0}, thread_id: {memory_info.get('thread_id')}")
        
        return jsonify(response_data), 200
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

# --- NEW: Todo API Routes ---
@chatbot_bp.route('/todos', methods=['GET'])
@login_required
def get_todos():
    """Get all todos for the current user."""
    try:
        todos = Todo.get_user_todos(current_user.id)
        return jsonify({'todos': [todo.to_dict() for todo in todos]}), 200
    except Exception as e:
        logger.error(f"Error fetching todos: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch todos'}), 500

@chatbot_bp.route('/todos', methods=['POST'])
@login_required
def create_todo():
    """Create a new todo for the current user."""
    try:
        data = request.get_json() or {}
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'Todo text is required'}), 400
        
        todo = Todo.create_todo(
            user_id=current_user.id,
            text=text,
            completed=data.get('completed', False)
        )
        
        return jsonify({'todo': todo.to_dict()}), 201
        
    except Exception as e:
        logger.error(f"Error creating todo: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to create todo'}), 500

@chatbot_bp.route('/todos/<int:todo_id>', methods=['PUT'])
@login_required
def update_todo(todo_id):
    """Update a todo for the current user."""
    try:
        todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()
        if not todo:
            return jsonify({'error': 'Todo not found'}), 404
        
        data = request.get_json() or {}
        text = data.get('text')
        completed = data.get('completed')
        
        todo.update_todo(text=text, completed=completed)
        
        return jsonify({'todo': todo.to_dict()}), 200
        
    except Exception as e:
        logger.error(f"Error updating todo {todo_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to update todo'}), 500

@chatbot_bp.route('/todos/<int:todo_id>', methods=['DELETE'])
@login_required
def delete_todo(todo_id):
    """Delete a todo for the current user."""
    try:
        todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()
        if not todo:
            return jsonify({'error': 'Todo not found'}), 404
        
        todo.delete_todo()
        
        return jsonify({'message': 'Todo deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting todo {todo_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to delete todo'}), 500

# --- NEW: Calendar Integration Route ---
@chatbot_bp.route('/calendar', methods=['GET'])
@login_required
def get_calendar_events():
    """Get Google Calendar events for the current user."""
    try:
        # Hardcoded request to pull Google Calendar data using Pipedream MCP
        external_user_id = str(current_user.id)
        app_slug = "google_calendar"
        
        # Try different possible tool names for listing events
        possible_tool_names = [
            "google_calendar-list-events",
            "google_calendar-events-list", 
            "google_calendar-get-events",
            "list-events",
            "events-list"
        ]
        
        # Get today's date range
        today = datetime.now().date()
        start_time = datetime.combine(today, datetime.min.time()).isoformat() + 'Z'
        end_time = datetime.combine(today, datetime.max.time()).isoformat() + 'Z'
        
        logger.info(f"Fetching events for today: {today}")
        logger.info(f"Time range: {start_time} to {end_time}")
        
        # Try to get available tools first to see what's available
        logger.info(f"Attempting to get calendar events for user {external_user_id}")
        
        # First, let's try to discover what tools are available
        tools_data = pipedream_tool_service.get_tools_for_app(external_user_id, app_slug)
        if tools_data and 'tools' in tools_data:
            available_tools = [tool.get('name', '') for tool in tools_data['tools']]
            logger.info(f"Available Google Calendar tools: {available_tools}")
            
            # Find the best matching tool for listing events
            list_events_tool = None
            for tool_name in possible_tool_names:
                if tool_name in available_tools:
                    list_events_tool = tool_name
                    break
            
            if not list_events_tool:
                # If no exact match, look for tools containing 'event' or 'list'
                for tool in tools_data['tools']:
                    tool_name = tool.get('name', '').lower()
                    if 'event' in tool_name or 'list' in tool_name:
                        list_events_tool = tool.get('name')
                        break
            
            if not list_events_tool:
                logger.error(f"No suitable calendar list events tool found. Available: {available_tools}")
                return jsonify({'error': 'No calendar list events tool available'}), 500
        else:
            logger.warning("Could not discover available tools, using default tool name")
            list_events_tool = "google_calendar-list-events"
        
        logger.info(f"Using calendar tool: {list_events_tool}")
        
        # Prepare tool arguments - try different parameter combinations
        tool_args_variations = [
            {
                "timeMin": start_time,
                "timeMax": end_time,
                "maxResults": 10
            },
            {
                "start": start_time,
                "end": end_time,
                "maxResults": 10
            },
            {
                "timeMin": start_time,
                "timeMax": end_time,
                "calendarId": "primary"
            },
            {
                "start": start_time,
                "end": end_time,
                "calendarId": "primary"
            }
        ]
        
        result = None
        for i, tool_args in enumerate(tool_args_variations):
            try:
                logger.info(f"Trying calendar tool with args variation {i+1}: {tool_args}")
                result = pipedream_tool_service.execute_tool(
                    external_user_id=external_user_id,
                    app_slug=app_slug,
                    tool_name=list_events_tool,
                    tool_args=tool_args
                )
                
                if result and 'error' not in result:
                    logger.info(f"Calendar tool succeeded with variation {i+1}")
                    break
                elif result and 'error' in result:
                    logger.warning(f"Calendar tool error with variation {i+1}: {result['error']}")
                    
            except Exception as e:
                logger.warning(f"Calendar tool exception with variation {i+1}: {str(e)}")
                continue
        
        if not result or 'error' in result:
            error_msg = result.get('error', 'Unknown error') if result else 'No result from calendar tool'
            logger.error(f"All calendar tool variations failed. Last error: {error_msg}")
            return jsonify({'error': f'Calendar access failed: {error_msg}'}), 500
        
        # Log the raw result for debugging
        logger.info(f"Calendar tool raw result: {result}")
        
        # Parse the calendar events from the result
        events = []
        
        # Handle different possible response structures
        items = None
        
        # Check if result has 'content' array (Pipedream MCP format)
        if 'content' in result and isinstance(result['content'], list):
            for content_item in result['content']:
                if isinstance(content_item, dict) and 'text' in content_item:
                    try:
                        # Parse the JSON string from the text field
                        text_content = content_item['text']
                        if isinstance(text_content, str):
                            parsed_content = json.loads(text_content)
                            if 'ret' in parsed_content and isinstance(parsed_content['ret'], list):
                                items = parsed_content['ret']
                                break
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Failed to parse content text: {e}")
                        continue
        
        # Fallback to direct structure checking
        if not items:
            if 'items' in result:
                items = result['items']
            elif 'events' in result:
                items = result['events']
            elif isinstance(result, list):
                items = result
            elif 'data' in result and isinstance(result['data'], list):
                items = result['data']
            elif 'ret' in result and isinstance(result['ret'], list):
                items = result['ret']
        
        if items:
            logger.info(f"Found {len(items)} calendar events")
            for item in items:
                # Handle different event structures
                if isinstance(item, dict):
                    start_time = item.get('start', {}).get('dateTime', item.get('start', {}).get('date')) if isinstance(item.get('start'), dict) else item.get('start')
                    end_time = item.get('end', {}).get('dateTime', item.get('end', {}).get('date')) if isinstance(item.get('end'), dict) else item.get('end')
                    
                    # Skip events without proper start/end times
                    if not start_time or not end_time:
                        continue
                    
                    try:
                        # Parse the start time and check if it's today
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        
                        # Convert to local timezone for comparison
                        from datetime import timezone
                        local_tz = datetime.now().astimezone().tzinfo
                        start_local = start_dt.astimezone(local_tz)
                        end_local = end_dt.astimezone(local_tz)
                        
                        # Check if the event is today
                        event_date = start_local.date()
                        if event_date != today:
                            logger.info(f"Skipping event '{item.get('summary', 'No Title')}' - date {event_date} is not today {today}")
                            continue
                        
                        event = {
                            'title': item.get('summary', item.get('title', 'No Title')),
                            'start': start_time,
                            'end': end_time,
                            'start_local': start_local.isoformat(),
                            'end_local': end_local.isoformat(),
                            'location': item.get('location', ''),
                            'description': item.get('description', ''),
                            'urgent': False,
                            'type': 'meeting' if 'meeting' in str(item.get('summary', '')).lower() else 'event'
                        }
                        events.append(event)
                        logger.info(f"Added event: {event['title']} at {start_local.strftime('%H:%M')}")
                        
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse event time for '{item.get('summary', 'No Title')}': {e}")
                        continue
        else:
            logger.warning(f"No events found in calendar response. Result structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")
        
        logger.info(f"Returning {len(events)} parsed events")
        return jsonify({'events': events}), 200
        
    except Exception as e:
        logger.error(f"Error fetching calendar events: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch calendar events: {str(e)}'}), 500

# --- NEW: Calendar Debug Route ---
@chatbot_bp.route('/calendar/debug', methods=['GET'])
@login_required
def debug_calendar():
    """Debug endpoint to check calendar access and available tools."""
    try:
        external_user_id = str(current_user.id)
        app_slug = "google_calendar"
        
        debug_info = {
            'user_id': external_user_id,
            'app_slug': app_slug,
            'timestamp': datetime.now().isoformat()
        }
        
        # Check if tools are available
        tools_data = pipedream_tool_service.get_tools_for_app(external_user_id, app_slug)
        if tools_data and 'tools' in tools_data:
            available_tools = [tool.get('name', '') for tool in tools_data['tools']]
            debug_info['available_tools'] = available_tools
            debug_info['tool_count'] = len(available_tools)
            
            # Check for event-related tools
            event_tools = [tool for tool in available_tools if 'event' in tool.lower()]
            debug_info['event_tools'] = event_tools
            
            # Check for list-related tools
            list_tools = [tool for tool in available_tools if 'list' in tool.lower()]
            debug_info['list_tools'] = list_tools
            
        else:
            debug_info['error'] = 'No tools data available'
            debug_info['tools_data'] = tools_data
        
        # Check authentication status
        try:
            auth_headers = pipedream_tool_service.get_mcp_auth_headers(external_user_id, app_slug)
            debug_info['auth_headers_available'] = bool(auth_headers)
            if auth_headers:
                debug_info['auth_keys'] = list(auth_headers.keys())
        except Exception as auth_error:
            debug_info['auth_error'] = str(auth_error)
        
        return jsonify(debug_info), 200
        
    except Exception as e:
        logger.error(f"Error in calendar debug: {str(e)}", exc_info=True)
        return jsonify({'error': f'Debug failed: {str(e)}'}), 500

# --- NEW: Todo Generation Route ---
@chatbot_bp.route('/generate-todos', methods=['POST'])
@login_required
def generate_morning_todos():
    """Generate morning todos through conversation with the agent."""
    try:
        data = request.get_json() or {}
        agent_id = data.get('agent_id')
        
        if not agent_id:
            return jsonify({'error': 'Agent ID is required'}), 400
        
        # Get today's date information
        today = datetime.now()
        today_str = today.strftime("%A, %B %d, %Y")  # e.g., "Friday, July 12, 2025"
        
        # Create a morning todo generation prompt with today's date
        morning_prompt = f"""Good morning! Today is {today_str}. It's time to plan your day. 

Based on your calendar for today ({today_str}), emails, and ongoing projects, please suggest 3-5 specific tasks for today. Focus on:
1. High-priority items that need attention
2. Follow-ups from yesterday
3. Preparation for upcoming meetings
4. Important deadlines

Please respond with just a simple list of tasks, one per line, without explanations."""
        
        # Get today's calendar events to provide context
        try:
            # Get today's calendar events for context
            today_events = []
            external_user_id = str(current_user.id)
            app_slug = "google_calendar"
            
            # Use the same calendar fetching logic as the calendar route
            tools_data = pipedream_tool_service.get_tools_for_app(external_user_id, app_slug)
            if tools_data and 'tools' in tools_data:
                available_tools = [tool.get('name', '') for tool in tools_data['tools']]
                list_events_tool = None
                for tool_name in ["google_calendar-list-events", "google_calendar-events-list", "list-events"]:
                    if tool_name in available_tools:
                        list_events_tool = tool_name
                        break
                
                if list_events_tool:
                    today = datetime.now().date()
                    start_time = datetime.combine(today, datetime.min.time()).isoformat() + 'Z'
                    end_time = datetime.combine(today, datetime.max.time()).isoformat() + 'Z'
                    
                    result = pipedream_tool_service.execute_tool(
                        external_user_id=external_user_id,
                        app_slug=app_slug,
                        tool_name=list_events_tool,
                        tool_args={"timeMin": start_time, "timeMax": end_time, "maxResults": 10}
                    )
                    
                    if result and 'content' in result:
                        for content_item in result['content']:
                            if isinstance(content_item, dict) and 'text' in content_item:
                                try:
                                    parsed_content = json.loads(content_item['text'])
                                    if 'ret' in parsed_content:
                                        for item in parsed_content['ret']:
                                            if isinstance(item, dict) and 'summary' in item:
                                                start_time = item.get('start', {}).get('dateTime', '')
                                                if start_time:
                                                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                                    local_tz = datetime.now().astimezone().tzinfo
                                                    start_local = start_dt.astimezone(local_tz)
                                                    if start_local.date() == today:
                                                        today_events.append({
                                                            'title': item.get('summary', 'No Title'),
                                                            'time': start_local.strftime('%H:%M'),
                                                            'duration': '1 hour'  # Default duration
                                                        })
                                except (json.JSONDecodeError, KeyError, ValueError):
                                    continue
        except Exception as e:
            logger.warning(f"Failed to fetch today's events for todo generation: {e}")
        
        # Add calendar context to the prompt
        calendar_context = ""
        if today_events:
            calendar_context = f"\n\nToday's calendar events:\n" + "\n".join([f"- {event['time']}: {event['title']}" for event in today_events[:5]])
        
        enhanced_prompt = morning_prompt + calendar_context
        
        # Use the agent service to process the morning prompt
        final_assistant_message, memory_info = agent_service.process_message(
            agent_id=agent_id,
            user_id=current_user.id,
            user_message=enhanced_prompt,
            thread_id=None,
            tool_choice='auto',
            web_search_enabled=True,
            logger=logger
        )
        
        # Parse the response to extract todo items
        if final_assistant_message:
            # Split by lines and clean up
            lines = final_assistant_message.split('\n')
            todos = []
            for line in lines:
                line = line.strip()
                # Remove common prefixes like numbers, dashes, etc.
                line = re.sub(r'^[\d\-\.\s]+', '', line)
                if line and len(line) > 3:  # Minimum length for a meaningful todo
                    todos.append(line)
            
            # Create todos in the database
            created_todos = []
            for todo_text in todos[:5]:  # Limit to 5 todos
                todo = Todo.create_todo(
                    user_id=current_user.id,
                    text=todo_text,
                    completed=False
                )
                created_todos.append(todo.to_dict())
            
            return jsonify({'todos': created_todos}), 200
        else:
            return jsonify({'error': 'Failed to generate todos'}), 500
            
    except Exception as e:
        logger.error(f"Error generating morning todos: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500