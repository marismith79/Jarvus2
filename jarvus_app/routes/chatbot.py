import json

from flask import Blueprint, Response, jsonify, request
from flask_login import current_user, login_required

from ..llm.client import JarvusAIClient
from ..models.user_tool import UserTool
from ..services.mcp_client import mcp_client
from ..utils.text_formatter import format_chat_message
from ..utils.tool_permissions import TOOL_FEATURES, check_tool_access
from ..services.tools import TOOL_DEFS

chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.route("/available_tools", methods=["GET"])
@login_required
def get_available_tools():
    """Get the list of available tools and their features for the current user."""
    user_tools = UserTool.query.filter_by(
        user_id=current_user.id, is_active=True
    ).all()
    available_tools = {}

    for tool in user_tools:
        if tool.tool_name in TOOL_FEATURES:
            features = {}
            for feature, description in TOOL_FEATURES[tool.tool_name].items():
                if check_tool_access(current_user.id, tool.tool_name, feature):
                    features[feature] = description
            if (
                features
            ):  # Only include tools that have at least one accessible feature
                available_tools[tool.tool_name] = features

    return jsonify(available_tools)


@chatbot_bp.route("/send", methods=["POST"])
@login_required
def handle_chat_message():
    """Process a user message and return the response."""
    data = request.get_json()
    if not data or "message" not in data:
        return (
            jsonify({"success": False, "error": "Missing message in request"}),
            400,
        )

    try:
        print("\n=== Processing Chat Message ===")
        print(f"User message: {data['message']}")

        # Get the user's available tools and their features
        user_tools = UserTool.query.filter_by(
            user_id=current_user.id, is_active=True
        ).all()
        available_tools = {}
        for tool in user_tools:
            if tool.tool_name in TOOL_FEATURES:
                features = {}
                for feature, description in TOOL_FEATURES[
                    tool.tool_name
                ].items():
                    if check_tool_access(
                        current_user.id, tool.tool_name, feature
                    ):
                        features[feature] = description
                if features:
                    available_tools[tool.tool_name] = features

        print(f"Available tools: {available_tools}")

        # Build tools list from TOOL_DEFS based on available_tools
        tools = []
        for tool_def in TOOL_DEFS:
            tool_name = tool_def["name"]
            # Map tool_def name to available_tools features
            if tool_name == "list_emails" and "gmail" in available_tools and "list_messages" in available_tools["gmail"]:
                tools.append(tool_def["openai_schema"])
            elif tool_name == "send_email" and "gmail" in available_tools and "send_email" in available_tools["gmail"]:
                tools.append(tool_def["openai_schema"])
            elif tool_name == "list_events" and "calendar" in available_tools and "events" in available_tools["calendar"]:
                tools.append(tool_def["openai_schema"])
            elif tool_name == "create_event" and "calendar" in available_tools and "events" in available_tools["calendar"]:
                tools.append(tool_def["openai_schema"])

        # Use the LLM client to generate a response
        llm_client = JarvusAIClient()
        messages = [
            llm_client.format_message(
                "system",
                f"""You are a helpful AI assistant made for task automation.

            When interacting with users:
            1. Be concise and clear in your responses
            2. Use the available tools when appropriate
            3. If you need to use a tool, explain what you're going to do first
            4. If you can't help with something, be honest about it

            Available tools:
            {json.dumps(available_tools, indent=2)}

            When using tools:
            1. Explain what you're doing before using a tool
            2. Format tool results in a clear, readable way
            3. Provide context and insights about the results
            4. Handle errors gracefully and inform the user if something goes wrong""",
            ),
            llm_client.format_message("user", data["message"]),
        ]

        def generate():
            try:
                for chunk in llm_client.create_chat_completion(
                    messages, tools=tools
                ):
                    # Format the chunk using the text formatter
                    formatted_chunk = format_chat_message(chunk)
                    yield f"data: {json.dumps({'content': formatted_chunk})}\n\n"
            except Exception as e:
                print(f"Error in generate: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(generate(), mimetype="text/event-stream")

    except Exception as e:
        print(f"Error in handle_chat_message: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@chatbot_bp.route("/send", methods=["GET"])
@login_required
def handle_chat_message_sse():
    """Process a user message via SSE (GET) and return the response."""
    message = request.args.get("message")
    if not message:
        return (
            jsonify({"success": False, "error": "Missing message in request"}),
            400,
        )

    try:
        print("\n=== Processing Chat Message (SSE GET) ===")
        print(f"User message: {message}")

        # Get the user's available tools and their features
        user_tools = UserTool.query.filter_by(
            user_id=current_user.id, is_active=True
        ).all()
        available_tools = {}
        for tool in user_tools:
            if tool.tool_name in TOOL_FEATURES:
                features = {}
                for feature, description in TOOL_FEATURES[
                    tool.tool_name
                ].items():
                    if check_tool_access(
                        current_user.id, tool.tool_name, feature
                    ):
                        features[feature] = description
                if features:
                    available_tools[tool.tool_name] = features

        print(f"Available tools: {available_tools}")

        # Build tools list from TOOL_DEFS based on available_tools
        tools = []
        for tool_def in TOOL_DEFS:
            tool_name = tool_def["name"]
            # Map tool_def name to available_tools features
            if tool_name == "list_emails" and "gmail" in available_tools and "list_messages" in available_tools["gmail"]:
                tools.append(tool_def["openai_schema"])
            elif tool_name == "send_email" and "gmail" in available_tools and "send_email" in available_tools["gmail"]:
                tools.append(tool_def["openai_schema"])
            elif tool_name == "list_events" and "calendar" in available_tools and "events" in available_tools["calendar"]:
                tools.append(tool_def["openai_schema"])
            elif tool_name == "create_event" and "calendar" in available_tools and "events" in available_tools["calendar"]:
                tools.append(tool_def["openai_schema"])

        # Use the LLM client to generate a response
        llm_client = JarvusAIClient()
        messages = [
            llm_client.format_message(
                "system",
                f"""You are a helpful AI assistant made for task automation.

            When interacting with users:
            1. Be concise and clear in your responses
            2. Use the available tools when appropriate
            3. If you need to use a tool, explain what you're going to do first
            4. If you can't help with something, be honest about it

            Available tools:
            {json.dumps(available_tools, indent=2)}

            When using tools:
            1. Explain what you're doing before using a tool
            2. Format tool results in a clear, readable way
            3. Provide context and insights about the results
            4. Handle errors gracefully and inform the user if something goes wrong""",
            ),
            llm_client.format_message("user", message),
        ]

        def generate():
            try:
                for chunk in llm_client.create_chat_completion(
                    messages, tools=tools
                ):
                    # Format the chunk using the text formatter
                    formatted_chunk = format_chat_message(chunk)
                    yield f"data: {json.dumps({'content': formatted_chunk})}\n\n"
            except Exception as e:
                print(f"Error in generate: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(generate(), mimetype="text/event-stream")

    except Exception as e:
        print(f"Error in handle_chat_message_sse: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
