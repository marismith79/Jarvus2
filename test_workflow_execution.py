#!/usr/bin/env python3
"""
Test script for workflow execution functionality
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:5000"
TEST_USER_EMAIL = "test@example.com"  # Replace with actual test user

def test_workflow_creation_and_execution():
    """Test creating a workflow and executing it"""
    
    # Sample workflow data (YC Company Scraper example)
    workflow_data = {
        "name": "YC Company Scraper",
        "description": "Scrape companies from Y Combinator batches and compile contact details",
        "goal": "Scrape companies from the most recent Y Combinator batch and compile them with contact details into a spreadsheet.",
        "instructions": """1. Visit the Y Combinator website and identify the most recent batches (e.g., F24, W24, S24, X25, S25).
2. For each company, collect the following information using the {scraping_ant} tool:
    - Company name
    - Short description/pitch
    - Company URL
    - Category/industry
    - Information on each founder
        - Research each company to find contact information:
        - Visit the company website
        - Look for founder/team information
        - Find contact email (prioritize non-generic emails)
        - Search for and gather social media profiles (Twitter/LinkedIn)
        - Fill in the spreadsheet with all collected data, sorted alphabetically by company name.
3. Create a {google_sheets} with the following columns:
    - Company Name
    - Description/Pitch
    - Company URL
    - Category/Industry
    - Founder Names
    - Contact Email
    - Social Media Links
    - YC Batch (e.g., W24)
4. Title the spreadsheet "YC [Batch] Companies - [Date]".
5. Send a message when you're done""",
        "notes": """- Only include companies from the 4 most recent YC batch.
- If unable to find contact information after a reasonable search, note "Not found" in the relevant fields.
- Respect rate limits when scraping to avoid being blocked.
- Format the spreadsheet with proper header styling and column widths for readability."""
    }
    
    print("🧪 Testing Workflow Creation and Execution")
    print("=" * 50)
    
    # Step 1: Create a workflow
    print("\n1. Creating workflow...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/workflows",
            json=workflow_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            workflow = response.json()["workflow"]
            workflow_id = workflow["id"]
            print(f"✅ Workflow created successfully! ID: {workflow_id}")
            print(f"   Name: {workflow['name']}")
        else:
            print(f"❌ Failed to create workflow: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating workflow: {str(e)}")
        return False
    
    # Step 2: Execute the workflow
    print("\n2. Executing workflow...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/workflows/{workflow_id}/execute",
            json={},  # No specific agent_id, will create temporary agent
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            execution = response.json()["execution"]
            execution_id = execution["execution_id"]
            print(f"✅ Workflow execution started! Execution ID: {execution_id}")
            print(f"   Status: {execution['status']}")
            print(f"   Workflow: {execution['workflow_name']}")
        else:
            print(f"❌ Failed to execute workflow: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error executing workflow: {str(e)}")
        return False
    
    # Step 3: Check execution status
    print("\n3. Checking execution status...")
    try:
        response = requests.get(f"{BASE_URL}/api/executions/{execution_id}")
        
        if response.status_code == 200:
            execution = response.json()["execution"]
            print(f"✅ Execution status retrieved!")
            print(f"   Status: {execution['status']}")
            print(f"   Current Step: {execution['current_step']}/{execution['total_steps']}")
            if execution['results']:
                print(f"   Results: {len(execution['results'])} step(s) completed")
        else:
            print(f"❌ Failed to get execution status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking execution status: {str(e)}")
    
    # Step 4: List user executions
    print("\n4. Listing user executions...")
    try:
        response = requests.get(f"{BASE_URL}/api/executions")
        
        if response.status_code == 200:
            executions = response.json()["executions"]
            print(f"✅ Found {len(executions)} execution(s) for user")
            for exec_info in executions:
                print(f"   - {exec_info['workflow_name']}: {exec_info['status']}")
        else:
            print(f"❌ Failed to list executions: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error listing executions: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Workflow execution test completed!")
    return True

def test_workflow_management():
    """Test workflow CRUD operations"""
    
    print("\n🧪 Testing Workflow Management")
    print("=" * 50)
    
    # Test workflow data
    test_workflow = {
        "name": "Test Workflow",
        "description": "A simple test workflow",
        "goal": "Test the workflow system",
        "instructions": "1. Print a test message\n2. Confirm the workflow is working\n3. Complete the test",
        "notes": "This is a test workflow for system validation"
    }
    
    # Create workflow
    print("\n1. Creating test workflow...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/workflows",
            json=test_workflow,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            workflow = response.json()["workflow"]
            workflow_id = workflow["id"]
            print(f"✅ Test workflow created! ID: {workflow_id}")
        else:
            print(f"❌ Failed to create test workflow: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating test workflow: {str(e)}")
        return False
    
    # Get workflow
    print("\n2. Retrieving workflow...")
    try:
        response = requests.get(f"{BASE_URL}/api/workflows/{workflow_id}")
        
        if response.status_code == 200:
            workflow = response.json()["workflow"]
            print(f"✅ Workflow retrieved successfully!")
            print(f"   Name: {workflow['name']}")
            print(f"   Goal: {workflow['goal'][:50]}...")
        else:
            print(f"❌ Failed to retrieve workflow: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error retrieving workflow: {str(e)}")
    
    # Update workflow
    print("\n3. Updating workflow...")
    try:
        update_data = {"name": "Updated Test Workflow", "notes": "This workflow has been updated"}
        response = requests.put(
            f"{BASE_URL}/api/workflows/{workflow_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            workflow = response.json()["workflow"]
            print(f"✅ Workflow updated successfully!")
            print(f"   New name: {workflow['name']}")
        else:
            print(f"❌ Failed to update workflow: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error updating workflow: {str(e)}")
    
    # List workflows
    print("\n4. Listing workflows...")
    try:
        response = requests.get(f"{BASE_URL}/api/workflows")
        
        if response.status_code == 200:
            workflows = response.json()["workflows"]
            print(f"✅ Found {len(workflows)} workflow(s)")
            for wf in workflows:
                print(f"   - {wf['name']} (ID: {wf['id']})")
        else:
            print(f"❌ Failed to list workflows: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error listing workflows: {str(e)}")
    
    # Clean up - delete test workflow
    print("\n5. Cleaning up test workflow...")
    try:
        response = requests.delete(f"{BASE_URL}/api/workflows/{workflow_id}")
        
        if response.status_code == 200:
            print(f"✅ Test workflow deleted successfully!")
        else:
            print(f"❌ Failed to delete test workflow: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error deleting test workflow: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Workflow management test completed!")
    return True

if __name__ == "__main__":
    print("🚀 Starting Workflow System Tests")
    print("Make sure the Flask app is running on http://localhost:5000")
    print("Make sure you're logged in as a test user")
    print()
    
    # Run tests
    test_workflow_management()
    test_workflow_creation_and_execution()
    
    print("\n✨ All tests completed!") 