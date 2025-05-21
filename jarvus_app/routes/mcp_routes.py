from flask import Blueprint, request, jsonify
from ..services.mcp_service import mcp_service

mcp_bp = Blueprint('mcp', __name__)

@mcp_bp.route('/process', methods=['POST'])
def process_request():
    """Process a user request using Azure OpenAI and MCP server."""
    data = request.get_json()
    if not data or 'input' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing input in request'
        }), 400
    
    result = mcp_service.process_with_azure_openai(data['input'])
    return jsonify(result)

@mcp_bp.route('/tools', methods=['GET'])
def get_tools():
    """Get the list of available MCP tools."""
    tools = mcp_service.get_available_tools()
    return jsonify(tools) 