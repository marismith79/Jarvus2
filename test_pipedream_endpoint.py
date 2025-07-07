#!/usr/bin/env python3
"""
Test script for Pipedream Google Docs endpoint
Tests both create_doc and append_text actions
"""

import json
import subprocess
import sys

def test_create_doc():
    """Test creating a new Google Doc"""
    print("=== Testing create_doc action ===")
    
    payload = {
        "action": "create_doc",
        "title": "Test Document from Jarvus"
    }
    
    curl_command = [
        "curl", "-X", "POST",
        "https://eojsclb8r4i421h.m.pipedream.net",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
        "-v"
    ]
    
    print(f"Command: {' '.join(curl_command)}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        print(f"Status Code: {result.returncode}")
        print(f"Response: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing curl: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")

def test_append_text():
    """Test appending text to an existing Google Doc"""
    print("\n=== Testing append_text action ===")
    
    # You'll need to replace this with an actual document ID from a previous create_doc call
    doc_id = "YOUR_DOCUMENT_ID_HERE"  # Replace with actual doc ID
    
    payload = {
        "action": "append_text",
        "doc_id": doc_id,
        "text": "This is test text appended from Jarvus application!"
    }
    
    curl_command = [
        "curl", "-X", "POST",
        "https://eojsclb8r4i421h.m.pipedream.net",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
        "-v"
    ]
    
    print(f"Command: {' '.join(curl_command)}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        print(f"Status Code: {result.returncode}")
        print(f"Response: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing curl: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")

def test_invalid_action():
    """Test with an invalid action to see error handling"""
    print("\n=== Testing invalid action ===")
    
    payload = {
        "action": "invalid_action",
        "some_data": "test"
    }
    
    curl_command = [
        "curl", "-X", "POST",
        "https://eojsclb8r4i421h.m.pipedream.net",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
        "-v"
    ]
    
    print(f"Command: {' '.join(curl_command)}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        print(f"Status Code: {result.returncode}")
        print(f"Response: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing curl: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")

def generate_curl_commands():
    """Generate the curl commands as strings for manual execution"""
    print("\n=== Generated CURL Commands ===")
    
    # Create doc command
    create_doc_payload = {
        "action": "create_doc",
        "title": "Test Document from Jarvus"
    }
    
    create_doc_curl = f"""curl -X POST https://eojsclb8r4i421h.m.pipedream.net \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(create_doc_payload)}' \\
  -v"""
    
    print("1. Create Document:")
    print(create_doc_curl)
    
    # Append text command (replace YOUR_DOCUMENT_ID_HERE with actual ID)
    append_text_payload = {
        "action": "append_text",
        "doc_id": "YOUR_DOCUMENT_ID_HERE",
        "text": "This is test text appended from Jarvus application!"
    }
    
    append_text_curl = f"""curl -X POST https://eojsclb8r4i421h.m.pipedream.net \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(append_text_payload)}' \\
  -v"""
    
    print("\n2. Append Text (replace YOUR_DOCUMENT_ID_HERE with actual doc ID):")
    print(append_text_curl)
    
    # Invalid action command
    invalid_payload = {
        "action": "invalid_action",
        "some_data": "test"
    }
    
    invalid_curl = f"""curl -X POST https://eojsclb8r4i421h.m.pipedream.net \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(invalid_payload)}' \\
  -v"""
    
    print("\n3. Test Invalid Action:")
    print(invalid_curl)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--generate":
        generate_curl_commands()
    else:
        print("Testing Pipedream Google Docs Endpoint")
        print("=" * 50)
        
        # Test create_doc first
        test_create_doc()
        
        # Test invalid action
        test_invalid_action()
        
        print("\n" + "=" * 50)
        print("Note: To test append_text, you need to:")
        print("1. Run the create_doc test first")
        print("2. Extract the document ID from the response")
        print("3. Update the doc_id in test_append_text() function")
        print("4. Run: python test_pipedream_endpoint.py")
        
        print("\nOr generate curl commands with:")
        print("python test_pipedream_endpoint.py --generate") 