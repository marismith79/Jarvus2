import os
import sys
import json
import time
from unittest.mock import patch, Mock
from flask import Flask, session
import pytest
import types

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
from jarvus_app.services.pipedream_auth_service import PipedreamAuthService
from jarvus_app.services.agent_service import agent_service
from jarvus_app.models.user import User
from jarvus_app.db import db

@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = 'test_secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
    
    with app.app_context():
        db.init_app(app)
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_user_and_agent(app):
    """Create a test user and agent in the same session context"""
    with app.app_context():
        user = User(
            id='test_user_123',
            email='test@example.com',
            name='Test User'
        )
        db.session.add(user)
        db.session.commit()
        
        agent = agent_service.create_agent(
            user_id=user.id,
            name="Test Agent",
            tools=["google_docs"],
            description="Test agent for Google Docs"
        )
        
        return user.id, agent.id

@patch('jarvus_app.routes.chatbot.get_valid_jwt_token', return_value="dummy_token")
@patch('jarvus_app.services.mcp_token_service.PipedreamAuthService.get_access_token', return_value="mock_token_123")
@patch('jarvus_app.services.mcp_token_service.requests.post')
@patch('jarvus_app.llm.client.JarvusAIClient.create_chat_completion')
@patch('jarvus_app.routes.chatbot.jarvus_ai.client.complete')
@patch('flask_login.utils._get_user')
def test_chatbot_mcp_tool_execution_flow(
    mock_get_user,
    mock_azure_complete,
    mock_tool_selection,
    mock_requests_post,
    mock_access_token,
    mock_jwt,
    client,
    app,
    test_user_and_agent
):
    """
    Test the complete chatbot flow for calling a Google Docs tool through MCP.
    This simulates the actual flow from user message to tool execution.
    """
    test_user_id, test_agent_id = test_user_and_agent
    with app.test_request_context():
        # re-query user and agent
        test_user = User.query.get(test_user_id)
        test_agent = agent_service.get_agent(test_agent_id, test_user_id)
        mock_get_user.return_value = test_user

    # Mock tool selection response (LLM decides which tools to use)
    mock_tool_selection.return_value = {
        'assistant': {
            'content': '["google_docs"]'
        }
    }

    # Mock Azure AI responses
    # First response: LLM decides to call a tool
    mock_azure_complete.side_effect = [
        # First call: LLM decides to call google_docs-create-document
        Mock(
            choices=[
                Mock(
                    message=Mock(
                        content=None,
                        tool_calls=[
                            types.SimpleNamespace(
                                id="call_123",
                                function=types.SimpleNamespace(
                                    name="google_docs-create-document",
                                    arguments='{"title": "Test Document", "content": "Hello World"}'
                                )
                            )
                        ]
                    )
                )
            ]
        ),
        # Second call: LLM responds after tool execution
        Mock(
            choices=[
                Mock(
                    message=Mock(
                        content="I've created a new Google Doc titled 'Test Document' with the content 'Hello World'. The document has been successfully created.",
                        tool_calls=None
                    )
                )
            ]
        ),
        # Third call: LLM responds after tool execution
        Mock(
            choices=[
                Mock(
                    message=Mock(
                        content="I've created a new Google Doc titled 'Test Document' with the content 'Hello World'. The document has been successfully created.",
                        tool_calls=None
                    )
                )
            ]
        )
    ]

    # Mock MCP tool execution response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": "success",
        "data": {
            "docId": "abc123",
            "title": "Test Document",
            "url": "https://docs.google.com/document/d/abc123"
        }
    }
    mock_response.text = json.dumps(mock_response.json.return_value)
    mock_requests_post.return_value = mock_response

    # Run inside a request context so session is available
    with app.test_request_context():
        session['pipedream_access_token'] = 'mock_token_123'
        session['pipedream_token_expires_at'] = int(time.time()) + 7200  # 2 hours from now

        # Simulate the chatbot endpoint call
        response = client.post('/chatbot/send', json={
            'message': 'Create a new Google Doc titled "Test Document" with content "Hello World"',
            'agent_id': test_agent.id,
            'tool_choice': 'auto',
            'web_search_enabled': False
        })

        # Verify the response
        assert response.status_code == 200
        response_data = response.get_json()
        assert 'new_messages' in response_data
        assert len(response_data['new_messages']) == 1

        # Verify the final message mentions the document creation
        final_message = response_data['new_messages'][0]
        assert "Test Document" in final_message
        assert "created" in final_message.lower()

        # Verify that the MCP service was called with correct parameters
        mock_requests_post.assert_called_once()
        call_args = mock_requests_post.call_args

        # Verify the request was made to the correct endpoint
        assert f"/v1/{test_user_id}/google_docs" in call_args[0][0]  # URL contains correct MCP endpoint

        # Verify the request payload
        request_data = call_args[1]['json']
        assert request_data['method'] == 'tools/call'
        assert request_data['params']['name'] == 'google_docs-create-document'
        assert request_data['params']['arguments']['title'] == 'Test Document'
        assert request_data['params']['arguments']['content'] == 'Hello World'

        print("✅ Chatbot MCP tool execution flow test passed!")
        print(f"Final response: {final_message}")

