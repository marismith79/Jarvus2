"""
Azure AI Foundry Models client implementation for handling LLM interactions.
This module provides a clean interface for communicating with Azure AI Foundry Models API
and managing conversation state.
"""

import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from typing import Dict, List, Optional, Any, Generator

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

        self.client = ChatCompletionsClient(
            endpoint=self.api_base,
            credential=AzureKeyCredential(self.api_key),
            api_version=self.api_version
        )
        print("=== Azure AI Foundry Models Client Initialization Complete ===\n")

    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = 2048,
        stream: bool = True
    ) -> Generator[str, None, None]:
        """
        Create a chat completion using Azure AI Foundry Models API with streaming support.
        Returns a generator that yields response chunks.
        """
        try:
            # Convert messages to Azure AI Inference format
            azure_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    azure_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    azure_messages.append(UserMessage(content=msg["content"]))

            response = self.client.complete(
                stream=stream,
                messages=azure_messages,
                max_tokens=max_tokens,
                temperature=0.8,
                top_p=0.1,
                presence_penalty=0.0,
                frequency_penalty=0.0,
                model=self.deployment_name
            )

            if stream:
                for update in response:
                    if update.choices:
                        content = update.choices[0].delta.content
                        if content:
                            yield content
            else:
                if response.choices:
                    yield response.choices[0].message.content

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