#!/usr/bin/env python3
"""
Real Google Docs creation test using actual MCP service and credentials.
This will actually create a document in your Google Docs account.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_real_google_docs_creation_direct():
    """
    Test creating a real Google Doc using direct MCP API calls.
    """
    print("🚀 Starting direct Google Docs creation test...")
    
    # Get credentials from environment
    client_id = os.getenv("PIPEDREAM_API_CLIENT_ID")
    client_secret = os.getenv("PIPEDREAM_API_CLIENT_SECRET")
    project_id = os.getenv("PIPEDREAM_PROJECT_ID")
    environment = os.getenv("PIPEDREAM_ENVIRONMENT")
    
    if not all([client_id, client_secret, project_id, environment]):
        print("❌ Missing required environment variables")
        return False
    
    # First, get an access token
    print("🔐 Getting access token...")
    token_url = "https://api.pipedream.com/v1/oauth/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        token_response = requests.post(token_url, data=token_data, timeout=10)
        if token_response.status_code != 200:
            print(f"❌ Failed to get access token: {token_response.status_code}")
            print(f"Response: {token_response.text}")
            return False
        
        token_info = token_response.json()
        access_token = token_info.get("access_token")
        if not access_token:
            print("❌ No access token in response")
            return False
        
        print("✅ Got access token")
        
    except Exception as e:
        print(f"❌ Error getting access token: {str(e)}")
        return False
    
    # Test parameters
    external_user_id = "b2c6c978-ce23-470e-aa97-f32e2cfb54e8"
    app_slug = "google_docs"
    tool_name = "google_docs-create-document"
    
    # Create a unique document title with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    document_title = f"Test Document Created by MCP {timestamp}"
    document_content = f"""
This is a test document created by the MCP service on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.

This document was created to test the integration between:
- Your application
- Pipedream MCP service
- Google Docs API

If you can see this document, the integration is working correctly!
    """.strip()
    
    tool_args = {
        "title": document_title,
        "content": document_content
    }
    
    print(f"📝 Attempting to create document: '{document_title}'")
    print(f"📄 Content preview: {document_content[:100]}...")
    print(f"🔧 Tool: {tool_name}")
    print(f"👤 User ID: {external_user_id}")
    print(f"📱 App: {app_slug}")
    print("-" * 50)
    
    # Prepare MCP request
    mcp_url = f"https://remote.mcp.pipedream.net/v1/{external_user_id}/{app_slug}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-pd-project-id": project_id,
        "x-pd-environment": environment,
        "x-pd-external-user-id": "b2c6c978-ce23-470e-aa97-f32e2cfb54e8",
        "x-pd-app-slug": app_slug,
        "x-pd-tool-mode": "tools-only",
        "x-pd-oauth-app-id": None,
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    mcp_body = {
        "jsonrpc": "2.0",
        "id": 20,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": tool_args
        }
    }
    
    print(f"[DEBUG] MCP URL: {mcp_url}")
    print(f"[DEBUG] MCP Headers: {headers}")
    print(f"[DEBUG] MCP Body: {mcp_body}")
    
    try:
        # Execute the MCP tool call
        response = requests.post(mcp_url, headers=headers, json=mcp_body, timeout=30)
        
        print(f"[DEBUG] MCP Response Status: {response.status_code}")
        print(f"[DEBUG] MCP Response: {response.text}")
        
        if response.status_code == 200:
            # Parse the response
            try:
                result = response.json()
            except json.JSONDecodeError:
                # Try parsing as SSE
                lines = response.text.strip().split('\n')
                for line in lines:
                    if line.startswith('data: '):
                        result = json.loads(line[6:])
                        break
                else:
                    print("❌ Could not parse response")
                    return False
            
            print("✅ Tool execution completed!")
            print(f"📊 Result: {json.dumps(result, indent=2)}")
            
            # Check if the document was created successfully
            if result.get("result") == "success":
                data = result.get("data", {})
                doc_id = data.get("docId")
                doc_url = data.get("url")
                doc_title = data.get("title")
                
                print("\n🎉 SUCCESS! Document created successfully!")
                print(f"📋 Document ID: {doc_id}")
                print(f"📋 Document Title: {doc_title}")
                print(f"🔗 Document URL: {doc_url}")
                print(f"\n📖 You can view your document at: {doc_url}")
                
                return True
            else:
                print(f"❌ Document creation failed: {result}")
                return False
        else:
            print(f"❌ MCP request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating document: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("🔐 Real Google Docs MCP Integration Test (Direct)")
    print("=" * 50)
    
    # Check if we have the required environment variables
    required_env_vars = [
        "PIPEDREAM_API_CLIENT_ID",
        "PIPEDREAM_API_CLIENT_SECRET", 
        "PIPEDREAM_PROJECT_ID",
        "PIPEDREAM_ENVIRONMENT"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please set these in your .env file or environment")
        sys.exit(1)
    
    print("✅ Environment variables found")
    
    # Test: Create a new document
    print("\n" + "="*50)
    print("TEST: Creating a new document")
    print("="*50)
    create_success = test_real_google_docs_creation_direct()
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"📝 Document creation: {'✅ PASSED' if create_success else '❌ FAILED'}")
    
    if create_success:
        print("\n🎉 Congratulations! Your MCP integration is working!")
        print("You should now have a new document in your Google Docs account.")
    else:
        print("\n🔧 The integration needs some troubleshooting.")
        print("Check your Pipedream credentials and Google Docs permissions.") 