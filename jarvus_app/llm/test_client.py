"""
Test script for verifying the OpenAI client functionality with MCP server integration.
Run this script directly to test the client: python -m jarvus_app.llm.test_client
"""

from .client import OpenAIClient

def test_basic_chat():
    """Test basic chat functionality with the OpenAI client."""
    try:
        # Initialize the client
        client = OpenAIClient()
        
        # Create a simple conversation
        messages = [
            client.format_message("system", "You are a helpful assistant."),
            client.format_message("user", "Hello! Can you tell me what 2+2 is?")
        ]
        
        # Get response from OpenAI
        response = client.create_chat_completion(messages)
        
        # Print the response
        print("\nTest Results:")
        print("-------------")
        print("User: Hello! Can you tell me what 2+2 is?")
        print(f"Assistant: {response.choices[0].message.content}")
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"\nError during test: {str(e)}")
        raise

def test_mcp_integration():
    """Test LLM's ability to use MCP server tools."""
    try:
        # Initialize the client
        client = OpenAIClient()
        
        # Define available tools (MCP server endpoints)
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "mcp_execute_command",
                    "description": "Execute a command on the MCP server",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The command to execute"
                            }
                        },
                        "required": ["command"]
                    }
                }
            }
        ]
        
        # Create a conversation that should trigger tool usage
        messages = [
            client.format_message("system", "You are a helpful assistant that can execute commands on the MCP server."),
            client.format_message("user", "Can you list the contents of the current directory?")
        ]
        
        # Get response from OpenAI with tools enabled
        response = client.create_chat_completion(
            messages,
            tools=tools
        )
        
        # Print the response
        print("\nMCP Integration Test Results:")
        print("----------------------------")
        print("User: Can you list the contents of the current directory?")
        print(f"Assistant Response: {response.choices[0].message}")
        
        # Check if the response includes a tool call
        if hasattr(response.choices[0].message, 'tool_calls'):
            print("\nTool Calls:")
            for tool_call in response.choices[0].message.tool_calls:
                print(f"- Function: {tool_call.function.name}")
                print(f"  Arguments: {tool_call.function.arguments}")
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"\nError during MCP integration test: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running basic chat test...")
    test_basic_chat()
    
    print("\nRunning MCP integration test...")
    test_mcp_integration() 