import os
import sys
import time
from flask import Flask, session
from jarvus_app.services.mcp_token_service import PipedreamAuthService

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
        # Ensure the session is clear and ready
        session.clear()
        # The service will fetch a real token using your .env credentials
        pipedream_auth_service = PipedreamAuthService()
        # Discover tools (to ensure registry is fresh, not strictly needed for execution)
        print("Discovering available tools for user...")
        registry = pipedream_auth_service.discover_all_tools(USER_ID)
        print(f"Discovered apps: {list(registry._apps.keys())}")
        if APP_SLUG in registry._apps:
            app_tools = registry._apps["google_docs"]
            # print(f"Available tools for {APP_SLUG}: {[t.name for t in app_tools.tools]}")
        else:
            print(f"No tools found for app: {APP_SLUG}")
            sys.exit(1)
        app_tools = registry._apps["google_docs"]

        # Execute the create-document tool
        print(f"\nExecuting tool: {TOOL_NAME} for user {USER_ID}...")
        result = pipedream_auth_service.execute_tool(
            external_user_id=USER_ID,
            app_slug=APP_SLUG,
            tool_name=TOOL_NAME,
            tool_args=TOOL_ARGS
        )
        print("\nTool execution response:")
        print(result) 