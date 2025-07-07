#!/usr/bin/env python3
"""
Test script for Pipedream Connect Link API OAuth flow
"""

import os
import sys
import requests
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
import base64
import json
from urllib.parse import urlparse, parse_qs, urlencode

# Load environment variables from .env file
load_dotenv()

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_pipedream_env_vars():
    print("\n==== Pipedream Environment Variables ====")
    var_names = [
        # New (correct) variables
        "PIPEDREAM_API_CLIENT_ID",
        "PIPEDREAM_API_CLIENT_SECRET",
        "PIPEDREAM_PROJECT_ID",
        "PIPEDREAM_REDIRECT_URI",
        "PIPEDREAM_DOCS_OAUTH_APP_ID",
        "PIPEDREAM_SHEETS_OAUTH_APP_ID",
        "PIPEDREAM_SLIDES_OAUTH_APP_ID",
        "PIPEDREAM_DRIVE_OAUTH_APP_ID",
        "PIPEDREAM_GMAIL_OAUTH_APP_ID",
        "PIPEDREAM_CALENDAR_OAUTH_APP_ID",
        # Old (deprecated) variables
        "PIPEDREAM_CLIENT_ID",
        "PIPEDREAM_CLIENT_SECRET",
        "PIPEDREAM_DOCS_AUTH_URL",
        "PIPEDREAM_DOCS_CALLBACK_URL",
        "PIPEDREAM_DOCS_ENDPOINT",
    ]
    for var in var_names:
        value = os.getenv(var)
        print(f"{var}: {value if value else 'NOT SET'}")
    print("==== End Pipedream Environment Variables ====")
    # Print the raw environment for PIPEDREAM_REDIRECT_URI
    print(f"os.environ['PIPEDREAM_REDIRECT_URI']: {os.environ.get('PIPEDREAM_REDIRECT_URI', 'NOT SET')}")
    # Print the .env file value if possible
    try:
        with open('.env') as f:
            for line in f:
                if line.strip().startswith('PIPEDREAM_REDIRECT_URI='):
                    print(f".env file PIPEDREAM_REDIRECT_URI: {line.strip()}")
    except Exception as e:
        print(f"Could not read .env file: {e}")

def test_connect_link_api_credentials():
    """Test that all required environment variables are set"""
    print("🔍 Testing Pipedream OAuth credentials...")
    
    required_vars = [
        "PIPEDREAM_REDIRECT_URI",
        "PIPEDREAM_DOCS_OAUTH_APP_ID"   # OAuth app ID for docs integration
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * len(value)} (length: {len(value)})")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    print("✅ All Connect Link API credentials are configured")
    return True

def test_connect_link_api_call():
    """Test the direct Pipedream OAuth URL generation"""
    print("\n🔍 Testing direct Pipedream OAuth URL generation...")
    
    redirect_uri = os.getenv("PIPEDREAM_REDIRECT_URI")
    oauth_app_id = os.getenv("PIPEDREAM_DOCS_OAUTH_APP_ID")
    
    if not oauth_app_id:
        print("❌ PIPEDREAM_DOCS_OAUTH_APP_ID not configured")
        return False
    
    if not redirect_uri:
        print("❌ PIPEDREAM_REDIRECT_URI not configured")
        return False

    # Test generating the OAuth URL (similar to what the function does)
    state = "test_state_123"
    auth_url = (
        f"https://pipedream.com/connect/oauth/{oauth_app_id}?"
        f"redirect_uri={redirect_uri}/docs&"
        f"state={state}&"
        f"source=docs"
    )
    
    print(f"🔗 Generated OAuth URL: {auth_url}")
    print(f"🔑 OAuth App ID: {oauth_app_id}")
    print(f"🔗 Redirect URI: {redirect_uri}")
    
    # Basic validation
    if "pipedream.com/connect/oauth/" in auth_url and oauth_app_id in auth_url:
        print("✅ OAuth URL generated successfully!")
        return True
    else:
        print("❌ OAuth URL generation failed")
        return False

