#!/usr/bin/env python3
"""
Test script to verify tool discovery optimization.
This script tests that subsequent calls to ensure_tools_discovered() don't trigger rediscovery.
"""

import sys
import os
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jarvus_app.services.pipedream_tool_registry import pipedream_tool_service, ensure_tools_discovered

def test_tool_discovery_optimization():
    """Test that tool discovery is optimized and doesn't repeat unnecessarily."""
    
    print("=== Testing Tool Discovery Optimization ===")
    
    # Test user ID
    test_user_id = "test_user_123"
    
    print(f"\n1. First call to ensure_tools_discovered() for user {test_user_id}")
    start_time = time.time()
    ensure_tools_discovered(test_user_id)
    first_call_time = time.time() - start_time
    print(f"   First call completed in {first_call_time:.2f} seconds")
    
    print(f"\n2. Checking if tools are initialized...")
    is_initialized = pipedream_tool_service.is_initialized()
    status = pipedream_tool_service.get_initialization_status()
    print(f"   Tools initialized: {is_initialized}")
    print(f"   Status: {status}")
    
    print(f"\n3. Second call to ensure_tools_discovered() for user {test_user_id}")
    start_time = time.time()
    ensure_tools_discovered(test_user_id)
    second_call_time = time.time() - start_time
    print(f"   Second call completed in {second_call_time:.2f} seconds")
    
    print(f"\n4. Third call to ensure_tools_discovered() for user {test_user_id}")
    start_time = time.time()
    ensure_tools_discovered(test_user_id)
    third_call_time = time.time() - start_time
    print(f"   Third call completed in {third_call_time:.2f} seconds")
    
    print(f"\n=== Results ===")
    print(f"First call time:  {first_call_time:.2f} seconds")
    print(f"Second call time: {second_call_time:.2f} seconds")
    print(f"Third call time:  {third_call_time:.2f} seconds")
    
    # Check if optimization is working
    if second_call_time < first_call_time * 0.1:  # Second call should be much faster
        print(f"✅ Optimization working: Second call was {first_call_time/second_call_time:.1f}x faster")
    else:
        print(f"❌ Optimization not working: Second call was only {first_call_time/second_call_time:.1f}x faster")
    
    if third_call_time < first_call_time * 0.1:  # Third call should also be much faster
        print(f"✅ Optimization working: Third call was {first_call_time/third_call_time:.1f}x faster")
    else:
        print(f"❌ Optimization not working: Third call was only {first_call_time/third_call_time:.1f}x faster")
    
    print(f"\n5. Testing force refresh...")
    start_time = time.time()
    ensure_tools_discovered(test_user_id, force_refresh=True)
    force_refresh_time = time.time() - start_time
    print(f"   Force refresh completed in {force_refresh_time:.2f} seconds")
    
    print(f"\n6. Testing reset and rediscovery...")
    pipedream_tool_service.reset_initialization()
    start_time = time.time()
    ensure_tools_discovered(test_user_id)
    reset_call_time = time.time() - start_time
    print(f"   Reset and rediscovery completed in {reset_call_time:.2f} seconds")
    
    print(f"\n=== Final Results ===")
    print(f"Initial discovery: {first_call_time:.2f} seconds")
    print(f"Cached calls:      {second_call_time:.2f} seconds")
    print(f"Force refresh:     {force_refresh_time:.2f} seconds")
    print(f"Reset discovery:   {reset_call_time:.2f} seconds")

if __name__ == "__main__":
    test_tool_discovery_optimization() 