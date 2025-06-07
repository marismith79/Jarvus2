"""
OpenAI client implementation for handling LLM interactions.
This module provides a clean interface for communicating with OpenAI's API
and managing conversation state.
"""

import os
from typing import Dict, List, Optional, Any
import openai

class OpenAIClient:
    def __init__(self):
        """Initialize the OpenAI client with API key from environment variables."""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        openai.api_key = self.api_key
        self.model = "gpt-4-turbo-preview"  # Default model, can be configured
    
    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a chat completion using OpenAI's API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            tools: Optional list of tool definitions for function calling
            temperature: Controls randomness (0.0 to 2.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Dictionary containing the API response
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response
        except Exception as e:
            raise Exception(f"Error creating chat completion: {str(e)}")
    
    def format_message(self, role: str, content: str) -> Dict[str, str]:
        """
        Format a message for the OpenAI API.
        
        Args:
            role: Message role ('system', 'user', 'assistant', or 'tool')
            content: Message content
            
        Returns:
            Formatted message dictionary
        """
        return {"role": role, "content": content}
    
    def format_tool_message(self, tool_call_id: str, content: str) -> Dict[str, str]:
        """
        Format a tool message for the OpenAI API.
        
        Args:
            tool_call_id: ID of the tool call this message is responding to
            content: Tool response content
            
        Returns:
            Formatted tool message dictionary
        """
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        } 