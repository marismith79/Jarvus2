"""
Tests for Gmail MCP functionality.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from flask import Flask

from jarvus_app.models.oauth import OAuthCredentials
from jarvus_app.models.tool_permission import ToolPermission
from jarvus_app.services.mcp_client import MCPClient, AuthenticationError, PermissionError
from jarvus_app.services.tool_registry import tool_registry, ToolCategory, ToolMetadata
from jarvus_app.db import db

# Test data
TEST_USER_ID = "test_user_123"
TEST_EMAIL = "test@example.com"
TEST_ACCESS_TOKEN = "test_access_token"
TEST_REFRESH_TOKEN = "test_refresh_token"

@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        db.init_app(app)
        db.create_all()
        yield app

@pytest.fixture
def mcp_client():
    """Create an MCP client instance."""
    return MCPClient(base_url="http://localhost:8000")

@pytest.fixture
def mock_oauth_credentials(app):
    """Create mock OAuth credentials."""
    with app.app_context():
        credentials = Mock(spec=OAuthCredentials)
        credentials.user_id = TEST_USER_ID
        credentials.access_token = TEST_ACCESS_TOKEN
        credentials.refresh_token = TEST_REFRESH_TOKEN
        credentials.expires_at = datetime.utcnow() + timedelta(hours=1)
        return credentials

@pytest.fixture
def mock_gmail_permissions():
    """Create mock Gmail tool permissions."""
    permissions = []
    for tool_id in ["gmail.list_emails", "gmail.search_emails", "gmail.send_email"]:
        permission = Mock(spec=ToolPermission)
        permission.user_id = TEST_USER_ID
        permission.tool_id = tool_id
        permission.granted = True
        permissions.append(permission)
    return permissions

def test_list_emails(app, mcp_client, mock_oauth_credentials, mock_gmail_permissions):
    """Test listing emails."""
    with app.app_context():
        with patch("requests.post") as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "messages": [
                    {"id": "1", "threadId": "t1", "snippet": "Test email 1"},
                    {"id": "2", "threadId": "t2", "snippet": "Test email 2"}
                ]
            }
            mock_post.return_value = mock_response

            # Test the function
            result = mcp_client.handle_operation(
                tool_name="gmail",
                operation="list_emails",
                parameters={"max_results": 2}
            )
            
            # Verify the result
            assert len(result["messages"]) == 2
            assert result["messages"][0]["id"] == "1"
            assert result["messages"][1]["id"] == "2"
            
            # Verify the request was made to the correct URL
            mock_post.assert_called_once_with(
                "http://localhost:8000/gmail/list_emails",
                json={"max_results": 2}
            )

def test_search_emails(app, mcp_client, mock_oauth_credentials, mock_gmail_permissions):
    """Test searching emails."""
    with app.app_context():
        with patch("requests.post") as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "messages": [
                    {"id": "1", "threadId": "t1", "snippet": "Search result 1"},
                    {"id": "2", "threadId": "t2", "snippet": "Search result 2"}
                ]
            }
            mock_post.return_value = mock_response

            # Test the function
            result = mcp_client.handle_operation(
                tool_name="gmail",
                operation="search_emails",
                parameters={"query": "test", "max_results": 2}
            )
            
            # Verify the result
            assert len(result["messages"]) == 2
            assert result["messages"][0]["snippet"] == "Search result 1"
            assert result["messages"][1]["snippet"] == "Search result 2"
            
            # Verify the request was made to the correct URL
            mock_post.assert_called_once_with(
                "http://localhost:8000/gmail/search_emails",
                json={"query": "test", "max_results": 2}
            )

def test_send_email(app, mcp_client, mock_oauth_credentials, mock_gmail_permissions):
    """Test sending an email."""
    with app.app_context():
        with patch("requests.post") as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "msg_123",
                "threadId": "t1",
                "labelIds": ["SENT"]
            }
            mock_post.return_value = mock_response

            # Test parameters
            email_params = {
                "to": "recipient@example.com",
                "subject": "Test Subject",
                "body": "Test Body",
                "cc": "cc@example.com",
                "bcc": "bcc@example.com"
            }

            # Test the function
            result = mcp_client.handle_operation(
                tool_name="gmail",
                operation="send_email",
                parameters=email_params
            )
            
            # Verify the result
            assert result["id"] == "msg_123"
            assert result["threadId"] == "t1"
            assert "SENT" in result["labelIds"]
            
            # Verify the request was made to the correct URL
            mock_post.assert_called_once_with(
                "http://localhost:8000/gmail/send_email",
                json=email_params
            )

def test_authentication_error(app, mcp_client, mock_oauth_credentials, mock_gmail_permissions):
    """Test handling of authentication errors."""
    with app.app_context():
        with patch("requests.post") as mock_post:
            # Mock authentication error response
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.raise_for_status.side_effect = Exception("Unauthorized")
            mock_post.return_value = mock_response

            # Test the function
            with pytest.raises(AuthenticationError):
                mcp_client.handle_operation(
                    tool_name="gmail",
                    operation="list_emails",
                    parameters={}
                )

def test_permission_error(app, mcp_client, mock_oauth_credentials, mock_gmail_permissions):
    """Test handling of permission errors."""
    with app.app_context():
        with patch("requests.post") as mock_post:
            # Mock permission error response
            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.raise_for_status.side_effect = Exception("Forbidden")
            mock_post.return_value = mock_response

            # Test the function
            with pytest.raises(PermissionError):
                mcp_client.handle_operation(
                    tool_name="gmail",
                    operation="list_emails",
                    parameters={}
                )

def test_rate_limiting(app, mcp_client, mock_oauth_credentials, mock_gmail_permissions):
    """Test handling of rate limiting."""
    with app.app_context():
        with patch("requests.post") as mock_post:
            # Mock rate limit response
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.raise_for_status.side_effect = Exception("Rate limit exceeded")
            mock_post.return_value = mock_response

            # Test the function
            with pytest.raises(Exception) as exc_info:
                mcp_client.handle_operation(
                    tool_name="gmail",
                    operation="list_emails",
                    parameters={}
                )
            assert "Rate limit exceeded" in str(exc_info.value)

def test_invalid_tool(app, mcp_client):
    """Test handling of invalid tool name."""
    with app.app_context():
        with pytest.raises(ValueError) as exc_info:
            mcp_client.handle_operation(
                tool_name="invalid_tool",
                operation="list_emails",
                parameters={}
            )
        assert "Tool not found" in str(exc_info.value) 