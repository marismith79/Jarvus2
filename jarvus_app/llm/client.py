"""
Azure OpenAI client implementation for handling LLM interactions.
This module provides a clean interface for communicating with Azure OpenAI's API
and managing conversation state.
"""

import os
from typing import Dict, List, Optional, Any
import openai

class OpenAIClient:
    def __init__(self):
        """Initialize the Azure OpenAI client with configuration from environment variables."""
        
        # Get the Azure OpenAI configuration
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.api_base = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_version = os.getenv('AZURE_OPENAI_API_VERSION')
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
        
        print(f"\nAzure OpenAI Configuration:")
        print(f"API Key found: {'Yes' if self.api_key else 'No'}")
        print(f"API Base: {self.api_base}")
        print(f"API Version: {self.api_version}")
        print(f"Deployment Name: {self.deployment_name}")
        
        if not all([self.api_key, self.api_base, self.api_version, self.deployment_name]):
            raise ValueError("Missing required Azure OpenAI configuration. Please check your environment variables.")
        
        # Set the Azure OpenAI configuration
        openai.api_key = self.api_key
        openai.api_base = self.api_base
        openai.api_version = self.api_version
        self.model = self.deployment_name
        print("=== Azure OpenAI Client Initialization Complete ===\n")
    
    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a chat completion using Azure OpenAI's API.
        
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
            print(f"Azure OpenAI API Error: {str(e)}")  # Add detailed error logging
            raise Exception(f"Error creating chat completion: {str(e)}")
    
    def format_message(self, role: str, content: str) -> Dict[str, str]:
        """
        Format a message for the Azure OpenAI API.
        
        Args:
            role: Message role ('system', 'user', 'assistant', or 'tool')
            content: Message content
            
        Returns:
            Formatted message dictionary
        """
        return {"role": role, "content": content}
    
    def format_tool_message(self, tool_call_id: str, content: str) -> Dict[str, str]:
        """
        Format a tool message for the Azure OpenAI API.
        
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