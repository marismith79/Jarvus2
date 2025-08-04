import os
import sys
import time
from flask import Flask, session
from jarvus_app.services.pipedream_auth_service import PipedreamAuthService
import requests

USER_ID = "b2c6c978-ce23-470e-aa97-f32e2cfb54e8"
APP_SLUG = "google_docs"
TOOL_NAME = "google_docs-create-document"

# Sample arguments for creating a document
TOOL_ARGS = {
    "title": "Test Document from MCP Integration",
    "content": "This is a test document created via the Pipedream MCP integration test."
}

# Set up Flask app for session context
app = Flask(__name__)
app.secret_key = 'test_secret'

with app.app_context():
    with app.test_request_context():
        session.clear()
        pipedream_auth_service = PipedreamAuthService()
        print("Discovering available tools for user via direct MCP endpoint...")
        registry = pipedream_auth_service.discover_all_tools(USER_ID)
        tools_data = pipedream_auth_service.get_tools_for_app(USER_ID, APP_SLUG)
        print(f"Tools data: {tools_data}")
        if tools_data and tools_data.get('tools'):
            print(f"Available tools for {APP_SLUG}: {[t['name'] for t in tools_data['tools']]}")
        else:
            print(f"No tools found for app: {APP_SLUG}")
            sys.exit(1)
        print(f"\nExecuting tool: {TOOL_NAME} for user {USER_ID} via direct MCP endpoint...")
        result = pipedream_auth_service.execute_tool(
            external_user_id=USER_ID,
            app_slug=APP_SLUG,
            tool_name=TOOL_NAME,
            tool_args=TOOL_ARGS
        )
        print("\nTool execution response:")
        print(result) 