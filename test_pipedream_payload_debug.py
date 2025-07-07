#!/usr/bin/env python3
"""
Debug script to test Pipedream payload structure and identify null value issues
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_payload_structure():
    """Test different payload structures to identify the null value issue"""
    print("🔍 Testing Pipedream payload structures...")
    
    client_id = os.getenv("PIPEDREAM_API_CLIENT_ID")
    client_secret = os.getenv("PIPEDREAM_API_CLIENT_SECRET")
    project_id = os.getenv("PIPEDREAM_PROJECT_ID")
    redirect_uri = os.getenv("PIPEDREAM_REDIRECT_URI")
    oauth_app_id = os.getenv("PIPEDREAM_DOCS_OAUTH_APP_ID")
    
    if not all([client_id, client_secret, project_id, redirect_uri, oauth_app_id]):
        print("❌ Missing required environment variables")
        return False
    
    # Step 1: Get Bearer token
    print("\n=== STEP 1: Getting Bearer Token ===")
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "project_id": project_id,
        "environment": "development"
    }
    
    token_response = requests.post(
        "https://api.pipedream.com/v1/oauth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        data=token_data,
        timeout=30
    )
    
    if token_response.status_code != 200:
        print(f"❌ Token request failed: {token_response.status_code}")
        return False
    
    bearer_token = token_response.json().get("access_token")
    print("✅ Bearer token obtained")
    
    # Step 2: Test different payload structures
    print("\n=== STEP 2: Testing Payload Structures ===")
    
    # Test 1: Standard payload (what you're currently using)
    print("\n--- Test 1: Standard Payload ---")
    payload1 = {
        "external_user_id": "test_user_123",
        "project_id": project_id,
        "oauth_app_id": oauth_app_id,
        "source": "docs",
        "success_redirect_uri": f"{redirect_uri}/docs?state=test1",
        "error_redirect_uri": f"{redirect_uri}/docs?state=test1",
        "allowed_origins": ["http://localhost:5001"],
        "environment": "development"
    }
    
    print("Payload 1:", json.dumps(payload1, indent=2))
    response1 = make_connect_request(bearer_token, project_id, payload1)
    print("Response 1:", json.dumps(response1, indent=2))
    
    # Test 2: Payload with explicit null values (to test null handling)
    print("\n--- Test 2: Payload with Explicit Nulls ---")
    payload2 = {
        "external_user_id": "test_user_123",
        "project_id": project_id,
        "oauth_app_id": oauth_app_id,
        "source": "docs",
        "success_redirect_uri": f"{redirect_uri}/docs?state=test2",
        "error_redirect_uri": f"{redirect_uri}/docs?state=test2",
        "allowed_origins": ["http://localhost:5001"],
        "environment": "development",
        "app_id": None,  # Explicit null
        "project_environment": None  # Explicit null
    }
    
    print("Payload 2:", json.dumps(payload2, indent=2))
    response2 = make_connect_request(bearer_token, project_id, payload2)
    print("Response 2:", json.dumps(response2, indent=2))
    
    # Test 3: Minimal payload (only required fields)
    print("\n--- Test 3: Minimal Payload ---")
    payload3 = {
        "external_user_id": "test_user_123",
        "project_id": project_id,
        "oauth_app_id": oauth_app_id,
        "source": "docs",
        "success_redirect_uri": f"{redirect_uri}/docs?state=test3",
        "error_redirect_uri": f"{redirect_uri}/docs?state=test3"
    }
    
    print("Payload 3:", json.dumps(payload3, indent=2))
    response3 = make_connect_request(bearer_token, project_id, payload3)
    print("Response 3:", json.dumps(response3, indent=2))
    
    # Test 4: Payload with different field names (testing field mapping)
    print("\n--- Test 4: Alternative Field Names ---")
    payload4 = {
        "external_user_id": "test_user_123",
        "project_id": project_id,
        "app_id": oauth_app_id,  # Using app_id instead of oauth_app_id
        "source": "docs",
        "success_redirect_uri": f"{redirect_uri}/docs?state=test4",
        "error_redirect_uri": f"{redirect_uri}/docs?state=test4",
        "allowed_origins": ["http://localhost:5001"],
        "environment": "development"
    }
    
    print("Payload 4:", json.dumps(payload4, indent=2))
    response4 = make_connect_request(bearer_token, project_id, payload4)
    print("Response 4:", json.dumps(response4, indent=2))
    
    return True

def make_connect_request(bearer_token, project_id, payload):
    """Make a connect token request and return the response"""
    try:
        response = requests.post(
            f"https://api.pipedream.com/v1/connect/{project_id}/tokens",
            headers={
                "Authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json",
                "X-PD-Environment": "development"
            },
            json=payload,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text, "status": response.status_code}
    except Exception as e:
        return {"error": str(e)}

def test_environment_validation():
    """Validate that environment variables are properly set"""
    print("\n🔍 Validating Environment Variables...")
    
    required_vars = {
        "PIPEDREAM_API_CLIENT_ID": os.getenv("PIPEDREAM_API_CLIENT_ID"),
        "PIPEDREAM_API_CLIENT_SECRET": os.getenv("PIPEDREAM_API_CLIENT_SECRET"),
        "PIPEDREAM_PROJECT_ID": os.getenv("PIPEDREAM_PROJECT_ID"),
        "PIPEDREAM_REDIRECT_URI": os.getenv("PIPEDREAM_REDIRECT_URI"),
        "PIPEDREAM_DOCS_OAUTH_APP_ID": os.getenv("PIPEDREAM_DOCS_OAUTH_APP_ID"),
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if var_value:
            print(f"✅ {var_name}: {'*' * len(var_value)} (length: {len(var_value)})")
        else:
            print(f"❌ {var_name}: NOT SET")
            missing_vars.append(var_name)
    
    if missing_vars:
        print(f"\n❌ Missing variables: {missing_vars}")
        return False
    
    print("\n✅ All environment variables are set")
    return True

def main():
    print("🚀 Pipedream Payload Debug Test")
    print("=" * 50)
    
    if not test_environment_validation():
        return False
    
    return test_payload_structure()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Debug test completed successfully")
    else:
        print("\n❌ Debug test failed")
        sys.exit(1) 