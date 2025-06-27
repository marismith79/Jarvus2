"""Web browsing tool registrations."""

import asyncio
import json
from typing import TYPE_CHECKING, Dict, Any
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_tool_result
from dotenv import load_dotenv
load_dotenv()
        
if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

async def execute_web_browse(task: str) -> Dict[str, Any]:
    """Execute the web browsing agent with the given task."""
    print(f"🔍 Starting web browse execution for task: {task}")
    try:
        # Import browser-use here to avoid import errors at module level
        from browser_use import Agent
        from browser_use.llm import ChatOpenAI
        
        print("🔍 Creating browser agent...")
        agent = Agent(
            task=task,
            llm=ChatOpenAI(model="gpt-4o"),
        )
        print("🔍 Running browser agent...")
        result = await agent.run()
        print(f"🔍 Browser agent completed with result: {result}")
        return {"success": True, "result": str(result)}
    except Exception as e:
        print(f"❌ Browser agent failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def web_browse_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor function for web browsing tools that handles async execution."""
    print(f"🔍 Web browse executor called with tool_name: {tool_name}, payload: {payload}")
    
    # The tool_name will be "web" (server_path), but we need to check for web_browse operation
    if tool_name == "web":
        # Extract parameters from the payload structure expected by MCP client
        operation = payload.get("operation", "")
        parameters = payload.get("parameters", {})
        
        # Only handle web_browse operations
        if operation == "web_browse":
            task = parameters.get("task", "")
            if not task:
                return {"success": False, "error": "Task parameter is required"}
            
            print(f"🔍 Web browse executor processing task: {task}")
            
            # Run the async function in a new event loop
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(execute_web_browse(task))
                loop.close()
                print(f"🔍 Web browse executor returning result: {result}")
                return result
            except Exception as e:
                error_result = {"success": False, "error": f"Failed to execute web browse: {str(e)}"}
                print(f"❌ Web browse executor failed: {error_result}")
                return error_result
        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}
    
    return {"success": False, "error": f"Unknown tool: {tool_name}"}

def register_web_tools(registry: 'ToolRegistry') -> None:
    """Register all web browsing-related tools."""
    print("🔧 Registering web tools...")
    
    registry.register(ToolMetadata(
        name="web_browse",
        description="Call a web browsing agent to browse the web to complete a specific task",
        category=ToolCategory.WEB,
        server_path="web",
        requires_auth=False,
        parameters=[
            ToolParameter("task", "string", "Task that the web browsing agent should complete", required=True),
        ],
        result_formatter=format_tool_result,
        executor=web_browse_executor
    ))
    
    print("✅ Web tools registered successfully") 