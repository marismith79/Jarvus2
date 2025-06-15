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
    ChatRequestMessage,
    ToolMessage,
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
        )

    def _format_message(self, msg: Dict[str, str]) -> ChatRequestMessage:
        """Format a message into the correct Azure AI format."""
        role_map = {
            "system": SystemMessage,
            "user": UserMessage,
            "tool": lambda content, **kwargs: ToolMessage(**kwargs, content=content),
        }
        
        msg_class = role_map.get(msg["role"], ChatRequestMessage)
        kwargs = {"content": msg["content"]}
        if msg["role"] == "tool":
            kwargs["tool_call_id"] = msg["tool_call_id"]
            
        return msg_class(**kwargs)

    def _parse_tool_arguments(self, arguments: str) -> Dict[str, Any]:
        """Safely parse tool arguments from JSON string."""
        try:
            if not arguments or not arguments.strip():
                return {}
            return json.loads(arguments)
        except json.JSONDecodeError as e:
            print(f"Failed to parse tool arguments: {e}")
            return {}

    def _validate_tool_call(self, tool_call: Any) -> Optional[str]:
        """Validate a tool call and return error message if invalid."""
        if not tool_call:
            return "Invalid tool call: tool call is None"
            
        if not hasattr(tool_call, 'function'):
            return "Invalid tool call: missing function attribute"
            
        if not tool_call.function:
            return "Invalid tool call: function is None"
            
        if not tool_call.function.name:
            return "Invalid tool call: missing function name"
            
        if not tool_registry.get_tool(tool_call.function.name):
            return f"Invalid tool call: unknown function '{tool_call.function.name}'"
            
        return None

    def _handle_tool_call(self, tool_call: Any, messages: List[ChatRequestMessage], jwt_token: Optional[str] = None) -> Optional[str]:
        """Handle a tool call and return the result."""
        try:
            # Validate tool call
            if error := self._validate_tool_call(tool_call):
                return error
                
            # Parse arguments
            args = self._parse_tool_arguments(tool_call.function.arguments)
            if not isinstance(args, dict):
                return f"Invalid tool arguments: expected dict, got {type(args)}"
                
            print(f"\n=== Tool Execution Debug ===")
            print(f"Tool name: {tool_call.function.name}")
            print(f"Raw arguments: {tool_call.function.arguments}")
            print(f"Parsed arguments: {args}")
            print(f"JWT Token provided: {jwt_token is not None}")
            print("===========================\n")
                
            # Execute tool with full arguments
            result = tool_registry.execute_tool(
                tool_name=tool_call.function.name,
                parameters=args,  # Pass the entire arguments dict
                jwt_token=jwt_token
            )
            messages.append(ToolMessage(tool_call_id=tool_call.id, content=str(result)))
            return None
            
        except Exception as e:
            error_msg = f"Error executing tool {getattr(tool_call.function, 'name', 'unknown')}: {str(e)}"
            print(error_msg)
            return error_msg

    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = True,
        max_tokens: int = 2048,
        temperature: float = 0.8,
        top_p: float = 0.1,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[str] = None,
        jwt_token: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Create a chat completion using Azure AI Foundry API with streaming support."""
        try:
            formatted_messages = [self._format_message(msg) for msg in messages]
            kwargs = {
                "stream": stream,
                "messages": formatted_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty,
                "model": self.deployment_name,
                **(tools and {"tools": tools} or {}),
                **(tool_choice and {"tool_choice": tool_choice} or {}),
            }

            response = self.client.complete(**kwargs)
            
            if not stream:
                yield response.choices[0].message.content
                return

            current_tool_call = None
            accumulated_args = ""
            
            for update in response:
                if not update.choices:
                    continue
                    
                choice = update.choices[0]
                
                # Handle tool calls
                if choice.delta.tool_calls:
                    tool_call = choice.delta.tool_calls[0]
                    
                    # Start of a new tool call
                    if tool_call.id:
                        current_tool_call = tool_call
                        accumulated_args = ""
                        continue
                        
                    # Accumulate arguments
                    if tool_call.function and tool_call.function.arguments:
                        accumulated_args += tool_call.function.arguments
                        
                    # If we have a complete tool call, execute it
                    if current_tool_call and current_tool_call.function and accumulated_args:
                        # Only execute if we have a complete JSON object
                        try:
                            # Try to parse the accumulated arguments to verify it's complete JSON
                            json.loads(accumulated_args)
                            current_tool_call.function.arguments = accumulated_args
                            if error := self._handle_tool_call(current_tool_call, formatted_messages, jwt_token):
                                yield error
                            current_tool_call = None
                            accumulated_args = ""
                        except json.JSONDecodeError:
                            # Not complete JSON yet, continue accumulating
                            continue
                        
                # Handle regular content
                elif choice.delta.content:
                    yield choice.delta.content

        except Exception as e:
            error_msg = f"Azure AI Foundry API Error: {str(e)}"
            print(error_msg)
            yield error_msg

    def close(self) -> None:
        """Close the client connection."""
        self.client.close()

    def format_message(self, role: str, content: str) -> Dict[str, str]:
        """Format a message for the chat completion."""
        return {"role": role, "content": content}

    def format_tool_message(self, tool_call_id: str, content: str) -> Dict[str, str]:
        """Format a tool message for the chat completion."""
        return {"role": "tool", "tool_call_id": tool_call_id, "content": content}
