"""Web browsing tool registrations."""

import asyncio
import json
import time
import base64
from typing import TYPE_CHECKING, Dict, Any, List, Optional
from ..tool_registry import ToolMetadata, ToolParameter, ToolCategory, format_tool_result
from dotenv import load_dotenv
load_dotenv()
        
if TYPE_CHECKING:
    from ..tool_registry import ToolRegistry

def format_recorded_actions(actions: List[Dict]) -> str:
    """Format recorded actions into a readable context string."""
    if not actions:
        return ""
    
    context = "RECORDED USER ACTIONS (SEQUENTIAL):\n"
    context += f"URL: {actions[0].get('url', 'Unknown')}\n"
    context += f"Total actions: {len(actions)}\n\n"
    
    for action in actions:
        context += f"Step {action.get('sequence', '?')}: {action['type'].upper()}\n"
        
        element = action.get('element', {})
        if element.get('tagName'):
            context += f"  Element: {element['tagName']}"
            if element.get('id'):
                context += f" (id: {element['id']})"
            if element.get('className'):
                context += f" (class: {element['className']})"
            context += "\n"
        
        # Enhanced element context
        if element.get('surroundingText'):
            surrounding = element['surroundingText']
            if surrounding.get('elementText'):
                context += f"  Element Text: {surrounding['elementText']}\n"
            if surrounding.get('parentText'):
                context += f"  Parent Context: {surrounding['parentText']}\n"
        
        if element.get('ariaLabel'):
            context += f"  Aria Label: {element['ariaLabel']}\n"
        
        if element.get('role'):
            context += f"  Role: {element['role']}\n"
        
        if element.get('isVisible') is not None:
            context += f"  Visible: {element['isVisible']}\n"
        
        if element.get('textContent'):
            context += f"  Text: {element['textContent']}\n"
        
        if element.get('value'):
            context += f"  Value: {element['value']}\n"
        
        if element.get('xpath'):
            context += f"  XPath: {element['xpath']}\n"
        
        # Handle enhanced screenshots
        screenshots = action.get('screenshots', {})
        if screenshots:
            context += f"  Screenshots:\n"
            
            if 'beforeAction' in screenshots:
                before = screenshots['beforeAction']
                if before.get('data'):
                    context += f"    Before Action: Full window captured ({before['filename']})\n"
                    context += f"    Window size: {before['windowSize']['width']}x{before['windowSize']['height']}\n"
                elif before.get('fallback'):
                    context += f"    Before Action: Element at ({before['x']}, {before['y']}) size {before['width']}x{before['height']}\n"
            
            if 'afterAction' in screenshots:
                after = screenshots['afterAction']
                if after.get('data'):
                    context += f"    After Action: Full window captured ({after['filename']})\n"
                    context += f"    Window size: {after['windowSize']['width']}x{after['windowSize']['height']}\n"
                elif after.get('fallback'):
                    context += f"    After Action: Element at ({after['x']}, {after['y']}) size {after['width']}x{after['height']}\n"
            
            if 'elementScreenshot' in screenshots:
                element_screenshot = screenshots['elementScreenshot']
                if element_screenshot.get('data'):
                    context += f"    Element Screenshot: {element_screenshot['filename']}\n"
                    context += f"    Element size: {element_screenshot['elementSize']['width']}x{element_screenshot['elementSize']['height']}\n"
        
        # Page state information
        page_state = action.get('pageState', {})
        if page_state:
            if 'beforeAction' in page_state:
                before_state = page_state['beforeAction']
                context += f"  Page State Before:\n"
                context += f"    URL: {before_state.get('url', 'Unknown')}\n"
                context += f"    Title: {before_state.get('title', 'Unknown')}\n"
                if before_state.get('errors'):
                    context += f"    Errors: {len(before_state['errors'])} errors detected\n"
            
            if 'afterAction' in page_state:
                after_state = page_state['afterAction']
                context += f"  Page State After:\n"
                context += f"    URL: {after_state.get('url', 'Unknown')}\n"
                context += f"    Title: {after_state.get('title', 'Unknown')}\n"
                if after_state.get('newElements'):
                    context += f"    New Elements: {len(after_state['newElements'])} elements added\n"
                if after_state.get('errors'):
                    context += f"    Errors: {len(after_state['errors'])} errors detected\n"
        
        # Browser context
        browser_context = action.get('browserContext', {})
        if browser_context:
            context += f"  Browser Context:\n"
            context += f"    Window Size: {browser_context.get('windowSize', {}).get('width', 'Unknown')}x{browser_context.get('windowSize', {}).get('height', 'Unknown')}\n"
            context += f"    Scroll Position: ({browser_context.get('scrollPosition', {}).get('x', 0)}, {browser_context.get('scrollPosition', {}).get('y', 0)})\n"
            context += f"    Viewport: {browser_context.get('viewport', {}).get('width', 'Unknown')}x{browser_context.get('viewport', {}).get('height', 'Unknown')}\n"
        
        context += "\n"
    
    return context

