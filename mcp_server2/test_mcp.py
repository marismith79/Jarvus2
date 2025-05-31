import sys
import time
import json
sys.path.insert(0, '/app')
from services.browser_service import BrowserService
from base64 import b64decode

def test_browser_tools():
    browser_service = BrowserService()
    session_id = "test-session"

    # 1. Create a browser session
    driver = browser_service.create_driver(session_id)
    print("Session created.")

    try:
        # 2. Navigate to a page
        result = browser_service.execute_action(session_id, {
            "type": "navigate",
            "params": {"url": "https://example.com"}
        })
        print("Navigate:", result)
        assert result["status"] == "success"

        # 3. Get page title
        result = browser_service.execute_action(session_id, {
            "type": "get_title",
            "params": {}
        })
        print("Title:", result)
        assert "Example Domain" in result["title"]

        # 4. Find element by CSS selector
        result = browser_service.execute_action(session_id, {
            "type": "find_element",
            "params": {"by": "css", "value": "h1"}
        })
        print("Find element:", result)
        assert result["status"] == "success"

        # 5. Execute JavaScript
        result = browser_service.execute_action(session_id, {
            "type": "execute_script",
            "params": {"script": "return document.title;"}
        })
        print("Execute script:", result)
        assert "Example Domain" in result["result"]

        # 6. Screenshot
        result = browser_service.execute_action(session_id, {
            "type": "screenshot",
            "params": {}
        })
        print("Screenshot:", "success" if result["status"] == "success" else "failed")
        assert result["status"] == "success"

        # 7. Open a new tab
        result = browser_service.execute_action(session_id, {
            "type": "new_tab",
            "params": {}
        })
        print("New tab:", result)
        assert result["status"] == "success"

        # 8. Get window handles
        result = browser_service.execute_action(session_id, {
            "type": "get_window_handles",
            "params": {}
        })
        print("Window handles:", result)
        assert result["status"] == "success"
        assert isinstance(result["handles"], list)

    finally:
        # Cleanup
        browser_service.cleanup(session_id)
        print("Session cleaned up.")

def test_dictionary_com_screenshot():
    browser_service = BrowserService()
    session_id = "dictionary-screenshot"
    driver = browser_service.create_driver(session_id)
    try:
        # Navigate to dictionary.com
        browser_service.execute_action(session_id, {
            "type": "navigate",
            "params": {"url": "https://www.dictionary.com/"}
        })
        # Take screenshot
        result = browser_service.execute_action(session_id, {
            "type": "screenshot",
            "params": {}
        })
        if result["status"] == "success":
            screenshot_data = result["screenshot"]
            file_path = "dictionary_com_screenshot.png"
            with open(file_path, "wb") as f:
                f.write(b64decode(screenshot_data))
            print(f"Screenshot saved to {file_path}")
        else:
            print("Failed to take screenshot:", result.get("message"))
    finally:
        browser_service.cleanup(session_id)
        print("Session cleaned up.")

def test_advanced_features():
    browser_service = BrowserService()
    session_id = "advanced-features-test"
    driver = browser_service.create_driver(session_id)
    
    try:
        # 1. Test performance monitoring
        print("\nTesting Performance Monitoring:")
        browser_service.execute_action(session_id, {
            "type": "start_performance_monitoring",
            "params": {}
        })
        
        # Navigate to a page
        browser_service.execute_action(session_id, {
            "type": "navigate",
            "params": {"url": "https://example.com"}
        })
        
        # Get performance metrics
        metrics = browser_service.execute_action(session_id, {
            "type": "get_performance_metrics",
            "params": {}
        })
        print("Performance Metrics:", metrics)
        
        # 2. Test network conditions
        print("\nTesting Network Conditions:")
        browser_service.execute_action(session_id, {
            "type": "set_network_conditions",
            "params": {
                "offline": False,
                "latency": 100,  # 100ms latency
                "download_throughput": 1024 * 1024,  # 1MB/s
                "upload_throughput": 1024 * 1024,  # 1MB/s
                "connection_type": "4G"
            }
        })
        
        # Navigate to test network conditions
        browser_service.execute_action(session_id, {
            "type": "navigate",
            "params": {"url": "https://example.com"}
        })
        
        # 3. Test relative locators
        print("\nTesting Relative Locators:")
        # First, navigate to a page with a form
        browser_service.execute_action(session_id, {
            "type": "navigate",
            "params": {"url": "https://example.com"}
        })
        
        # Find an element relative to another
        result = browser_service.execute_action(session_id, {
            "type": "find_element_relative",
            "params": {
                "base_by": "css",
                "base_value": "h1",
                "position": "below",
                "target_by": "css",
                "target_value": "p"
            }
        })
        print("Relative Element:", result)
        
    finally:
        browser_service.cleanup(session_id)
        print("Session cleaned up.")

