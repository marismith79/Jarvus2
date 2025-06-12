"""
Azure AI Foundry Models client implementation for handling LLM interactions.
This module provides a clean interface for communicating with Azure AI Foundry Models API
and managing conversation state.
"""

import os
from openai import AzureOpenAI
from typing import Dict, List, Optional, Any

class JarvusAIClient:
    def __init__(self):
        """Initialize the Azure AI Foundry Models client with configuration from environment variables."""
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.api_base = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_version = os.getenv('AZURE_OPENAI_API_VERSION')
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')

        print(f"\nAzure AI Foundry Models Configuration:")
        print(f"API Key found: {'Yes' if self.api_key else 'No'}")
        print(f"API Base: {self.api_base}")
        print(f"API Version: {self.api_version}")
        print(f"Deployment Name: {self.deployment_name}")

        if not all([self.api_key, self.api_base, self.api_version, self.deployment_name]):
            raise ValueError("Missing required Azure AI Foundry Models configuration. Please check your environment variables.")

        self.client = AzureOpenAI(
            api_version=self.api_version,
            azure_endpoint=self.api_base,
            api_key=self.api_key
        )
        self.deployment_id = self.deployment_name
        print("=== Azure AI Foundry Models Client Initialization Complete ===\n")

    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None
    ) -> Any:
        """
        Create a chat completion using Azure AI Foundry Models API.
        Automatically merge the system prompt into the first user message if the model does not support the system role (e.g., o1-mini).
        Do not send the 'tools' parameter if the model does not support it (e.g., o1-mini).
        """
        try:
            # If using o1-mini or o1-preview or any o1* model, merge system prompt into first user message
            o1_model = self.deployment_id and self.deployment_id.startswith("o1")
            if o1_model:
                if messages and messages[0]["role"] == "system":
                    system_content = messages[0]["content"]
                    # Find the first user message
                    for i, msg in enumerate(messages[1:], start=1):
                        if msg["role"] == "user":
                            messages[i]["content"] = f"{system_content}\n\n{messages[i]['content']}"
                            break
                    # Remove the system message
                    messages = [msg for msg in messages if msg["role"] != "system"]

            params = {
                "messages": messages,
                "model": self.deployment_id
            }
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            if tools is not None and not o1_model:
                params["tools"] = tools
            response = self.client.chat.completions.create(**params)
            return response
        except Exception as e:
            print(f"Azure AI Foundry Models API Error: {str(e)}")
            raise Exception(f"Error creating chat completion: {str(e)}")

    def format_message(self, role: str, content: str) -> Dict[str, str]:
        return {"role": role, "content": content}

    def format_tool_message(self, tool_call_id: str, content: str) -> Dict[str, str]:
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        } 