def format_single_action(action: Dict, step_number: int) -> str:
    """Format a single action for inclusion in examples."""
    formatted = f"  Step {step_number}: {action['type'].upper()}\n"
    
    element = action.get('element', {})
    if element.get('tagName'):
        formatted += f"    Element: {element['tagName']}"
        if element.get('id'):
            formatted += f" (id: {element['id']})"
        if element.get('className'):
            formatted += f" (class: {element['className']})"
        formatted += "\n"
    
    # Enhanced element context
    if element.get('surroundingText'):
        surrounding = element['surroundingText']
        if surrounding.get('elementText'):
            formatted += f"    Element Text: {surrounding['elementText']}\n"
        if surrounding.get('parentText'):
            formatted += f"    Parent Context: {surrounding['parentText']}\n"
    
    if element.get('ariaLabel'):
        formatted += f"    Aria Label: {element['ariaLabel']}\n"
    
    if element.get('role'):
        formatted += f"    Role: {element['role']}\n"
    
    if element.get('isVisible') is not None:
        formatted += f"    Visible: {element['isVisible']}\n"
    
    if element.get('textContent'):
        formatted += f"    Text: {element['textContent']}\n"
    
    if element.get('value'):
        formatted += f"    Value: {element['value']}\n"
    
    if element.get('xpath'):
        formatted += f"    XPath: {element['xpath']}\n"
    
    # Handle enhanced screenshots
    screenshots = action.get('screenshots', {})
    if screenshots:
        formatted += f"    Screenshots:\n"
        
        if 'beforeAction' in screenshots and screenshots['beforeAction'] is not None:
            before = screenshots['beforeAction']
            if before.get('data'):
                formatted += f"      Before Action: Full window captured ({before['filename']})\n"
                formatted += f"      Window size: {before['windowSize']['width']}x{before['windowSize']['height']}\n"
            elif before.get('fallback'):
                formatted += f"      Before Action: Element at ({before['x']}, {before['y']}) size {before['width']}x{before['height']}\n"
        
        if 'afterAction' in screenshots and screenshots['afterAction'] is not None:
            after = screenshots['afterAction']
            if after.get('data'):
                formatted += f"      After Action: Full window captured ({after['filename']})\n"
                formatted += f"      Window size: {after['windowSize']['width']}x{after['windowSize']['height']}\n"
            elif after.get('fallback'):
                formatted += f"      After Action: Element at ({after['x']}, {after['y']}) size {after['width']}x{after['height']}\n"
        
        if 'elementScreenshot' in screenshots and screenshots['elementScreenshot'] is not None:
            element_screenshot = screenshots['elementScreenshot']
            if element_screenshot.get('data'):
                formatted += f"      Element Screenshot: {element_screenshot['filename']}\n"
                formatted += f"      Element size: {element_screenshot['elementSize']['width']}x{element_screenshot['elementSize']['height']}\n"
    
    # Page state information
    page_state = action.get('pageState', {})
    if page_state:
        if 'beforeAction' in page_state:
            before_state = page_state['beforeAction']
            formatted += f"    Page State Before:\n"
            formatted += f"      URL: {before_state.get('url', 'Unknown')}\n"
            formatted += f"      Title: {before_state.get('title', 'Unknown')}\n"
            if before_state.get('errors'):
                formatted += f"      Errors: {len(before_state['errors'])} errors detected\n"
        
        if 'afterAction' in page_state:
            after_state = page_state['afterAction']
            formatted += f"    Page State After:\n"
            formatted += f"      URL: {after_state.get('url', 'Unknown')}\n"
            formatted += f"      Title: {after_state.get('title', 'Unknown')}\n"
            if after_state.get('newElements'):
                formatted += f"      New Elements: {len(after_state['newElements'])} elements added\n"
            if after_state.get('errors'):
                formatted += f"      Errors: {len(after_state['errors'])} errors detected\n"
    
    # Browser context
    browser_context = action.get('browserContext', {})
    if browser_context:
        formatted += f"    Browser Context:\n"
        formatted += f"      Window Size: {browser_context.get('windowSize', {}).get('width', 'Unknown')}x{browser_context.get('windowSize', {}).get('height', 'Unknown')}\n"
        formatted += f"      Scroll Position: ({browser_context.get('scrollPosition', {}).get('x', 0)}, {browser_context.get('scrollPosition', {}).get('y', 0)})\n"
        formatted += f"      Viewport: {browser_context.get('viewport', {}).get('width', 'Unknown')}x{browser_context.get('viewport', {}).get('height', 'Unknown')}\n"
    
    formatted += "\n"
    return formatted

