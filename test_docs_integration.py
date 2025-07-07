#!/usr/bin/env python3
"""
Test script to verify Google Docs integration with Pipedream
"""

import os
import sys
import json

# Add the jarvus_app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvus_app'))

def test_environment_variables():
    """Test that required environment variables are set"""
    print("Testing Environment Variables...")
    print("=" * 50)
    
    required_vars = [
        "PIPEDREAM_DOCS_AUTH_URL",
        "PIPEDREAM_DOCS_CALLBACK_URL", 
        "PIPEDREAM_DOCS_ENDPOINT"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {missing_vars}")
        print("Please set these in your .env file")
    else:
        print("\n✅ All required environment variables are set!")
    
    return len(missing_vars) == 0

def test_oauth_model():
    """Test OAuth model functionality"""
    print("\nTesting OAuth Model...")
    print("=" * 50)
    
    try:
        from models.oauth import OAuthCredentials
        print("✅ OAuth model imported successfully")
        
        # Test model structure
        creds = OAuthCredentials(
            user_id="test_user",
            service="docs",
            connect_id="con_test123",
            state="test_state"
        )
        print("✅ OAuth model can be instantiated")
        
        # Test to_dict method
        creds_dict = creds.to_dict()
        expected_keys = ["id", "user_id", "service", "connect_id", "state", "created_at", "updated_at"]
        for key in expected_keys:
            if key in creds_dict:
                print(f"✅ to_dict() contains {key}")
            else:
                print(f"❌ to_dict() missing {key}")
        
        return True
        
    except Exception as e:
        print(f"❌ OAuth model test failed: {e}")
        return False

def test_tool_registry():
    """Test tool registry for docs tools"""
    print("\nTesting Tool Registry...")
    print("=" * 50)
    
    try:
        from services.tool_registry import tool_registry, ToolCategory
        
        # Check if docs tools are registered
        docs_tools = tool_registry.get_tools_by_category(ToolCategory.DOCS)
        print(f"✅ Found {len(docs_tools)} docs tools registered")
        
        # List some docs tools
        docs_tool_names = [tool.function.name for tool in docs_tools[:5]]
        print(f"Sample docs tools: {docs_tool_names}")
        
        return len(docs_tools) > 0
        
    except Exception as e:
        print(f"❌ Tool registry test failed: {e}")
        return False

def test_mcp_client():
    """Test MCP client Pipedream routing"""
    print("\nTesting MCP Client...")
    print("=" * 50)
    
    try:
        from services.mcp_client import MCPClient
        
        # Create test client
        client = MCPClient()
        print("✅ MCP client created successfully")
        
        # Test Pipedream endpoints configuration
        pipedream_endpoints = client.pipedream_endpoints
        print(f"✅ Pipedream endpoints configured: {list(pipedream_endpoints.keys())}")
        
        # Test docs endpoint
        docs_endpoint = pipedream_endpoints.get("docs")
        if docs_endpoint:
            print(f"✅ Docs endpoint: {docs_endpoint}")
        else:
            print("❌ Docs endpoint not configured")
        
        return docs_endpoint is not None
        
    except Exception as e:
        print(f"❌ MCP client test failed: {e}")
        return False

def test_tool_permissions():
    """Test tool permissions functionality"""
    print("\nTesting Tool Permissions...")
    print("=" * 50)
    
    try:
        from utils.tool_permissions import TOOLS, get_connected_services
        
        # Check if docs is in TOOLS
        if "docs" in TOOLS:
            print(f"✅ Docs tool defined: {TOOLS['docs']}")
        else:
            print("❌ Docs tool not defined in TOOLS")
        
        # Test get_connected_services function structure
        services = get_connected_services("test_user")
        if "docs" in services:
            print("✅ get_connected_services includes docs")
        else:
            print("❌ get_connected_services missing docs")
        
        return "docs" in TOOLS and "docs" in services
        
    except Exception as e:
        print(f"❌ Tool permissions test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Google Docs Integration with Pipedream")
    print("=" * 60)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("OAuth Model", test_oauth_model),
        ("Tool Registry", test_tool_registry),
        ("MCP Client", test_mcp_client),
        ("Tool Permissions", test_tool_permissions),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Docs integration is ready.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 