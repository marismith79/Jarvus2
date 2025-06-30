#!/usr/bin/env python3
"""
Test script to evaluate browser agent performance with enhanced recording data.
Run this after recording a workflow with the Chrome extension.
"""

import json
import sys
import os
from datetime import datetime

def test_browser_agent(recording_file_path, task_description=None):
    """
    Test the browser agent with recorded data.
    
    Args:
        recording_file_path (str): Path to the exported recording JSON file
        task_description (str): Optional custom task description
    """
    
    print("🧪 Browser Agent Performance Test")
    print("=" * 50)
    
    # Load the recorded data
    try:
        with open(recording_file_path, 'r') as f:
            recorded_data = json.load(f)
        print(f"✅ Loaded recording from: {recording_file_path}")
    except FileNotFoundError:
        print(f"❌ Error: Recording file not found: {recording_file_path}")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in recording file: {recording_file_path}")
        return
    
    # Analyze the recording
    session = recorded_data.get('recordingSession', {})
    actions = recorded_data.get('actions', [])
    
    print(f"📊 Recording Analysis:")
    print(f"   - Duration: {session.get('duration', 0)}ms")
    print(f"   - Total actions: {len(actions)}")
    print(f"   - Start time: {datetime.fromtimestamp(session.get('startTime', 0)/1000)}")
    
    # Count action types
    action_types = {}
    for action in actions:
        action_type = action.get('type', 'unknown')
        action_types[action_type] = action_types.get(action_type, 0) + 1
    
    print(f"   - Action breakdown: {action_types}")
    
    # Count screenshots
    screenshot_count = 0
    for action in actions:
        screenshots = action.get('screenshots', {})
        if screenshots:
            screenshot_count += len(screenshots)
    
    print(f"   - Screenshots captured: {screenshot_count}")
    
    # Default task description if not provided
    if not task_description:
        task_description = f"Complete the recorded workflow with {len(actions)} actions"
    
    print(f"\n🎯 Task: {task_description}")
    print(f"⏱️  Starting browser agent test...")
    
    # Import the web browse executor
    try:
        # Add parent directory to path since we're now in benchmarks/ subdirectory
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(parent_dir)
        from jarvus_app.services.tools.web import web_browse_executor
    except ImportError as e:
        print(f"❌ Error importing web_browse_executor: {e}")
        print("Make sure you're running this from the project root directory")
        return
    
    # Test the web browse tool
    start_time = datetime.now()
    
    try:
        result = web_browse_executor("web", {
            "operation": "web_browse",
            "parameters": {
                "task": task_description,
                "recorded_actions": recorded_data
            }
        })
        
        end_time = datetime.now()
        execution_duration = (end_time - start_time).total_seconds()
        
        print(f"\n📈 Test Results:")
        print(f"   - Success: {result.get('success', False)}")
        print(f"   - Total execution time: {execution_duration:.2f} seconds")
        
        if 'timing' in result:
            timing = result['timing']
            print(f"   - Agent execution time: {timing.get('execution_time_seconds', 0)} seconds")
            print(f"   - Total overhead: {timing.get('total_executor_time_seconds', 0) - timing.get('execution_time_seconds', 0):.2f} seconds")
        
        if result.get('success'):
            print(f"   - Status: ✅ SUCCESS")
        else:
            print(f"   - Status: ❌ FAILED")
            print(f"   - Error: {result.get('error', 'Unknown error')}")
        
        print(f"\n📝 Agent Result:")
        print(f"   {result.get('result', 'No result provided')}")
        
        # Performance analysis
        print(f"\n📊 Performance Analysis:")
        if session.get('duration', 0) > 0:
            human_duration = session.get('duration', 0) / 1000  # Convert to seconds
            speedup = human_duration / execution_duration if execution_duration > 0 else 0
            print(f"   - Human recording time: {human_duration:.2f} seconds")
            print(f"   - Agent execution time: {execution_duration:.2f} seconds")
            print(f"   - Speedup factor: {speedup:.2f}x")
        
        # Enhanced data analysis
        enhanced_actions = 0
        for action in actions:
            if (action.get('element', {}).get('surroundingText') or 
                action.get('element', {}).get('ariaLabel') or
                action.get('screenshots')):
                enhanced_actions += 1
        
        # print(f"   - Actions with enhanced data: {enhanced_actions}/{len(actions)}")
        # print(f"   - Enhancement coverage: {(enhanced_actions/len(actions)*100):.1f}%")
        
    except Exception as e:
        print(f"❌ Error during browser agent execution: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run the test."""
    if len(sys.argv) < 2:
        print("Usage: python test_browser_agent.py <recording_file.json> [task_description]")
        print("\nExample:")
        print("  python test_browser_agent.py my_recording.json")
        print("  python test_browser_agent.py my_recording.json 'Fill out the pizza order form'")
        return
    
    recording_file = sys.argv[1]
    task_description = sys.argv[2] if len(sys.argv) > 2 else None
    
    test_browser_agent(recording_file, task_description)

if __name__ == "__main__":
    main() 