def test_performance_metrics():
    browser_service = BrowserService()
    session_id = "performance-test"
    driver = browser_service.create_driver(session_id)
    
    try:
        print("\n=== Performance Testing ===")
        
        # 1. Test under normal conditions
        print("\n1. Testing under normal conditions:")
        browser_service.execute_action(session_id, {
            "type": "start_performance_monitoring",
            "params": {}
        })
        
        browser_service.execute_action(session_id, {
            "type": "navigate",
            "params": {"url": "https://example.com"}
        })
        
        normal_metrics = browser_service.execute_action(session_id, {
            "type": "get_performance_metrics",
            "params": {}
        })
        print("Normal conditions metrics:", json.dumps(normal_metrics, indent=2))
        
        # After retrieving normal conditions metrics:
        with open("performance_metrics_normal.json", "w") as f:
            json.dump(normal_metrics, f, indent=2)
        
        # 2. Test under 3G conditions
        print("\n2. Testing under 3G conditions:")
        browser_service.execute_action(session_id, {
            "type": "set_network_conditions",
            "params": {
                "offline": False,
                "latency": 200,  # 200ms latency
                "download_throughput": 750 * 1024,  # 750KB/s
                "upload_throughput": 250 * 1024,  # 250KB/s
                "connection_type": "3G"
            }
        })
        
        browser_service.execute_action(session_id, {
            "type": "start_performance_monitoring",
            "params": {}
        })
        
        browser_service.execute_action(session_id, {
            "type": "navigate",
            "params": {"url": "https://example.com"}
        })
        
        three_g_metrics = browser_service.execute_action(session_id, {
            "type": "get_performance_metrics",
            "params": {}
        })
        print("3G conditions metrics:", json.dumps(three_g_metrics, indent=2))
        
        # After retrieving 3G conditions metrics:
        with open("performance_metrics_3g.json", "w") as f:
            json.dump(three_g_metrics, f, indent=2)
        
        # 3. Test under 2G conditions
        print("\n3. Testing under 2G conditions:")
        browser_service.execute_action(session_id, {
            "type": "set_network_conditions",
            "params": {
                "offline": False,
                "latency": 300,  # 300ms latency
                "download_throughput": 250 * 1024,  # 250KB/s
                "upload_throughput": 50 * 1024,  # 50KB/s
                "connection_type": "2G"
            }
        })
        
        browser_service.execute_action(session_id, {
            "type": "start_performance_monitoring",
            "params": {}
        })
        
        browser_service.execute_action(session_id, {
            "type": "navigate",
            "params": {"url": "https://example.com"}
        })
        
        two_g_metrics = browser_service.execute_action(session_id, {
            "type": "get_performance_metrics",
            "params": {}
        })
        print("2G conditions metrics:", json.dumps(two_g_metrics, indent=2))
        
        # After retrieving 2G conditions metrics:
        with open("performance_metrics_2g.json", "w") as f:
            json.dump(two_g_metrics, f, indent=2)
        
        # 4. Compare metrics
        print("\n4. Performance Comparison:")
        print(f"Normal conditions duration: {normal_metrics['metrics']['duration']:.2f}s")
        print(f"3G conditions duration: {three_g_metrics['metrics']['duration']:.2f}s")
        print(f"2G conditions duration: {two_g_metrics['metrics']['duration']:.2f}s")
        
    except Exception as e:
        print(f"Test failed: {e}")
        driver.save_screenshot("test_failure_screenshot.png")
        raise
    finally:
        browser_service.cleanup(session_id)
        print("\nSession cleaned up.")

if __name__ == "__main__":
    test_browser_tools()
    test_dictionary_com_screenshot()
    test_advanced_features()
    test_performance_metrics() 