@patch('jarvus_app.routes.chatbot.get_valid_jwt_token', return_value="dummy_token")
@patch('jarvus_app.services.mcp_token_service.PipedreamAuthService.get_access_token', return_value="mock_token_123")
@patch('jarvus_app.services.mcp_token_service.requests.post')
@patch('jarvus_app.llm.client.JarvusAIClient.create_chat_completion')
@patch('jarvus_app.routes.chatbot.jarvus_ai.client.complete')
@patch('flask_login.utils._get_user')
def test_chatbot_mcp_tool_execution_with_error_handling(
    mock_get_user,
    mock_azure_complete,
    mock_tool_selection,
    mock_requests_post,
    mock_access_token,
    mock_jwt,
    client,
    app,
    test_user_and_agent
):
    """
    Test the chatbot flow when MCP tool execution fails and error handling kicks in.
    """
    test_user_id, test_agent_id = test_user_and_agent
    with app.test_request_context():
        # re-query user and agent
        test_user = User.query.get(test_user_id)
        test_agent = agent_service.get_agent(test_agent_id, test_user_id)
        mock_get_user.return_value = test_user

    # Mock tool selection response
    mock_tool_selection.return_value = {
        'assistant': {
            'content': '["google_docs"]'
        }
    }

    # Mock Azure AI responses
    mock_azure_complete.side_effect = [
        # First call: LLM decides to call a tool
        Mock(
            choices=[
                Mock(
                    message=Mock(
                        content=None,
                        tool_calls=[
                            types.SimpleNamespace(
                                id="call_456",
                                function=types.SimpleNamespace(
                                    name="google_docs-create-document",
                                    arguments='{"title": "Error Test", "content": "This will fail"}'
                                )
                            )
                        ]
                    )
                )
            ]
        ),
        # Second call: LLM responds after tool error
        Mock(
            choices=[
                Mock(
                    message=Mock(
                        content="I encountered an error while trying to create the document. The tool call failed with a timeout error. Let me try a different approach or you might want to check your Google Docs connection.",
                        tool_calls=None
                    )
                )
            ]
        ),
        # Third call: LLM responds after tool error
        Mock(
            choices=[
                Mock(
                    message=Mock(
                        content="I encountered an error while trying to create the document. The tool call failed with a timeout error. Let me try a different approach or you might want to check your Google Docs connection.",
                        tool_calls=None
                    )
                )
            ]
        )
    ]

    # Mock MCP tool execution failure
    mock_response = Mock()
    mock_response.status_code = 408  # Timeout
    mock_response.json.return_value = {
        "error": "Request timeout",
        "message": "The MCP server did not respond in time"
    }
    mock_response.text = json.dumps(mock_response.json.return_value)
    mock_requests_post.return_value = mock_response

    # Run inside a request context
    with app.test_request_context():
        session['pipedream_access_token'] = 'mock_token_123'
        session['pipedream_token_expires_at'] = int(time.time()) + 7200

        # Simulate the chatbot endpoint call
        response = client.post('/chatbot/send', json={
            'message': 'Create a Google Doc that will fail',
            'agent_id': test_agent.id,
            'tool_choice': 'auto',
            'web_search_enabled': False
        })

        # Verify the response
        assert response.status_code == 200
        response_data = response.get_json()
        assert 'new_messages' in response_data

        # Verify the final message mentions the error
        final_message = response_data['new_messages'][0]
        assert "error" in final_message.lower() or "failed" in final_message.lower()

        # Verify that the MCP service was called (even though it failed)
        mock_requests_post.assert_called_once()

        print("✅ Chatbot MCP tool execution error handling test passed!")
        print(f"Error response: {final_message}")

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 