async def execute_web_browse(task: str, context: Optional[str] = None, examples: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """Execute the web browsing agent with the given task and optional context/examples."""
    start_time = time.time()
    print(f"🔍 Starting web browse execution for task: {task}")
    print(f"⏱️  Action started at: {time.strftime('%H:%M:%S', time.localtime(start_time))}")
    
    if context:
        print(f"📋 Context provided: {len(context)} characters")
    if examples:
        print(f"📚 Examples provided: {len(examples)} examples")
        
        # Count different types of data in examples
        screenshot_count = 0
        enhanced_element_count = 0
        page_state_count = 0
        
        for example in examples:
            actions = example.get('actions', [])
            for action in actions:
                screenshots = action.get('screenshots', {})
                if screenshots:
                    screenshot_count += len(screenshots)
                
                element = action.get('element', {})
                if element.get('surroundingText') or element.get('ariaLabel') or element.get('role'):
                    enhanced_element_count += 1
                
                if action.get('pageState'):
                    page_state_count += 1
        
        print(f"📸 Screenshots captured: {screenshot_count} (before/after/element)")
        print(f"🔍 Enhanced elements: {enhanced_element_count} with context/accessibility data")
        print(f"📄 Page state tracking: {page_state_count} actions with state changes")
        
        # Count unique URLs across all examples
        all_urls = set()
        for example in examples:
            actions = example.get('actions', [])
            for action in actions:
                if action.get('url'):
                    all_urls.add(action['url'])
        print(f"🌐 URLs visited: {len(all_urls)} unique pages")
    
    try:
        # Import browser-use here to avoid import errors at module level
        from browser_use import Agent
        from browser_use.llm import ChatOpenAI
        from browser_use.browser.session import BrowserSession
        
        print("🔍 Creating browser agent...")
        
        # Build enhanced task with context and examples
        enhanced_task = task
        
        if context:
            enhanced_task = f"CONTEXT:\n{context}\n\nTASK:\n{task}"
        
        if examples:
            enhanced_task += "\n\nEXAMPLES OF SIMILAR TASKS:\n"
            for i, example in enumerate(examples, 1):
                enhanced_task += f"\nExample {i}:\n"
                enhanced_task += f"Task: {example.get('task', '')}\n"
                
                # Format the recorded actions as steps
                actions = example.get('actions', [])
                if actions:
                    enhanced_task += f"Steps:\n"
                    for j, action in enumerate(actions, 1):
                        enhanced_task += format_single_action(action, j)
                
                if example.get('result'):
                    enhanced_task += f"Result: {example['result']}\n"
        
        # Create a headless browser session with unique profile
        import tempfile
        import uuid
        
        # Create unique profile directory for this session
        unique_profile_dir = f"/tmp/browser_use_profile_{uuid.uuid4().hex[:8]}"
        
        # Disable deterministic rendering for faster performance
        browser_args = [
            '--disable-css',
            '--disable-stylesheets',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ]
        
        browser_session = BrowserSession(
            headless=True,
            viewport={"width": 1920, "height": 1080},
            user_data_dir=unique_profile_dir,
            browser_args=browser_args
        )
        
        agent = Agent(
            task=enhanced_task,
            llm=ChatOpenAI(model="gpt-4o"),
            browser_session=browser_session
        )
        print("🔍 Running browser agent...")
        result = await agent.run()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"🔍 Browser agent completed with result: {result}")
        print(f"⏱️  Action completed at: {time.strftime('%H:%M:%S', time.localtime(end_time))}")
        print(f"⏱️  Total execution time: {execution_time:.2f} seconds")
        
        return {
            "success": True, 
            "result": str(result),
            "timing": {
                "start_time": time.strftime('%H:%M:%S', time.localtime(start_time)),
                "end_time": time.strftime('%H:%M:%S', time.localtime(end_time)),
                "execution_time_seconds": round(execution_time, 2),
                "execution_time_formatted": f"{execution_time:.2f} seconds"
            }
        }
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"❌ Browser agent failed with error: {str(e)}")
        print(f"⏱️  Action failed at: {time.strftime('%H:%M:%S', time.localtime(end_time))}")
        print(f"⏱️  Time before failure: {execution_time:.2f} seconds")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False, 
            "error": str(e),
            "timing": {
                "start_time": time.strftime('%H:%M:%S', time.localtime(start_time)),
                "end_time": time.strftime('%H:%M:%S', time.localtime(end_time)),
                "execution_time_seconds": round(execution_time, 2),
                "execution_time_formatted": f"{execution_time:.2f} seconds",
                "status": "failed"
            }
        }

