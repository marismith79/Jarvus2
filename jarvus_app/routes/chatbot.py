from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from ..services.mcp_client import mcp_client
from ..llm.client import JarvusAIClient
from ..models.user_tool import UserTool
from ..utils.tool_permissions import TOOL_FEATURES, check_tool_access
import json

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/available_tools', methods=['GET'])
@login_required
def get_available_tools():
    """Get the list of available tools and their features for the current user."""
    user_tools = UserTool.query.filter_by(user_id=current_user.id, is_active=True).all()
    available_tools = {}
    
    for tool in user_tools:
        if tool.tool_name in TOOL_FEATURES:
            features = {}
            for feature, description in TOOL_FEATURES[tool.tool_name].items():
                if check_tool_access(current_user.id, tool.tool_name, feature):
                    features[feature] = description
            if features:  # Only include tools that have at least one accessible feature
                available_tools[tool.tool_name] = features
    
    return jsonify(available_tools)

@chatbot_bp.route('/send', methods=['POST'])
@login_required
def handle_chat_message():
    """Process a user message and return the response."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing message in request'
        }), 400
    
    try:
        print("\n=== Processing Chat Message ===")
        print(f"User message: {data['message']}")
        
        # Get the user's available tools and their features
        user_tools = UserTool.query.filter_by(user_id=current_user.id, is_active=True).all()
        available_tools = {}
        for tool in user_tools:
            if tool.tool_name in TOOL_FEATURES:
                features = {}
                for feature, description in TOOL_FEATURES[tool.tool_name].items():
                    if check_tool_access(current_user.id, tool.tool_name, feature):
                        features[feature] = description
                if features:
                    available_tools[tool.tool_name] = features
        
        print(f"Available tools: {available_tools}")
        
        # Define the available tools with their full specifications
        tools = []
        
        # Add Gmail tools if available
        if 'gmail' in available_tools:
            if 'list_messages' in available_tools['gmail']:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": "list_emails",
                        "description": "List recent emails from your inbox with optional filtering",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of emails to return"
                                },
                                "query": {
                                    "type": "string",
                                    "description": "Gmail query syntax for filtering emails"
                                }
                            },
                            "required": []
                        }
                    }
                })
            
            if 'send_email' in available_tools['gmail']:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": "send_email",
                        "description": "Send new emails with support for CC and BCC",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "to": {
                                    "type": "string",
                                    "description": "Recipient email address"
                                },
                                "subject": {
                                    "type": "string",
                                    "description": "Email subject"
                                },
                                "body": {
                                    "type": "string",
                                    "description": "Email body content"
                                },
                                "cc": {
                                    "type": "string",
                                    "description": "CC email address",
                                    "required": False
                                },
                                "bcc": {
                                    "type": "string",
                                    "description": "BCC email address",
                                    "required": False
                                }
                            },
                            "required": ["to", "subject", "body"]
                        }
                    }
                })
        
        # Add Calendar tools if available
        if 'calendar' in available_tools:
            if 'events' in available_tools['calendar']:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": "list_events",
                        "description": "List upcoming calendar events with date range filtering",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of events to return"
                                },
                                "time_min": {
                                    "type": "string",
                                    "description": "Start time in ISO 8601 format (e.g., 2024-01-01T00:00:00Z)"
                                },
                                "time_max": {
                                    "type": "string",
                                    "description": "End time in ISO 8601 format (e.g., 2024-12-31T23:59:59Z)"
                                }
                            },
                            "required": []
                        }
                    }
                })
                
                tools.append({
                    "type": "function",
                    "function": {
                        "name": "create_event",
                        "description": "Create new calendar events with attendees",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "summary": {
                                    "type": "string",
                                    "description": "Event title"
                                },
                                "start": {
                                    "type": "string",
                                    "description": "Start time in ISO 8601 format (e.g., 2024-01-24T10:00:00Z)"
                                },
                                "end": {
                                    "type": "string",
                                    "description": "End time in ISO 8601 format (e.g., 2024-01-24T11:00:00Z)"
                                },
                                "location": {
                                    "type": "string",
                                    "description": "Event location"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Event description"
                                },
                                "attendees": {
                                    "type": "array",
                                    "description": "List of attendee email addresses",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": ["summary", "start", "end"]
                        }
                    }
                })
        
        # Use the LLM client to generate a response
        llm_client = JarvusAIClient()
        messages = [
            llm_client.format_message("system", f"""You are a helpful AI assistant made for task automation.
            
            When interacting with users:
            1. Be concise and clear in your responses
            2. Use the available tools when appropriate
            3. If you're not sure about something, ask for clarification
            4. Always maintain a professional and friendly tone
            
            Available tools:
            {json.dumps(available_tools, indent=2)}
            
            When using tools:
            1. Explain what you're doing before using a tool
            2. Format tool results in a clear, readable way
            3. Provide context and insights about the results
            4. Handle errors gracefully and inform the user if something goes wrong"""),
            llm_client.format_message("user", data['message'])
        ]
        
        print("\nSending request to Azure AI Foundry Models...")
        response = llm_client.create_chat_completion(
            messages,
            tools=tools,

        )
        
        # Check if the response includes tool calls
        choice = response.choices[0]
        tool_calls = getattr(choice.message, 'tool_calls', None)
        if tool_calls:
            print("\nTool calls detected:")
            for tool_call in tool_calls:
                print(f"Tool: {tool_call.function.name}")
                print(f"Arguments: {tool_call.function.arguments}")
                
                # Execute the tool call
                try:
                    args = json.loads(tool_call.function.arguments)
                    
                    # Map tool names to MCP client methods
                    if tool_call.function.name == "list_emails":
                        result = mcp_client.list_emails(
                            max_results=args.get('max_results', 10),
                            query=args.get('query')
                        )
                    elif tool_call.function.name == "search_emails":
                        result = mcp_client.search_emails(
                            query=args['query'],
                            max_results=args.get('max_results', 10)
                        )
                    elif tool_call.function.name == "send_email":
                        result = mcp_client.send_email(
                            to=args['to'],
                            subject=args['subject'],
                            body=args['body'],
                            cc=args.get('cc'),
                            bcc=args.get('bcc')
                        )
                    elif tool_call.function.name == "list_events":
                        result = mcp_client.list_events(
                            max_results=args.get('max_results', 10),
                            time_min=args.get('time_min'),
                            time_max=args.get('time_max')
                        )
                    elif tool_call.function.name == "create_event":
                        result = mcp_client.create_event(
                            summary=args['summary'],
                            start=args['start'],
                            end=args['end'],
                            location=args.get('location'),
                            description=args.get('description'),
                            attendees=args.get('attendees')
                        )
                    else:
                        raise ValueError(f"Unknown tool: {tool_call.function.name}")
                    
                    print(f"\nTool execution result: {result}")
                    
                    # Add tool response to messages
                    messages.append(choice.message)
                    messages.append(llm_client.format_tool_message(
                        tool_call.id,
                        json.dumps(result)
                    ))
                    
                    # Get final response from Azure AI Foundry Models
                    print("\nGetting final response from Azure AI Foundry Models...")
                    final_response = llm_client.create_chat_completion(messages)
                    return jsonify({
                        'success': True,
                        'reply': final_response.choices[0].message.content,
                        'tool_executed': True,
                        'tool_result': result
                    })
                except Exception as e:
                    print(f"Error executing tool: {str(e)}")
                    return jsonify({
                        'success': False,
                        'error': f'Error executing tool: {str(e)}'
                    }), 500
        # If no tool calls, return the direct response
        return jsonify({
            'success': True,
            'reply': choice.message.content,
            'tool_executed': False
        })
        
    except Exception as e:
        print(f"Error in handle_chat_message: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error processing message: {str(e)}'
        }), 500 