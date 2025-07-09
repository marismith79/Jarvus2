"""
Enhanced Agent Service with Memory Management
Integrates short-term and long-term memory with agent interactions.
"""

import uuid
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from flask_login import current_user
from flask import abort

from ..db import db
from ..models.history import History, InteractionHistory
from ..models.memory import ShortTermMemory, LongTermMemory
from .memory_service import memory_service, MemoryConfig
from ..llm.client import JarvusAIClient

from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolMessage,
    ChatCompletions
)
from jarvus_app.services.tool_registry import tool_registry
from jarvus_app.services.pipedream_auth_service import pipedream_auth_service as default_pipedream_auth_service

        

logger = logging.getLogger(__name__)


class AgentService:
    """Enhanced agent service with memory management capabilities"""
    
    def __init__(self):
        self.llm_client = JarvusAIClient()
    
    def get_agent(self, agent_id: int, user_id: int) -> History:
        """Get an agent with memory context"""
        agent = History.query.filter_by(id=agent_id, user_id=user_id).first_or_404()
        try:
            db.session.refresh(agent)
        except:
            pass
        return agent
    
    def get_agent_tools(self, agent: History) -> List[str]:
        """Get tools for an agent"""
        return agent.tools or []
    
    def create_agent(self, user_id: int, name: str, tools: Optional[List[str]] = None, description: str = None) -> History:
        """Create a new agent with memory initialization"""
        if not name:
            abort(400, 'Agent name is required.')
        
        new_agent = History(
            user_id=user_id,
            name=name,
            tools=tools or [],
            description=description or '',
            messages=[]
        )
        
        db.session.add(new_agent)
        db.session.commit()
        
        # Initialize memory for the agent
        self._initialize_agent_memory(user_id, new_agent.id)
        
        logger.info(f"Created new agent {new_agent.id} with memory initialization")
        return new_agent
    
    def process_message(
        self, 
        agent_id: int, 
        user_id: int, 
        user_message: str,
        thread_id: Optional[str] = None,
        tool_choice: str = 'auto',
        web_search_enabled: bool = True,
        pipedream_auth_service=None,
        logger=None
    ) -> Tuple[str, Dict[str, Any]]:
        """Process a message with full memory context and tool orchestration, using two-step tool selection."""
        if logger is None:
            logger = logging.getLogger(__name__)
        pipedream_auth_service = default_pipedream_auth_service
        if not thread_id:
            thread_id = f"thread_{agent_id}_{user_id}_{int(datetime.utcnow().timestamp())}"
        # Step 1: Get context
        agent, allowed_tools, memory_info, messages = self._get_context_for_message(
            agent_id, user_id, user_message, thread_id, web_search_enabled
        )
        # Step 2: Tool selection
        filtered_tools = self._select_tools_with_llm(user_message, allowed_tools)
        # If web_search_enabled is False, filter out web tools
        if not web_search_enabled:
            filtered_tools = [
                t for t in filtered_tools
                if not (hasattr(tool_registry.get_tool(t), 'category') and getattr(tool_registry.get_tool(t), 'category', None) and tool_registry.get_tool(t).category.value == 'web')
            ]
        # Step 3: Orchestration
        final_assistant_message = self._orchestrate_tool_calls(
            messages=messages,
            allowed_tools=filtered_tools,
            user_id=user_id,
            agent_id=agent_id,
            tool_choice=tool_choice,
            pipedream_auth_service=pipedream_auth_service,
            logger=logger
        )
        # Save updated messages to DB (as dicts)
        agent.messages = []
        for m in messages:
            if isinstance(m, UserMessage):
                agent.messages.append({'role': 'user', 'content': m.content})
            elif isinstance(m, AssistantMessage):
                agent.messages.append({'role': 'assistant', 'content': m.content})
            elif isinstance(m, SystemMessage):
                agent.messages.append({'role': 'system', 'content': m.content})
            else:
                agent.messages.append({'role': 'user', 'content': getattr(m, 'content', '')})
        db.session.commit()
        if final_assistant_message:
            self._save_interaction(agent, user_message, final_assistant_message)
        self._store_memories_from_interaction(user_id, agent_id, messages)
        agent = self.get_agent(agent_id, user_id)  # Re-fetch from DB
        return final_assistant_message, memory_info
    
    def _initialize_agent_memory(self, user_id: int, agent_id: int):
        """Initialize memory structures for a new agent"""
        try:
            # Create initial memory entry for the agent
            memory_service.store_memory(
                user_id=user_id,
                namespace="agent_config",
                memory_data={
                    "agent_id": agent_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "memory_enabled": True
                },
                memory_type="config",
                importance_score=2.0
            )
            logger.info(f"Initialized memory for agent {agent_id}")
        except Exception as e:
            logger.error(f"Failed to initialize memory for agent {agent_id}: {str(e)}")
    
    def _get_context_for_message(
        self,
        agent_id: int,
        user_id: int,
        user_message: str,
        thread_id: Optional[str],
        web_search_enabled: bool
    ):
        agent = self.get_agent(agent_id, user_id)
        allowed_tools = set(self.get_agent_tools(agent))
        if web_search_enabled:
            allowed_tools.add('web')
        allowed_tools = list(allowed_tools)
        memory_context = memory_service.get_context_for_conversation(
            user_id=user_id,
            thread_id=thread_id,
            current_message=user_message
        )
        current_state = memory_service.get_latest_state(thread_id, user_id)
        if not current_state:
            current_state = {
                'messages': [],
                'agent_id': agent_id,
                'user_id': user_id,
                'thread_id': thread_id
            }
        current_state['messages'].append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.utcnow().isoformat()
        })
        messages = []
        system_message = f"""You are a helpful AI assistant with access to user memories and conversation history.\n\n{memory_context if memory_context else 'No specific memories or context available.'}\n\nPlease be helpful, accurate, and remember important information about the user when appropriate."""
        messages.append({'role': 'system', 'content': system_message})
        conversation_messages = current_state['messages'][-10:]
        for msg in conversation_messages:
            if msg.get('content'):
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        memory_info = {
            'thread_id': thread_id,
            'memory_context_used': bool(memory_context)
        }
        return agent, allowed_tools, memory_info, messages

    def _select_tools_with_llm(self, user_message, allowed_tools):
        jarvus_ai = self.llm_client
        tool_selection_prompt = (
            "Given the following user message and these tool categories, "
            "which tool(s) or tool category(ies) would you use to answer the message? "
            "Respond with a JSON list of tool names or categories. If none, return an empty list."
        )
        tool_selection_messages = [
            {"role": "system", "content": tool_selection_prompt},
            {"role": "user", "content": user_message},
            {"role": "system", "content": f"Available tool categories: {allowed_tools}"}
        ]
        tool_selection_response = jarvus_ai.create_chat_completion(tool_selection_messages)
        def parse_tools_from_response(resp):
            try:
                if isinstance(resp, dict) and 'assistant' in resp and 'content' in resp['assistant']:
                    content = resp['assistant']['content']
                elif isinstance(resp, dict) and 'choices' in resp and resp['choices']:
                    content = resp['choices'][0]['message']['content']
                else:
                    content = str(resp)
                import re, json
                match = re.search(r'\[.*\]', content, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
                return json.loads(content)
            except Exception:
                return []
        needed_tools_or_categories = set(parse_tools_from_response(tool_selection_response))
        filtered_tools = [
            t for t in allowed_tools
            if t in needed_tools_or_categories or (hasattr(t, 'category') and t.category.value in needed_tools_or_categories)
        ]
        return filtered_tools

    def _orchestrate_tool_calls(
        self,
        messages,
        allowed_tools,
        user_id,
        agent_id,
        tool_choice,
        pipedream_auth_service,
        logger
    ):
        """Orchestrate tool calling logic for both legacy and enhanced chat handlers."""
        jarvus_ai = self.llm_client
        sdk_tools = tool_registry.get_sdk_tools_by_modules(allowed_tools)
        new_messages = []
        try:
            while True:
                logger.info("Calling Azure AI for completion (_orchestrate_tool_calls)")
                response: ChatCompletions = jarvus_ai.client.complete(
                    messages=messages,
                    model=jarvus_ai.deployment_name,
                    tools=sdk_tools,
                    stream=False,
                    tool_choice=tool_choice
                )
                logger.info("Received response from Azure AI (_orchestrate_tool_calls)")
                choice = response.choices[0]
                msg = choice.message
                assistant_msg = AssistantMessage(content=msg.content if msg.content is not None else "", tool_calls=msg.tool_calls)
                messages.append(assistant_msg)
                new_messages.append({'role': 'assistant', 'content': assistant_msg.content})
                if not msg.tool_calls:
                    logger.info("No tool calls in response - conversation complete (_orchestrate_tool_calls)")
                    break
                logger.info(f"Processing {len(msg.tool_calls)} tool calls (_orchestrate_tool_calls)")
                for call in msg.tool_calls:
                    retries = 0
                    max_retries = 3
                    current_call = call
                    while retries < max_retries:
                        tool_name = current_call.function.name
                        tool_args = json.loads(current_call.function.arguments) if current_call.function.arguments else {}
                        logger.info(f"Executing tool: {tool_name} with args: {tool_args} (_orchestrate_tool_calls)")
                        try:
                            app_slug = "google_docs"  # TODO: Dynamically determine app_slug if needed
                            external_user_id = str(user_id)
                            tool_result = pipedream_auth_service.execute_tool(
                                external_user_id=external_user_id,
                                app_slug=app_slug,
                                tool_name=tool_name,
                                tool_args=tool_args
                            )
                            tool_msg = ToolMessage(content=json.dumps(tool_result), tool_call_id=current_call.id)
                            messages.append(tool_msg)
                            logger.info("Prompting LLM for final response after tool execution (_orchestrate_tool_calls)")
                            response = jarvus_ai.client.complete(
                                messages=messages,
                                model=jarvus_ai.deployment_name,
                                stream=False,
                            )
                            choice = response.choices[0]
                            msg = choice.message
                            assistant_msg = AssistantMessage(content=msg.content if msg.content is not None else "", tool_calls=msg.tool_calls)
                            messages.append(assistant_msg)
                            new_messages.append({'role': 'assistant', 'content': assistant_msg.content})
                            break
                        except Exception as e:
                            error_msg = f"Tool call '{tool_name}' failed with error: {str(e)}"
                            logger.error(error_msg)
                            tool_msg = ToolMessage(content=json.dumps({"error": error_msg}), tool_call_id=current_call.id)
                            messages.append(tool_msg)
                            messages.append(UserMessage(content=f"{error_msg}. Please analyze the error and try a different tool or fix the arguments and call a tool again. Do not just suggest alternatives in text—actually call a tool."))
                            messages.append(SystemMessage(content="When you see an error message, you must analyze it and try a different tool or fix the arguments and call a tool again. Do not just suggest alternatives in text—actually call a tool."))
                            retries += 1
                            if retries >= max_retries:
                                logger.error(f"Max retries reached for tool call '{tool_name}'. Moving on. (_orchestrate_tool_calls)")
                                break
                            logger.info("Prompting LLM again after tool call failure (_orchestrate_tool_calls)")
                            response = jarvus_ai.client.complete(
                                messages=messages,
                                model=jarvus_ai.deployment_name,
                                tools=sdk_tools,
                                stream=False,
                                tool_choice="required"
                            )
                            logger.info("Received response from Azure AI (retry, _orchestrate_tool_calls)")
                            choice = response.choices[0]
                            msg = choice.message
                            assistant_msg = AssistantMessage(content=msg.content if msg.content is not None else "", tool_calls=msg.tool_calls)
                            messages.append(assistant_msg)
                            new_messages.append({'role': 'assistant', 'content': assistant_msg.content})
                            logger.info(f"Assistant message (retry, _orchestrate_tool_calls): {assistant_msg}")
                            if not msg.tool_calls:
                                logger.info("No tool calls in response after retry - conversation complete (_orchestrate_tool_calls)")
                                break
                            current_call = msg.tool_calls[0]
            # Return the last assistant message
            final_assistant_message = ""
            if new_messages:
                for msg in reversed(new_messages):
                    if msg.get('role') == 'assistant' and msg.get('content'):
                        final_assistant_message = msg.get('content')
                        break
            return final_assistant_message
        except Exception as e:
            logger.error(f"Error in _orchestrate_tool_calls: {str(e)}", exc_info=True)
            return ""
    
    def _save_interaction(self, agent: History, user_message: str, assistant_message: str):
        """Save interaction to InteractionHistory for display"""
        interaction = InteractionHistory(
            history_id=agent.id,
            user_id=agent.user_id,
            user_message=user_message,
            assistant_message=assistant_message
        )
        db.session.add(interaction)
        db.session.commit()
    
    def _store_memories_from_interaction(self, user_id, agent_id, messages):
        """Extract tool call and feedback and store memories from the last exchange."""
        try:
            last_two = messages[-2:] if len(messages) >= 2 else messages
            tool_call = None
            for m in reversed(messages):
                if isinstance(m, ToolMessage):
                    try:
                        tool_call = json.loads(m.content)
                    except Exception:
                        tool_call = m.content
                    break
            feedback = None
            for m in reversed(messages):
                if isinstance(m, UserMessage) and hasattr(m, 'feedback'):
                    feedback = m.feedback
                    break
            memory_service.extract_and_store_memories(
                user_id=user_id,
                conversation_messages=last_two,
                agent_id=agent_id,
                tool_call=tool_call,
                feedback=feedback
            )
        except Exception as e:
            logger.error(f"Failed to extract and store memories: {str(e)}")


# Global enhanced agent service instance
agent_service = AgentService() 