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
        print("\n=== OpenAI Client Initialization ===")
        
        # Debug: Print all environment variables that might contain the API key
        print("\nEnvironment variables:")
        for key in os.environ:
            if 'OPENAI' in key:
                value = os.environ[key]
                masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                print(f"  {key}: {masked}")
        
        # Get the API key
        self.api_key = os.getenv('OPENAI_API_KEY')
        print(f"\nAPI Key found: {'Yes' if self.api_key else 'No'}")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Debug: Print first 4 and last 4 characters of the API key
        masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "***"
        print(f"Loading OpenAI API key: {masked_key}")
        print("API key starts with 'sk-':", self.api_key.startswith('sk-'))
        
        # Set the API key and ensure we're using the standard OpenAI API
        openai.api_key = self.api_key
        openai.api_base = "https://api.openai.com/v1"  # Standard OpenAI endpoint
        openai.api_version = None  # Remove any version header
        self.model = "gpt-4-turbo-preview"  # Default model, can be configured
        print("=== OpenAI Client Initialization Complete ===\n")
    
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
            print(f"OpenAI API Error: {str(e)}")  # Add detailed error logging
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