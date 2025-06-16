"""
Azure AI Inference client implementation for handling LLM interactions.
This module provides a clean interface for communicating with Azure AI Foundry API
and managing conversation state.
"""

import json
import os
from typing import Any, Dict, Generator, List, Optional

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ChatRequestMessage,
    ToolMessage,
    FunctionCall,
    ChatCompletionsToolDefinition,
    FunctionDefinition,
)
from azure.core.credentials import AzureKeyCredential

from ..services.tool_registry import tool_registry


class JarvusAIClient:
    def __init__(self) -> None:
        """Initialize the Azure AI Inference client with configuration from environment variables."""
        self._init_config()
        self._init_client()

    def _init_config(self) -> None:
        """Initialize configuration from environment variables."""
        self.api_key = os.getenv("AZURE_AI_FOUNDRY_KEY")
        self.api_base = os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
        self.api_version = os.getenv("AZURE_AI_FOUNDRY_API_VERSION")
        self.deployment_name = os.getenv("AZURE_AI_FOUNDRY_DEPLOYMENT_NAME")

        if not all([self.api_key, self.api_base, self.deployment_name]):
            raise ValueError("Missing required Azure AI Foundry configuration")

    def _init_client(self) -> None:
        """Initialize the Azure AI client."""
        self.client = ChatCompletionsClient(
            endpoint=self.api_base or "",
            credential=AzureKeyCredential(self.api_key or ""),
            api_version=self.api_version,
        )

    def _format_message(self, msg: Dict[str, str]) -> ChatRequestMessage:
        """Format a message into the correct Azure AI format."""
        print(f"\n=== Formatting Message ===")
        print(f"Message role: {msg['role']}")
        print(f"Message content type: {type(msg.get('content'))}")
        
        role = msg['role']
        content = msg.get('content', '')  # Default to empty string if content is None
        
        if role == 'system':
            return SystemMessage(content=content)
        if role == 'user':
            return UserMessage(content=content)
        if role == 'assistant':
            return AssistantMessage(content=content)
        if role == 'tool':
            return ToolMessage(tool_call_id=msg['tool_call_id'], content=content)
        
        # Fallback for any other message types
        return ChatRequestMessage(role=role, content=content)

    def _parse_tool_arguments(self, arguments: str) -> Dict[str, Any]:
        """Safely parse tool arguments from JSON string."""
        try:
            if not arguments or not arguments.strip():
                return {}
            return json.loads(arguments)
        except json.JSONDecodeError as e:
            print(f"Failed to parse tool arguments: {e}")
            return {}

    def _validate_tool_call(self, function_call: Any) -> Optional[str]:
        """Validate a function call and return error message if invalid."""
        if not function_call:
            return "Invalid function call: function call is None"
            
        if not hasattr(function_call, 'name'):
            return "Invalid function call: missing name attribute"
            
        if not function_call.name:
            return "Invalid function call: missing function name"
            
        if not tool_registry.get_tool(function_call.name):
            return f"Invalid function call: unknown function '{function_call.name}'"
            
        return None

    def _handle_tool_call(self, function_call: Any, messages: List[ChatRequestMessage], jwt_token: Optional[str] = None) -> Optional[str]:
        """Handle a function call and return the result."""
        try:
            # Validate function call
            if error := self._validate_tool_call(function_call):
                return error
                
            # Parse arguments
            args = self._parse_tool_arguments(function_call.arguments)
            if not isinstance(args, dict):
                return f"Invalid tool arguments: expected dict, got {type(args)}"
                
            print(f"\n=== Tool Execution Debug ===")
            print(f"Tool name: {function_call.name}")
            print(f"Raw arguments: {function_call.arguments}")
            print(f"Parsed arguments: {args}")
            print(f"JWT Token provided: {jwt_token is not None}")
            print("===========================\n")
                
            # Execute tool with full arguments
            result = tool_registry.execute_tool(
                tool_name=function_call.name,
                parameters=args,
                jwt_token=jwt_token
            )
            
            # Convert result to string if it's not already
            result_str = str(result) if not isinstance(result, str) else result
            
            print(f"Tool result extracted")
            
            # Step 1: Add the assistant message with tool_calls
            assistant_message = AssistantMessage(
                tool_calls=[ FunctionCall(
                    name=function_call.name,
                    arguments=function_call.arguments,
                    id=function_call.id
                )]
            )
            
            # Step 2: Add the tool response message
            tool_message = ToolMessage(
                tool_call_id=function_call.id,
                content=result_str
            )
            
            messages.append(assistant_message)
            messages.append(tool_message)
            
            print(f"\n=== Message Sequence Debug ===")
            print(f"Assistant message: {assistant_message}")
            print(f"Tool message: {tool_message}")
            print("===========================\n")
            
            return None
            
        except Exception as e:
            error_msg = f"Error executing tool {getattr(function_call, 'name', 'unknown')}: {str(e)}"
            print(error_msg)
            return error_msg

    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        max_tokens: int = 2048,
        temperature: float = 0.8,
        top_p: float = 0.1,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Create a chat completion using Azure AI Foundry API with streaming support."""
        try:
            print("\n=== Creating Chat Completion ===")
            print(f"Number of messages: {len(messages)}")
            print(f"Last message role: {messages[-1]['role'] if messages else 'None'}")
            print(f"Tool choice: {tool_choice}")
            
            formatted_messages = [self._format_message(msg) for msg in messages]
            
            # Convert tool schemas to ChatCompletionsToolDefinition objects
            formatted_tools = None
            if tools:
                print(f"\n=== Tools ===")
                formatted_tools = [
                    ChatCompletionsToolDefinition(
                        function=FunctionDefinition(
                            name=tool["function"]["name"],
                            description=tool["function"]["description"],
                            parameters=tool["function"]["parameters"],
                        )
                    )
                    for tool in tools
                ]
                print(f"\n=== Tool Definitions ===")
                print(f"Number of tools: {len(formatted_tools)}")
                print(f"Tool: {formatted_tools}")
                print(f"Tool types: {[type(tool) for tool in formatted_tools]}")
                print("=======================\n")
            
            kwargs = {
                "stream": stream,
                "messages": formatted_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty,
                "model": self.deployment_name,
                **(formatted_tools and {"tools": formatted_tools} or {}),
                **(tool_choice and {"tool_choice": tool_choice} or {}),
            }

            response = self.client.complete(**kwargs)
            
            if not stream:
                # Handle tool calls in non-streaming mode
                if hasattr(response.choices[0].message, 'tool_calls'):
                    tool_calls = response.choices[0].message.tool_calls
                    if tool_calls:
                        tool_call = tool_calls[0]  # assuming only one for now
                        yield json.dumps({
                            "tool_call": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                                "id": tool_call.id
                            }
                        })
                        return
                # If no tool calls, return content
                yield response.choices[0].message.content
                return

            # Streaming mode handling
            current_tool_calls = []
            accumulated_args = {}
            
            for update in response:
                if not update.choices:
                    print("\n=== No choices in update ===")
                    continue
                    
                choice = update.choices[0]
                delta = choice.delta
                
                print("\n=== Response Delta Debug ===")
                print(f"Has content: {hasattr(delta, 'content')}")
                print(f"Has tool_calls: {hasattr(delta, 'tool_calls')}")
                print(f"Content: {getattr(delta, 'content', None)}")
                print(f"Raw delta: {delta}")
                print("=========================\n")
                
                # Handle tool calls
                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        print(f"\n=== Tool Call Delta ===")
                        print(f"Tool call ID: {tool_call.id if hasattr(tool_call, 'id') else 'None'}")
                        print(f"Function name: {tool_call.function.name if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'name') else 'None'}")
                        print(f"Arguments: {tool_call.function.arguments if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'arguments') else 'None'}")
                        print("=========================\n")
                        
                        # Start of a new tool call
                        if hasattr(tool_call, 'id') and tool_call.id:
                            if tool_call.id not in accumulated_args:
                                accumulated_args[tool_call.id] = ""
                            current_tool_calls.append(tool_call)
                            continue
                            
                        # Accumulate arguments for existing tool call
                        if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'arguments') and tool_call.function.arguments:
                            tool_call_id = tool_call.id
                            accumulated_args[tool_call_id] += tool_call.function.arguments
                            
                        # If we have complete tool calls, execute them
                        for tool_call in current_tool_calls:
                            tool_call_id = tool_call.id
                            if tool_call_id in accumulated_args:
                                try:
                                    # Try to parse the accumulated arguments to verify it's complete JSON
                                    json.loads(accumulated_args[tool_call_id])
                                    
                                    # Yield the complete tool call
                                    yield json.dumps({
                                        "tool_call": {
                                            "name": tool_call.function.name,
                                            "arguments": accumulated_args[tool_call_id],
                                            "id": tool_call_id
                                        }
                                    })
                                    
                                    # Remove processed tool call
                                    current_tool_calls.remove(tool_call)
                                    del accumulated_args[tool_call_id]
                                    
                                except json.JSONDecodeError:
                                    # Not complete JSON yet, continue accumulating
                                    continue
                        
                # Handle regular content
                elif hasattr(delta, 'content'):
                    content = delta.content
                    if content is not None:  # Only yield if content is not None
                        print(f"\n=== Content Delta ===")
                        print(f"Content: {content}")
                        print("===================\n")
                        yield json.dumps({"content": content})
                    else:
                        print("\n=== Empty Content Delta ===")
                        print("Skipping empty content")
                        print("===================\n")

        except Exception as e:
            error_msg = f"Azure AI Foundry API Error: {str(e)}"
            print(error_msg)
            yield json.dumps({"error": error_msg})

    def close(self) -> None:
        """Close the client connection."""
        self.client.close()

    def format_message(self, role: str, content: str) -> Dict[str, str]:
        """Format a message for the chat completion."""
        return {"role": role, "content": content}

    def format_tool_message(self, tool_call_id: str, content: str) -> Dict[str, str]:
        """Format a tool message for the chat completion."""
        return {"role": "tool", "tool_call_id": tool_call_id, "content": content}