def test_oauth_route_integration():
    """Test that the OAuth route can be imported and configured"""
    print("\n🔍 Testing OAuth route integration...")
    
    try:
        # Test importing the OAuth module
        from jarvus_app.routes.oauth import oauth_bp, connect_pipedream_service
        
        print("✅ OAuth module imports successfully")
        
        # Test that the function exists and is callable
        if callable(connect_pipedream_service):
            print("✅ connect_pipedream_service function is callable")
        else:
            print("❌ connect_pipedream_service is not callable")
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_basic_auth_credentials():
    """Test that OAuth app ID is valid format"""
    print("\n🔍 Testing OAuth app ID format...")
    
    oauth_app_id = os.getenv("PIPEDREAM_DOCS_OAUTH_APP_ID")
    
    if not oauth_app_id:
        print("❌ PIPEDREAM_DOCS_OAUTH_APP_ID not configured")
        return False
    
    # Basic validation - OAuth app IDs typically start with 'oa_'
    if oauth_app_id.startswith("oa_"):
        print("✅ OAuth app ID format looks valid!")
        return True
    else:
        print(f"❌ OAuth app ID format may be invalid: {oauth_app_id}")
        return False

def test_connect_link_api_real_call():
    """Test the actual Pipedream Connect Link API call with proper two-step authentication"""
    print("\n🔍 Testing real Connect Link API call with two-step authentication...")

    client_id = os.getenv("PIPEDREAM_API_CLIENT_ID")
    client_secret = os.getenv("PIPEDREAM_API_CLIENT_SECRET")
    project_id = os.getenv("PIPEDREAM_PROJECT_ID")
    redirect_uri = os.getenv("PIPEDREAM_REDIRECT_URI")
    oauth_app_id = os.getenv("PIPEDREAM_DOCS_OAUTH_APP_ID")

    if not all([client_id, client_secret, project_id, redirect_uri, oauth_app_id]):
        print("❌ Missing one or more required environment variables for real API call")
        return False

    import base64
    import json

    # Step 1: Get Bearer token using client credentials
    print("=== STEP 1: GETTING BEARER TOKEN ===")
    
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "project_id": project_id,
        "environment": "development"
    }
    
    print("Token Request URL:", "https://api.pipedream.com/v1/oauth/token")
    print("Token Request Headers:", json.dumps({
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }, indent=2))
    print("Token Request Payload:", json.dumps(token_data, indent=2))
    
    try:
        token_response = requests.post(
            "https://api.pipedream.com/v1/oauth/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
            },
            data=token_data,
            timeout=30
        )
        
        print("=== TOKEN RESPONSE ===")
        print("Status:", token_response.status_code)
        print("Headers:", dict(token_response.headers))
        print("Body:", token_response.text)
        print("===============================")
        
        if token_response.status_code != 200:
            print("❌ Failed to get Bearer token!")
            return False
        
        token_info = token_response.json()
        bearer_token = token_info.get("access_token")
        
        if not bearer_token:
            print("❌ No access_token in token response!")
            return False
        
        print("✅ Successfully obtained Bearer token!")
        
    except Exception as e:
        print(f"❌ Exception during token request: {e}")
        return False

    # Step 2: Use Bearer token to create connect token
    print("\n=== STEP 2: CREATING CONNECT TOKEN ===")
    bearer_auth = f"Bearer {bearer_token}"
    
    state = "test_state_python_debug"
    connect_token_data = {
        "external_user_id": "test_user_123",  # Hardcoded to match Node.js test
        "project_id": project_id,
        "oauth_app_id": oauth_app_id,
        "source": "docs",
        "success_redirect_uri": f"{redirect_uri}/docs?state={state}",
        "error_redirect_uri": f"{redirect_uri}/docs?state={state}",
        "allowed_origins": ["http://localhost:5001"]
    }

    print("Connect Token Request URL:", f"https://api.pipedream.com/v1/connect/{project_id}/tokens")
    print("Connect Token Request Headers:", json.dumps({
        "Authorization": bearer_auth,
        "Content-Type": "application/json",
        "X-PD-Environment": "development"
    }, indent=2))
    print("Connect Token Request Payload:", json.dumps(connect_token_data, indent=2))

    try:
        response = requests.post(
            f"https://api.pipedream.com/v1/connect/{project_id}/tokens",
            headers={
                "Authorization": bearer_auth,
                "Content-Type": "application/json",
                "X-PD-Environment": "development"
            },
            json=connect_token_data,
            timeout=30
        )
        
        print("=== CONNECT TOKEN RESPONSE ===")
        print("Status:", response.status_code)
        print("Headers:", dict(response.headers))
        print("Body:", response.text)
        print("===============================")
        
        if response.status_code == 200:
            connect_data = response.json()
            connect_link_url = connect_data.get("connect_link_url")
            if connect_link_url:
                # Fix: Append required 'app' parameter and 'connectLink=true' flag
                # This prevents the null values issue where Pipedream doesn't know which OAuth app to load
                
                # Parse the existing URL
                parsed_url = urlparse(connect_link_url)
                query_params = parse_qs(parsed_url.query)
                
                # Add required parameters
                query_params['connectLink'] = ['true']
                query_params['app'] = ['docs']  # Use the service name as the app slug
                
                # Rebuild the URL with the new parameters
                new_query = urlencode(query_params, doseq=True)
                fixed_connect_link_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{new_query}"
                
                print("✅ Real Connect Link API call succeeded!")
                print(f"🔗 Original Connect Link URL: {connect_link_url}")
                print(f"🔗 Fixed Connect Link URL: {fixed_connect_link_url}")
                return True
            else:
                print("❌ No connect_link_url in response!")
                return False
        else:
            print("❌ Real Connect Link API call failed!")
            return False
    except Exception as e:
        print(f"❌ Exception during connect token request: {e}")
        return False

