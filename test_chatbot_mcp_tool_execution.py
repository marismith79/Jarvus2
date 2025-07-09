import os
import sys
import json
import time
from unittest.mock import patch, Mock
from flask import Flask, session
import pytest

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up environment variables for testing
os.environ.update({
    "PIPEDREAM_API_CLIENT_ID": "test_client_id",
    "PIPEDREAM_API_CLIENT_SECRET": "test_client_secret", 
    "PIPEDREAM_PROJECT_ID": "proj_test123",
    "PIPEDREAM_ENVIRONMENT": "development",
    "PIPEDREAM_MCP_REQ_ENDPOINT": "https://mock-mcp-endpoint.test"
})

from jarvus_app.routes.chatbot import chatbot_bp
from jarvus_app.services.mcp_token_service import PipedreamAuthService

@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = 'test_secret'
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@patch('jarvus_app.services.mcp_token_service.requests.post')
@patch('flask_login.utils._get_user')
def test_mcp_tool_execution(mock_get_user, mock_requests_post, client, app):
    """
    Test that a tool call to a Pipedream MCP tool is executed and returns the expected result.
    """
    # Mock user
    class DummyUser:
        id = 123
        is_authenticated = True
    mock_get_user.return_value = DummyUser()

    # Mock MCP tool execution response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success", "data": {"docId": "abc123"}}
    mock_requests_post.return_value = mock_response

    tool_name = 'google_docs-create-document'
    tool_args = {"title": "Test Doc", "content": "Hello world"}
    app_slug = "google_docs"
    external_user_id = str(DummyUser.id)

    # Run inside a request context so session is available
    with app.test_request_context():
        session['pipedream_access_token'] = 'mock_token_123'
        session['pipedream_token_expires_at'] = int(time.time()) + 7200  # 2 hours from now
        # Re-instantiate the service to ensure it uses the correct session
        pipedream_auth_service = PipedreamAuthService()
        result = pipedream_auth_service.execute_tool(
            external_user_id=external_user_id,
            app_slug=app_slug,
            tool_name=tool_name,
            tool_args=tool_args
        )
        assert result["result"] == "success"
        assert "data" in result
        assert result["data"]["docId"] == "abc123"
        print("MCP tool execution test passed! Result:", result) 