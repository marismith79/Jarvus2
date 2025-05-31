import sys
import time
sys.path.insert(0, '/app')
from services.browser_service import BrowserService

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

if __name__ == "__main__":
    test_browser_tools() 