def test_oauth_route_function():
    """Test that the OAuth route function can generate a connect link URL"""
    print("\n🔍 Testing OAuth route function...")
    
    try:
        # Import the function
        from jarvus_app.routes.oauth import connect_pipedream_service
        
        # Mock Flask context for testing
        from flask import Flask
        from flask_login import LoginManager
        from unittest.mock import Mock, patch
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Mock current_user
        mock_user = Mock()
        mock_user.id = 123
        
        with app.test_request_context():
            with patch('flask_login.current_user', mock_user):
                with patch('flask.redirect') as mock_redirect:
                    with patch('flask.url_for') as mock_url_for:
                        mock_url_for.return_value = "/profile"
                        
                        # Mock the requests.post calls
                        with patch('requests.post') as mock_post:
                            # Mock token response
                            mock_token_response = Mock()
                            mock_token_response.status_code = 200
                            mock_token_response.json.return_value = {
                                "access_token": "test_bearer_token_123",
                                "token_type": "Bearer",
                                "expires_in": 3600
                            }
                            
                            # Mock connect token response
                            mock_connect_response = Mock()
                            mock_connect_response.status_code = 200
                            mock_connect_response.json.return_value = {
                                "connect_link_url": "https://pipedream.com/_static/connect.html?token=test_token"
                            }
                            
                            # Set up the mock to return different responses for different calls
                            mock_post.side_effect = [mock_token_response, mock_connect_response]
                            
                            # Call the function
                            result = connect_pipedream_service("docs")
                            
                            # Verify the function was called
                            assert mock_post.call_count == 2, "Expected 2 API calls (token + connect)"
                            
                            # Verify redirect was called
                            mock_redirect.assert_called_once_with("https://pipedream.com/_static/connect.html?token=test_token")
                            
                            print("✅ OAuth route function works correctly!")
                            return True
                            
    except Exception as e:
        print(f"❌ OAuth route function test failed: {e}")
        return False

def main():
    print_pipedream_env_vars()
    """Run all tests"""
    print("🚀 Testing Pipedream Direct OAuth Integration")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_connect_link_api_credentials),
        ("OAuth App ID Format", test_basic_auth_credentials),
        ("OAuth URL Generation", test_connect_link_api_call),
        ("OAuth Route Integration", test_oauth_route_integration),
        ("Real Connect Link API Call", test_connect_link_api_real_call),
        ("OAuth Route Function", test_oauth_route_function)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Direct OAuth integration is working.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 