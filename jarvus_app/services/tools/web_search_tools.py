"""Web Search and HTTP Request tool registrations for MCP server with automatic Chrome opening."""

import time
import re
from typing import TYPE_CHECKING
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_tool_result
from ..mcp_client import mcp_client
from ..chrome_service import chrome_control

if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def extract_urls_from_search_result(search_result):
    """Extract URLs from various search result formats."""
    urls = []
    
    if isinstance(search_result, dict):
        # Try different possible response structures
        if 'items' in search_result:
            items = search_result['items']
            for item in items:
                url = item.get('link') or item.get('url') or item.get('href')
                if url and url.startswith('http'):
                    urls.append({
                        'url': url,
                        'title': item.get('title', 'Unknown'),
                        'snippet': item.get('snippet', '')
                    })
        
        elif 'results' in search_result:
            results = search_result['results']
            for result in results:
                url = result.get('link') or result.get('url') or result.get('href')
                if url and url.startswith('http'):
                    urls.append({
                        'url': url,
                        'title': result.get('title', 'Unknown'),
                        'snippet': result.get('snippet', '')
                    })
    
    elif isinstance(search_result, str):
        # Simple URL extraction from text
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        found_urls = re.findall(url_pattern, search_result)
        for url in found_urls:
            urls.append({
                'url': url,
                'title': 'Article',
                'snippet': ''
            })
    
    return urls

def google_search_executor(tool_name, payload, jwt_token=None):
    """Enhanced Google search that automatically opens results in Chrome."""
    query = payload.get('parameters', {}).get('query')
    auto_open = payload.get('parameters', {}).get('auto_open', True)  # Default to True
    max_articles = payload.get('parameters', {}).get('max_articles', 3)
    
    print(f"🔍 Searching for: {query}")
    
    # Step 1: Perform the search
    body = {'mode': 'google', 'query': query}
    search_result = mcp_client.execute_tool(tool_name='search/google', payload=body, jwt_token=jwt_token)
    
    if not search_result or not isinstance(search_result, dict):
        return {"success": False, "error": "Search API returned invalid result"}
    
    # Step 2: Extract URLs from search results
    urls = extract_urls_from_search_result(search_result)
    
    if not urls:
        return {
            "success": False, 
            "error": "No URLs found in search results",
            "search_result": search_result
        }
    
    print(f"📰 Found {len(urls)} articles")
    
    # Step 3: Auto-open in Chrome if requested
    opened_urls = []
    if auto_open:
        # Check Chrome connection
        if not chrome_control.connect_to_chrome():
            return {
                "success": True,
                "query": query,
                "total_found": len(urls),
                "opened_count": 0,
                "opened_urls": [],
                "message": f"Found {len(urls)} articles for '{query}', but Chrome is not accessible. Make sure Chrome is running with --remote-debugging-port=9222",
                "found_urls": urls
            }
        
        # Open articles in Chrome
        for i, article in enumerate(urls[:max_articles]):
            url = article['url']
            title = article['title']
            
            print(f"🌐 Opening article {i+1}: {title[:50]}...")
            
            # Use new_tab=True to open each article in a new tab
            result = chrome_control.navigate_to_url(url, new_tab=True)
            if result.get("success"):
                opened_urls.append({
                    'url': url,
                    'title': title,
                    'status': 'opened'
                })
                print(f"   ✅ Opened: {title[:50]}...")
                time.sleep(2)  # Wait between openings
            else:
                opened_urls.append({
                    'url': url,
                    'title': title,
                    'status': 'failed',
                    'error': result.get('error')
                })
                print(f"   ❌ Failed to open: {result.get('error')}")
    
    # Return comprehensive result
    return {
        "success": True,
        "query": query,
        "total_found": len(urls),
        "opened_count": len([u for u in opened_urls if u['status'] == 'opened']),
        "opened_urls": opened_urls,
        "all_urls": urls,
        "message": f"Found {len(urls)} articles for '{query}'" + (f", opened {len([u for u in opened_urls if u['status'] == 'opened'])} in Chrome" if auto_open else "")
    }

def http_request_executor(tool_name, payload, jwt_token=None):
    """HTTP request executor (unchanged)."""
    params = payload.get('parameters', {})
    body = {'mode': 'http'}
    body.update(params)
    return mcp_client.execute_tool(tool_name='search/http', payload=body, jwt_token=jwt_token)

def register_web_search_tools(registry: 'ToolRegistry') -> None:
    """Register the Google Web Search and HTTP Request tools."""
    # Enhanced Google Custom Search tool with auto-open
    registry.register(ToolMetadata(
        name="google_web_search",
        description="Perform a web search using Google Custom Search and automatically open the results in Chrome browser.",
        category=ToolCategory.WEB,
        server_path="search/google",  # This should match the MCP server route
        requires_auth=False,
        parameters=[
            ToolParameter("query", "string", "Search query for Google Custom Search", required=True),
            ToolParameter("auto_open", "boolean", "Automatically open search results in Chrome (default: true)", required=False),
            ToolParameter("max_articles", "integer", "Maximum number of articles to open (default: 3)", required=False),
        ],
        result_formatter=format_tool_result,
        executor=google_search_executor
    ))

    # Direct HTTP Request tool
    registry.register(ToolMetadata(
        name="http_request",
        description="Send a direct HTTP request via the MCP server (GET, POST, etc.).",
        category=ToolCategory.WEB,
        server_path="search/http",  # This should match the MCP server route
        requires_auth=False,
        parameters=[
            ToolParameter("url", "string", "URL for direct HTTP request", required=True),
            ToolParameter("method", "string", "HTTP method for the request (default: GET)", required=False),
            ToolParameter("headers", "object", "Headers for the HTTP request", required=False),
            ToolParameter("body", "string", "Body for the HTTP request", required=False),
        ],
        result_formatter=format_tool_result,
        executor=http_request_executor
    )) 