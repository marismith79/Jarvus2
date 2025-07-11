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
from jarvus_app.services.pipedream_auth_service import pipedream_auth_service
from jarvus_app.services.pipedream_tool_registry import pipedream_tool_service
from ..services.pipedream_tool_registry import ensure_tools_discovered
        

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
        
        # Always include Google Docs tools for all agents
        default_tools = ['docs']
        if tools:
            # Merge user-selected tools with default tools, avoiding duplicates
            all_tools = list(set(default_tools + tools))
        else:
            all_tools = default_tools
        
        new_agent = History(
            user_id=user_id,
            name=name,
            tools=all_tools,
            description=description or '',
            messages=[]
        )
        
        db.session.add(new_agent)
        db.session.commit()
        
        # Initialize memory for the agent
        self._initialize_agent_memory(user_id, new_agent.id)
        
        logger.info(f"Created new agent {new_agent.id} with memory initialization")
        return new_agent
    
    def delete_agent(self, agent_id: int, user_id: int) -> bool:
        """Delete an agent and all its associated data from the database."""
        agent = self.get_agent(agent_id, user_id)  # This will 404 if agent doesn't exist or doesn't belong to user
        try:
            db.session.delete(agent)
            db.session.commit()
            logger.info(f"Successfully deleted agent {agent_id} for user {user_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete agent {agent_id}: {str(e)}")
            raise

    def process_message(
        self,
        agent_id,
        user_id,
        user_message,
        thread_id=None,
        tool_choice="auto",
        web_search_enabled=True,
        logger=None,
        session_data=None
    ):
        """Process a message with full memory context and tool orchestration, using plan-then-act."""
        if logger is None:
            logger = logging.getLogger(__name__)
        if not thread_id:
            thread_id = f"thread_{agent_id}_{user_id}_{int(datetime.utcnow().timestamp())}"
        # Step 1: Get context
        agent, allowed_tools, memory_info, messages = self._get_context_for_message(
            agent_id, user_id, user_message, thread_id, web_search_enabled
        )
        # Step 2: Tool selection
        filtered_tools = self._select_tools_with_llm(user_message, allowed_tools)
        print("[DEBUG] allowed_tools", allowed_tools)
        print("[DEBUG] filtered_tools", filtered_tools)
        # if filtered_tools:
        #     # Step 3: Planning step
        #     plan = self._plan_task_with_llm(user_message, filtered_tools)
        #     # Inject plan into system prompt
        #     plan_instructions = [
        #         "### Plan",
        #         f"You must follow this plan exactly, step by step: {json.dumps(plan, indent=2)}",
        #         "You must only make tool calls that correspond to steps in the plan, and stop making tool calls when the plan is complete."
        #     ]
        #     # Insert plan as a system message after the first system message
        #     messages.insert(1, {"role": "system", "content": "\n".join(plan_instructions)})
        # Step 4: Orchestration
        orchestration_messages = messages.copy()
        final_assistant_message = self._orchestrate_tool_calls(
            user_id=user_id,
            allowed_tools=filtered_tools,
            messages=orchestration_messages,
            tool_choice=tool_choice,
            logger=logger,
            session_data=session_data
        )
        # Save updated messages to DB (as dicts)
        agent.messages = []
        for m in orchestration_messages:
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
        self._store_memories_from_interaction(user_id, agent_id, orchestration_messages)
        agent = self.get_agent(agent_id, user_id)  # Re-fetch from DB
        return final_assistant_message, memory_info
    
    def get_agent_interaction_history(self, agent: History):
        interactions = InteractionHistory.query.filter_by(
            history_id=agent.id,
            user_id=agent.user_id
        ).order_by(InteractionHistory.created_at.asc()).all()
        history = []
        for interaction in interactions:
            history.append({'role': 'user', 'content': interaction.user_message})
            history.append({'role': 'assistant', 'content': interaction.assistant_message})
        return history

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
        from jarvus_app import config
        agent = self.get_agent(agent_id, user_id)
        allowed_tools = set(self.get_agent_tools(agent))
        if web_search_enabled:
            allowed_tools.add('web')
        allowed_tools = list(allowed_tools)
        # Get current state (working memory)
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
        # 1. System instructions
        system_instructions = [
            "### System Instructions",
            config.Config.CHATBOT_SYSTEM_PROMPT.strip(),
        ]
        messages = [
            {"role": "system", "content": "\n".join(system_instructions)}
        ]
        # 2. Long-term memory (episodic, semantic, procedural) from memory_service
        memory_sections = memory_service.get_context_for_conversation(
            user_id=user_id,
            thread_id=thread_id,
            as_sections=True
        )
        long_term_sections = []
        if memory_sections['episodic']:
            long_term_sections.append("### Episodic Memory")
            long_term_sections.extend(memory_sections['episodic'])
        if memory_sections['semantic']:
            long_term_sections.append("\n### Semantic Memory")
            long_term_sections.extend(memory_sections['semantic'])
        if memory_sections['procedural']:
            long_term_sections.append("\n### Procedural Memory")
            long_term_sections.extend(memory_sections['procedural'])
        messages.append({
            "role": "system",
            "content": "\n".join(long_term_sections) if long_term_sections else ""
        })
        # 3. Working memory (recent turns)
        working_turns = []
        conversation_messages = current_state['messages'][-10:] if 'messages' in current_state else []
        for msg in conversation_messages:
            if msg.get('content') and msg['role'] in ['user', 'assistant']:
                content = msg['content']
                if not (content.startswith('{') and content.endswith('}')) and 'tool_call' not in content.lower():
                    working_turns.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
        messages.extend(working_turns)
        # 4. Current user query (always last)
        messages.append({
            'role': 'user',
            'content': user_message
        })
        memory_info = {
            'thread_id': thread_id,
            'memory_context_used': True
        }
        return agent, allowed_tools, memory_info, messages

    def _select_tools_with_llm(self, user_message, allowed_tools):
        jarvus_ai = self.llm_client
        tool_selection_prompt = (
            "Given the following user message and these tool categories, "
            "which tool(s) or tool category(ies) would you use to answer the message? "
            "Respond with a JSON list of tool names or categories. Return the exact name that is provided. If none, return an empty list."
        )
        tool_selection_messages = [
            {"role": "system", "content": tool_selection_prompt},
            {"role": "user", "content": user_message},
            {"role": "system", "content": f"Available tool categories: {allowed_tools}"}
        ]
        tool_selection_response = jarvus_ai.create_chat_completion(tool_selection_messages)
        print("[DEBUG] tool_selection_response:", tool_selection_response)
        # def parse_tools_from_response(resp):
        #     try:
        #         if isinstance(resp, dict) and 'assistant' in resp and 'content' in resp['assistant']:
        #             content = resp['assistant']['content']
        #         elif isinstance(resp, dict) and 'choices' in resp and resp['choices']:
        #             content = resp['choices'][0]['message']['content']
        #         else:
        #             content = str(resp)
        #         import re, json
        #         match = re.search(r'\[.*\]', content, re.DOTALL)
        #         if match:
        #             return json.loads(match.group(0))
        #         return json.loads(content)
        #     except Exception:
        #         return []
        needed_tools_or_categories = tool_selection_response['choices'][0]['message']['content']
        print("[DEBUG] needed_tools_or_categories:", needed_tools_or_categories)
        filtered_tools = [
            t for t in allowed_tools
            if t in needed_tools_or_categories or (hasattr(t, 'category') and t.category.value in needed_tools_or_categories)
        ]
        return filtered_tools

    def _plan_task_with_llm(self, user_message, allowed_tools):
        """
        Use the LLM to generate a step-by-step plan for the user's request.
        Returns a list of plan steps, each a dict with 'tool' and 'parameters'.
        """
        jarvus_ai = self.llm_client
        planning_prompt = (
            f"You are an AI agent with access to the following tools: {allowed_tools}. "
            "Given the user's request, break it down into a step-by-step plan. "
            "Respond with a JSON list, where each item is an action with a 'tool' name and 'parameters' dict. "
            "If the task is simple, the list may have only one step."
        )
        planning_messages = [
            {"role": "system", "content": planning_prompt},
            {"role": "user", "content": user_message}
        ]
        planning_response = jarvus_ai.create_chat_completion(planning_messages, logger=logger)
        def parse_plan_from_response(resp):
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
        plan = parse_plan_from_response(planning_response)
        # Ensure plan is a list of dicts with 'tool' and 'parameters'
        filtered_plan = []
        for step in plan:
            if isinstance(step, dict) and 'tool' in step and 'parameters' in step:
                filtered_plan.append(step)
        return filtered_plan

    def _format_tool_result_for_llm(self, tool_result):
        """
        Format a tool result dict (from pipedream or other tool calls) into a string for the LLM.
        Returns a summary first, then the complete payload.
        """
        import json
        
        # If it's already a string, return it as is
        if isinstance(tool_result, str):
            return tool_result
        
        # If it's a dict, create summary + full payload
        if isinstance(tool_result, dict):
            # Try to extract a summary first
            summary = None
            try:
                # Look for common summary fields
                if 'content' in tool_result and isinstance(tool_result['content'], list):
                    for item in tool_result['content']:
                        if isinstance(item, dict) and 'text' in item:
                            try:
                                inner = json.loads(item['text'])
                                summary = inner.get('exports', {}).get('$summary')
                                if summary:
                                    break
                            except Exception:
                                continue
                
                # Direct summary
                if not summary:
                    summary = tool_result.get('exports', {}).get('$summary')
                
                # Fallback: look for error or success indicators
                if not summary:
                    if tool_result.get('isError'):
                        summary = f"Error: {tool_result.get('error', 'Unknown error')}"
                    else:
                        summary = "Operation completed successfully"
                        
            except Exception:
                summary = "Operation completed"
            
            # Create the full response with summary first
            try:
                full_payload = json.dumps(tool_result, indent=2)
                return f"SUMMARY: {summary}\n\nCOMPLETE RESULT:\n{full_payload}"
            except Exception:
                return f"SUMMARY: {summary}\n\nCOMPLETE RESULT:\n{str(tool_result)}"
        
        # For any other type, convert to string
        return str(tool_result)

    def _orchestrate_tool_calls(self, user_id, allowed_tools, messages, tool_choice, logger, session_data=None):
        """Orchestrate tool calling logic for both legacy and enhanced chat handlers, with plan adherence."""
        jarvus_ai = self.llm_client
        # Ensure tools are discovered if needed
        ensure_tools_discovered(user_id, session_data)
        # Only include SDK tools that are in allowed_tools
        tool_to_app_mapping = pipedream_tool_service.get_tool_to_app_mapping(session_data)
        
        all_sdk_tools = pipedream_tool_service.get_all_sdk_tools(session_data)
        sdk_tools = [
            tool for tool in all_sdk_tools
            if tool_to_app_mapping.get(tool.function.name) in allowed_tools
        ]
        
        # # Use DB-cached tool discovery for allowed app slugs
        # from jarvus_app.services.pipedream_tool_registry import get_or_discover_tools_for_user_apps
        # sdk_tools = get_or_discover_tools_for_user_apps(user_id, allowed_tools)
        print("DEBUG allowed_sdk_tools", sdk_tools)
        new_messages = []
        try:
            while True:
                logger.info("Calling Azure AI for completion (_orchestrate_tool_calls)")
                response = jarvus_ai.create_chat_completion(
                    messages=messages,
                    tools=sdk_tools,
                    tool_choice=tool_choice,
                    logger=logger
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
                            # Get the app slug for this tool from the mapping
                            app_slug = tool_to_app_mapping.get(tool_name, "google_docs")  # fallback
                            
                            external_user_id = str(user_id)
                            tool_result = pipedream_tool_service.execute_tool(
                                external_user_id=external_user_id,
                                app_slug=app_slug,
                                tool_name=tool_name,
                                tool_args=tool_args
                            )
                            # Format tool result for LLM
                            formatted_result = self._format_tool_result_for_llm(tool_result)
                            tool_msg = ToolMessage(content=formatted_result, tool_call_id=current_call.id)
                            messages.append(tool_msg)

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
                            response = jarvus_ai.create_chat_completion(
                                messages=messages,
                                tools=sdk_tools,
                                tool_choice="required",
                                logger=logger
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