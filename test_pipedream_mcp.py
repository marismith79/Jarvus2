#!/usr/bin/env python3
"""
Test script using the existing MCP client to test Pipedream Google Docs endpoint
"""

import sys
import os

# Add the jarvus_app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvus_app'))

from services.mcp_client import MCPClient

def test_pipedream_with_mcp_client():
    """Test the Pipedream endpoint using the MCP client"""
    
    # Create a new MCP client instance pointing to the Pipedream endpoint
    pipedream_client = MCPClient(base_url="https://eojsclb8r4i421h.m.pipedream.net")
    
    print("Testing Pipedream Google Docs Endpoint with MCP Client")
    print("=" * 60)
    
    # Test 1: Create a new document
    print("\n1. Testing create_doc action...")
    create_doc_payload = {
        "action": "create_doc",
        "title": "Test Document from Jarvus MCP Client"
    }
    
    try:
        result = pipedream_client.execute_tool("", create_doc_payload)
        print(f"✅ Create doc successful!")
        print(f"Response: {result}")
        
        # Extract document ID if available
        doc_id = None
        if isinstance(result, dict):
            doc_id = result.get('documentId') or result.get('id')
        
        if doc_id:
            print(f"📄 Document ID: {doc_id}")
            
            # Test 2: Append text to the created document
            print(f"\n2. Testing append_text action with doc_id: {doc_id}...")
            append_text_payload = {
                "action": "append_text",
                "doc_id": doc_id,
                "text": "This text was appended using the Jarvus MCP client!"
            }
            
            try:
                append_result = pipedream_client.execute_tool("", append_text_payload)
                print(f"✅ Append text successful!")
                print(f"Response: {append_result}")
            except Exception as e:
                print(f"❌ Append text failed: {e}")
        else:
            print("⚠️  Could not extract document ID from response")
            
    except Exception as e:
        print(f"❌ Create doc failed: {e}")
    
    # Test 3: Test invalid action
    print(f"\n3. Testing invalid action...")
    invalid_payload = {
        "action": "invalid_action",
        "some_data": "test"
    }
    
    try:
        invalid_result = pipedream_client.execute_tool("", invalid_payload)
        print(f"Response: {invalid_result}")
    except Exception as e:
        print(f"✅ Invalid action properly handled: {e}")

def test_direct_requests():
    """Test direct requests to understand the endpoint behavior"""
    
    import requests
    import json
    
    print("\n" + "=" * 60)
    print("Testing Direct Requests to Pipedream Endpoint")
    print("=" * 60)
    
    base_url = "https://eojsclb8r4i421h.m.pipedream.net"
    
    # Test 1: Create document
    print("\n1. Direct request - Create document")
    create_payload = {
        "action": "create_doc",
        "title": "Direct Test Document"
    }
    
    try:
        response = requests.post(
            base_url,
            json=create_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 2: Invalid action
    print("\n2. Direct request - Invalid action")
    invalid_payload = {
        "action": "invalid_action",
        "test": "data"
    }
    
    try:
        response = requests.post(
            base_url,
            json=invalid_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("Pipedream Google Docs Endpoint Testing")
    print("=" * 60)
    
    # Test with MCP client
    test_pipedream_with_mcp_client()
    
    # Test direct requests
    test_direct_requests()
    
    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60) 