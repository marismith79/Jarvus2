import pytest
from flask import Flask, session
from unittest.mock import patch, MagicMock
import time

# Import the function to test
from jarvus_app.utils.token_utils import get_valid_jwt_token

@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = 'test'
    return app

# Helper to set session values
class SessionSetter:
    def __init__(self, client):
        self.client = client
    def set(self, **kwargs):
        with self.client.session_transaction() as sess:
            for k, v in kwargs.items():
                sess[k] = v

# Test: valid JWT, no refresh needed
def test_valid_jwt_token(app):
    with app.test_request_context():
        now = int(time.time())
        session['jwt_token'] = 'valid.jwt.token'
        session['refresh_token'] = 'refresh_token'
        session['expires_at'] = now + 3600
        assert get_valid_jwt_token() == 'valid.jwt.token'

# Test: expired JWT, refresh succeeds
@patch('jarvus_app.utils.token_utils.msal.ConfidentialClientApplication')
def test_expired_jwt_refresh_success(mock_msal, app):
    with app.test_request_context():
        now = int(time.time())
        session['jwt_token'] = 'expired.jwt.token'
        session['refresh_token'] = 'refresh_token'
        session['expires_at'] = now - 10
        # Mock MSAL refresh
        mock_app = MagicMock()
        mock_app.acquire_token_by_refresh_token.return_value = {
            'id_token': 'new.jwt.token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3600
        }
        mock_msal.return_value = mock_app
        token = get_valid_jwt_token()
        assert token == 'new.jwt.token'
        assert session['jwt_token'] == 'new.jwt.token'
        assert session['refresh_token'] == 'new_refresh_token'
        assert int(session['expires_at']) > now

# Test: expired JWT, refresh fails
@patch('jarvus_app.utils.token_utils.msal.ConfidentialClientApplication')
def test_expired_jwt_refresh_fail(mock_msal, app):
    with app.test_request_context():
        now = int(time.time())
        session['jwt_token'] = 'expired.jwt.token'
        session['refresh_token'] = 'refresh_token'
        session['expires_at'] = now - 10
        # Mock MSAL refresh failure
        mock_app = MagicMock()
        mock_app.acquire_token_by_refresh_token.return_value = {}
        mock_msal.return_value = mock_app
        token = get_valid_jwt_token()
        assert token is None
        assert 'jwt_token' not in session
        assert 'refresh_token' not in session
        assert 'expires_at' not in session 