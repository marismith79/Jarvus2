#!/usr/bin/env python3
"""
Test script to verify OAuth callback URL is working
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_callback_url():
    """Test that the callback URL is accessible"""
    print("🔍 Testing OAuth callback URL accessibility...")
    
    base_url = "http://localhost:5001"
    callback_url = f"{base_url}/pipedream/callback/docs"
    
    print(f"Testing callback URL: {callback_url}")
    
    try:
        # Test with a simple GET request (this will fail auth but we can see if the route exists)
        response = requests.get(callback_url, timeout=5)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 302:  # Redirect to login
            print("✅ Callback URL exists and redirects to login (expected)")
            return True
        elif response.status_code == 200:
            print("✅ Callback URL is accessible")
            return True
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to localhost:5001 - is the Flask app running?")
        return False
    except Exception as e:
        print(f"❌ Error testing callback URL: {e}")
        return False

def test_connect_url():
    """Test that the connect URL is accessible"""
    print("\n🔍 Testing OAuth connect URL accessibility...")
    
    base_url = "http://localhost:5001"
    connect_url = f"{base_url}/connect/docs"
    
    print(f"Testing connect URL: {connect_url}")
    
    try:
        # Test with a simple GET request (this will fail auth but we can see if the route exists)
        response = requests.get(connect_url, timeout=5)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 302:  # Redirect to login
            print("✅ Connect URL exists and redirects to login (expected)")
            return True
        elif response.status_code == 200:
            print("✅ Connect URL is accessible")
            return True
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to localhost:5001 - is the Flask app running?")
        return False
    except Exception as e:
        print(f"❌ Error testing connect URL: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing OAuth URL Accessibility")
    print("=" * 50)
    
    tests = [
        ("Callback URL", test_callback_url),
        ("Connect URL", test_connect_url)
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
        print("🎉 All tests passed! OAuth URLs are accessible.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 