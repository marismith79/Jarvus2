"""
Azure AI Inference client implementation for handling LLM interactions.
This module provides a clean interface for communicating with Azure AI Foundry API
and managing conversation state.
"""

import json
import os
from typing import Any, Dict, List, Optional

from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential


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

    def _parse_tool_arguments(self, arguments: str) -> Dict[str, Any]:
        """Safely parse tool arguments from JSON string."""
        try:
            if not arguments or not arguments.strip():
                return {}
            return json.loads(arguments)
        except json.JSONDecodeError as e:
            print(f"Failed to parse tool arguments: {e}")
            return {}

    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.8,
        top_p: float = 0.1,
        presence_penalty: float = 0.0,
        jwt_token: Optional[str] = None,
        frequency_penalty: float = 0.0,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[str] = None,
    ) -> Dict:
        """Create a chat completion using Azure AI Foundry API."""
        try:
            print("\n=== Creating Chat Completion ===")
            print(f"Number of messages: {len(messages)}")
            print(f"Last message role: {messages[-1]['role'] if messages else 'None'}")
            print(f"Tool choice: {tool_choice}")
            # print(f"Raw messages: {messages}")
            
            kwargs = {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty,
                "model": self.deployment_name,
                **({"tools": tools} if tools else {}),
                **({"tool_choice": tool_choice} if tool_choice else {}),
            }
            response = self.client.complete(**kwargs)
            
            print(f"Request kwargs: {kwargs}")
            print(f"Raw response: {response}")
            print(f"Response choices: {response['choices']}")
            print(f"First choice message: {response['choices'][0]['message']}")
            
            choice = response.choices[0] # ChatChoice
            msg = choice.message # ChatResponseMessage
            if msg.tool_calls:
                # one or more ChatCompletionsToolCall objects
                for call in msg.tool_calls:
                    print("Function to call:", call.name)
                    print("With args JSON:", call.arguments)
            else:
                return {"assistant": {"role": msg.role, "content": msg.content}}

        except Exception as e:
            error_msg = f"Azure AI Foundry API Error: {str(e)}"
            return {"error": error_msg}

    def format_message(self, role: str, content: str) -> Dict[str, str]:
        """Format a message for the chat completion."""
        return {"role": role, "content": content}