"""
Azure AI Inference client implementation for handling LLM interactions.
This module provides a clean interface for communicating with Azure AI Foundry API
and managing conversation state with multimodal support.
"""

import json
import os
from typing import Any, Dict, List, Optional, Union

from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolMessage,
    TextContentItem,
    ImageContentItem,
    ImageUrl
)


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
        messages: List[Union[Dict[str, str], SystemMessage, UserMessage, AssistantMessage, ToolMessage]],
        max_tokens: int = 2048,
        temperature: float = 0.8,
        top_p: float = 0.1,
        presence_penalty: float = 0.0,
        jwt_token: Optional[str] = None,
        frequency_penalty: float = 0.0,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[str] = None,
        logger: Optional[Any] = None,  # Add logger argument
    ):
        """Create a chat completion using Azure AI Foundry API with multimodal support."""
        try:
            # Messages are already in the correct format from agent_service
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
            # if logger:
            #     logger.info(f"[AzureAI] Request kwargs: {json.dumps({k: v for k, v in kwargs.items() if k != 'messages'}, default=str)[:1000]}")
            #     # Log message count instead of full content to avoid base64 spam
            #     message_count = len(messages)
            #     logger.info(f"[AzureAI] Request messages: {message_count} messages")
            response = self.client.complete(**kwargs)
            # if logger:
            #     try:
            #         logger.info(f"[AzureAI] Response Logged")
            #     except Exception as e:
            #         logger.warning(f"[AzureAI] Could not log response: {e}")
            return response
        except Exception as e:
            error_msg = f"Azure AI Foundry API Error: {str(e)}"
            if logger:
                logger.error(f"[AzureAI] Exception: {error_msg}")
            return {"error": error_msg}

    def format_message(self, role: str, content: str) -> Dict[str, str]:
        """Format a message for the chat completion."""
        return {"role": role, "content": content}
    
    def format_response(self, response) -> Dict:
        """Format a response from azure open ai api"""
        return {"assistant": {"role": response.choices[0].message.role, "content": response.choices[0].message.content}}