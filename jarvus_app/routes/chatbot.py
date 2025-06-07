from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from ..services.mcp_service import mcp_service
from ..services.mcp_client import mcp_client
from ..llm.client import OpenAIClient
from ..models.user_tool import UserTool
import json

chatbot_bp = Blueprint('chatbot', __name__)

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
        
        # Get the user's available tools directly from the database
        user_tools = UserTool.query.filter_by(user_id=current_user.id, is_active=True).all()
        print(f"Available tools: {[tool.tool_name for tool in user_tools]}")
        
        # Define the available tools with their full specifications
        tools = [
            {
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
            },
            {
                "type": "function",
                "function": {
                    "name": "search_emails",
                    "description": "Advanced email search with Gmail query syntax",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Gmail query syntax for searching emails"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of emails to return"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        # Use the LLM client to generate a response
        llm_client = OpenAIClient()
        messages = [
            llm_client.format_message("system", """You are a helpful assistant with access to Gmail through the MCP server. 
            You can list and search emails using the available tools.
            When a user asks about their emails, use the appropriate tool to fetch the information.
            For listing recent emails, use the list_emails tool.
            For searching specific emails, use the search_emails tool."""),
            llm_client.format_message("user", data['message'])
        ]
        
        print("\nSending request to OpenAI...")
        response = llm_client.create_chat_completion(
            messages,
            tools=tools
        )
        
        # Check if the response includes tool calls
        if hasattr(response.choices[0].message, 'tool_calls'):
            print("\nTool calls detected:")
            for tool_call in response.choices[0].message.tool_calls:
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
                    else:
                        raise ValueError(f"Unknown tool: {tool_call.function.name}")
                    
                    print(f"\nTool execution result: {result}")
                    
                    # Add tool response to messages
                    messages.append(response.choices[0].message)
                    messages.append(llm_client.format_tool_message(
                        tool_call.id,
                        json.dumps(result)
                    ))
                    
                    # Get final response from OpenAI
                    print("\nGetting final response from OpenAI...")
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
            'reply': response.choices[0].message.content,
            'tool_executed': False
        })
        
    except Exception as e:
        print(f"Error in handle_chat_message: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error processing message: {str(e)}'
        }), 500 