def web_browse_executor(tool_name: str, payload: Dict[str, Any], jwt_token: str = None) -> Any:
    """Executor function for web browsing tools that handles async execution."""
    executor_start_time = time.time()
    print(f"🔍 Web browse executor called with tool_name: {tool_name}, payload: {payload}")
    print(f"⏱️  Executor started at: {time.strftime('%H:%M:%S', time.localtime(executor_start_time))}")
    
    # The tool_name will be "web" (server_path), but we need to check for web_browse operation
    if tool_name == "web":
        # Extract parameters from the payload structure expected by MCP client
        operation = payload.get("operation", "")
        parameters = payload.get("parameters", {})
        
        # Only handle web_browse operations
        if operation == "web_browse":
            task = parameters.get("task", "")
            context = parameters.get("context", None)
            examples = parameters.get("examples", None)
            
            # Backward compatibility: convert recorded_actions to examples format
            if parameters.get("recorded_actions") and not examples:
                recorded_actions = parameters["recorded_actions"]
                print(f"🔄 Converting recorded_actions to examples format for backward compatibility")
                
                # If it's the full extension export format, convert it properly
                if isinstance(recorded_actions, dict) and 'actions' in recorded_actions:
                    examples = convert_chrome_extension_to_examples(recorded_actions)
                else:
                    # If it's just the actions array, wrap it
                    examples = [{
                        "task": task,
                        "actions": recorded_actions,
                        "result": "Workflow completed successfully"
                    }]
                
                print(f"📚 Converted to {len(examples)} example(s)")
            
            if not task:
                return {"success": False, "error": "Task parameter is required"}
            
            print(f"🔍 Web browse executor processing task: {task}")
            if context:
                print(f"📋 Context provided: {len(context)} characters")
            if examples:
                print(f"📚 Examples provided: {len(examples)} examples")
            
            # Run the async function in a new event loop
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(execute_web_browse(task, context, examples))
                loop.close()
                
                executor_end_time = time.time()
                total_executor_time = executor_end_time - executor_start_time
                
                print(f"🔍 Web browse executor returning result: {result}")
                print(f"⏱️  Total executor time (including async overhead): {total_executor_time:.2f} seconds")
                
                # Add executor timing to the result
                if isinstance(result, dict) and "timing" in result:
                    result["timing"]["total_executor_time_seconds"] = round(total_executor_time, 2)
                    result["timing"]["total_executor_time_formatted"] = f"{total_executor_time:.2f} seconds"
                
                return result
            except Exception as e:
                executor_end_time = time.time()
                total_executor_time = executor_end_time - executor_start_time
                
                error_result = {
                    "success": False, 
                    "error": f"Failed to execute web browse: {str(e)}",
                    "timing": {
                        "start_time": time.strftime('%H:%M:%S', time.localtime(executor_start_time)),
                        "end_time": time.strftime('%H:%M:%S', time.localtime(executor_end_time)),
                        "total_executor_time_seconds": round(total_executor_time, 2),
                        "total_executor_time_formatted": f"{total_executor_time:.2f} seconds",
                        "status": "failed"
                    }
                }
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
        description="Call a web browsing agent to browse the web to complete a specific task. Supports context and examples with enhanced action data (screenshots, element context, page state) for improved performance.",
        category=ToolCategory.WEB,
        server_path="web",
        requires_auth=False,
        parameters=[
            ToolParameter("task", "string", "Task that the web browsing agent should complete", required=True),
            ToolParameter("context", "string", "Additional context or instructions for the task", required=False),
            ToolParameter("examples", "array", "List of example tasks with actions, screenshots, and results", required=False, items_type="object"),
        ],
        result_formatter=format_tool_result,
        executor=web_browse_executor
    ))
    
    print("✅ Web tools registered successfully")

def convert_chrome_extension_to_examples(extension_export: Dict) -> List[Dict]:
    """Convert Chrome extension export format to examples format for browser-use."""
    if not extension_export or 'actions' not in extension_export:
        return []
    
    # Extract session info
    session = extension_export.get('recordingSession', {})
    start_time = session.get('startTime', 0)
    end_time = session.get('endTime', 0)
    duration = session.get('duration', 0)
    
    # Create example from recorded actions
    example = {
        "task": f"Complete the recorded workflow ({duration}ms duration)",
        "actions": extension_export['actions'],
        "result": "Workflow completed successfully",
        "metadata": {
            "recording_session": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": duration,
                "total_actions": len(extension_export['actions'])
            }
        }
    }
    
    return [example] 