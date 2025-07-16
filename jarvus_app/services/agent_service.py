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
from ..services.browser_http_client import sync_take_screenshot_auto

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
from jarvus_app import Config
        

logger = logging.getLogger(__name__)


class AgentService:
    """Enhanced agent service with memory management capabilities"""
    
    # Configuration constants for smart thread management
    NEW_CONVERSATION_TIMEOUT_MINUTES = 30  # Time gap to consider new conversation
    MAX_WORKING_MEMORY_CHECKPOINTS = 20    # Max checkpoints to keep per thread
    WORKING_MEMORY_CONTEXT_LIMIT = 10      # Max messages to include in context
    LLM_ANALYSIS_TIMEOUT_SECONDS = 5       # Timeout for LLM conversation analysis
    ENABLE_LLM_CONVERSATION_DETECTION = True  # Enable/disable LLM-based detection
    
    def __init__(self):
        self.llm_client = JarvusAIClient()
    
    def get_agent(self, agent_id: int, user_id: str) -> History:
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

    def create_agent(self, user_id: str, name: str, tools: Optional[List[str]] = None, description: str = None) -> History:
        """Create a new agent with memory initialization"""
        if not name:
            abort(400, 'Agent name is required.')
        
        # Always include Google Docs tools for all agents
        default_tools = ['web']
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
    
    def delete_agent(self, agent_id: int, user_id: str) -> bool:
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
        current_task=None,
        logger=None,
        mentions=None,  # Add mentions parameter
        execution_type="chat"  # NEW PARAM
    ):
        """Process a message with full memory context and tool orchestration."""
        if logger is None:
            logger = logging.getLogger(__name__)
        
        # Smart thread ID management
        thread_id = self._get_or_create_thread_id(agent_id, user_id, user_message, thread_id)
        logger.info(f"Using thread_id: {thread_id} for agent {agent_id}, user {user_id}, execution_type={execution_type}")
        
        # Step 1: Get context
        agent, allowed_tools, memory_info, messages, current_state = self._get_context_for_message(
            agent_id, user_id, user_message, thread_id, web_search_enabled, current_task #, screenshot_data
        )
        
        # Step 2: If mentions are present, add them as hints to the user message
        if mentions:
            mention_hints = self._create_mention_hints(mentions, allowed_tools)
            if mention_hints:
                # Find the user message (should be the last message) and append the hint
                for i, msg in enumerate(messages):
                    if msg.get('role') == 'user' and msg.get('content') == user_message:
                        messages[i]['content'] = f"{user_message}\n\n{mention_hints}"
                        logger.info(f"Added mention hints to user message: {mention_hints}")
                        break
        
        # Use all allowed tools (mentions are just hints, not restrictions)
        filtered_tools = allowed_tools
        
        print("[DEBUG] allowed_tools", allowed_tools)
        # print("[DEBUG] conversation_context_length", len(conversation_context))
        # print("[DEBUG] conversation_context", conversation_context[-2:] if len(conversation_context) >= 2 else conversation_context)
        # print("[DEBUG] filtered_tools", filtered_tools)
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
        final_assistant_message, _ = self.execution_agent(
            user_id=user_id,
            allowed_tools=filtered_tools if len(filtered_tools)!= 0 else None,
            messages=orchestration_messages,
            tool_choice=tool_choice,
            logger=logger
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
        
        # Save conversation to working memory (short-term memory)
        if final_assistant_message:
            # Add the assistant's response to the current state
            current_state['messages'].append({
                'role': 'assistant',
                'content': final_assistant_message,
                'timestamp': datetime.utcnow().isoformat()
            })
            # Branch memory update logic based on execution_type
            if execution_type == "chat":
                # Standard memory update
                memory_service.save_checkpoint(
                    thread_id=thread_id,
                    user_id=user_id,
                    agent_id=agent_id,
                    state_data=current_state
                )
            elif execution_type == "todo_generation":
                # Custom logic for todo generation (e.g., don't save to working memory)
                pass
            elif execution_type == "workflow_step":
                # Custom logic for workflow step
                memory_service.save_checkpoint(
                    thread_id=thread_id,
                    user_id=user_id,
                    agent_id=agent_id,
                    state_data=current_state
                )
            else:
                # Default to standard memory update
                memory_service.save_checkpoint(
                    thread_id=thread_id,
                    user_id=user_id,
                    agent_id=agent_id,
                    state_data=current_state
                )
            # logger.info(f"Saved working memory checkpoint for thread {thread_id} with {len(current_state['messages'])} messages")
            
            # Clean up old working memory checkpoints to prevent indefinite growth
            self._cleanup_old_working_memory(thread_id, user_id)
        
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

    def _initialize_agent_memory(self, user_id: str, agent_id: int):
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
            # logger.info(f"Initialized memory for agent {agent_id}")
        except Exception as e:
            logger.error(f"Failed to initialize memory for agent {agent_id}: {str(e)}")
    
    def _get_context_for_message(
        self,
        agent_id: int,
        user_id: str,
        user_message: str,
        thread_id: Optional[str],
        web_search_enabled: bool,
        current_task=None,
        # screenshot_data: Optional[str]
    ):
        from jarvus_app import config
        agent = self.get_agent(agent_id, user_id)
        allowed_tools = set(self.get_agent_tools(agent))
        if not web_search_enabled:
            allowed_tools.remove('web')
        allowed_tools = list(allowed_tools)
        # Get current state (working memory)
        current_state = memory_service.get_latest_state(thread_id, user_id)
        # logger.info(f"Retrieved working memory state for thread {thread_id}: {current_state is not None}")
        if not current_state:
            current_state = {
                'messages': [],
                'agent_id': agent_id,
                'user_id': user_id,
                'thread_id': thread_id
            }
            # logger.info(f"Created new working memory state for thread {thread_id}")
        else:
            # logger.info(f"Found existing working memory with {len(current_state.get('messages', []))} messages")
            pass
        
        current_state['messages'].append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.utcnow().isoformat()
        })
        # 1. System instructions
        now_iso = datetime.now().isoformat()
        system_prompt = config.Config.CHATBOT_SYSTEM_PROMPT.strip().replace("{CURRENT_DATETIME}", now_iso)
        system_instructions = [
            "### System Instructions",
            system_prompt,
        ]
        
        # Add current task context
        task_text = current_task.text if current_task else "General tasks and conversation"
        system_instructions.extend([
            "",
            "### Current Task Context",
            f"You are currently working on: {task_text}",
            "When responding to the user, consider how your response relates to this current task.",
            "If the user's request is related to this task, prioritize helping them complete it.",
            "If the user's request is unrelated, you can still help but be mindful of their current focus."
        ])
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
        conversation_messages = current_state['messages'][-self.WORKING_MEMORY_CONTEXT_LIMIT:] if 'messages' in current_state else []
        # logger.info(f"Retrieved {len(conversation_messages)} messages from working memory for thread {thread_id}")
        for msg in conversation_messages:
            if msg.get('content') and msg['role'] in ['user', 'assistant']:
                content = msg['content']
                if not (content.startswith('{') and content.endswith('}')) and 'tool_call' not in content.lower():
                    working_turns.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
        messages.extend(working_turns)
        # logger.info(f"Added {len(working_turns)} working memory turns to context")
        # 4. Current user query (always last)
        # if screenshot_data:
        #     # Create proper multimodal content with text and image
        #     # from azure.ai.inference.models import TextContentItem, ImageContentItem
        #     # content_items = [TextContentItem(text=user_message)]
        #     # Create data URL for the screenshot
        #     data_url = f"data:image/png;base64,{screenshot_data}"
        #     # content_items.append(ImageContentItem(image_url=data_url))
        #     # user_message_obj = UserMessage(content=content_items)
        #     messages.append(
        #         {
        #             'role': 'user',
        #             'content': [
        #                 {'type': 'text', 'text': user_message},
        #                 {'type': 'image_url', 'image_url': {'url': data_url}}
        #             ]
        #         }
        #     )
        # else:
        # Regular text message
        messages.append({
            'role': 'user',
            'content': user_message
        })
        memory_info = {
            'thread_id': thread_id,
            'memory_context_used': True
        }
        return agent, allowed_tools, memory_info, messages, current_state

    def _detect_new_conversation(self, user_message: str, current_state: dict) -> bool:
        """
        Use LLM to detect if the user is starting a new conversation based on:
        1. Message content and context
        2. Time gap since last message
        3. Semantic analysis of conversation continuity
        """
        if not current_state or not current_state.get('messages'):
            return True
        
        # Check time gap first (if more than configured timeout, consider it a new conversation)
        if current_state.get('messages'):
            last_message = current_state['messages'][-1]
            if 'timestamp' in last_message:
                from datetime import datetime, timedelta
                try:
                    last_time = datetime.fromisoformat(last_message['timestamp'].replace('Z', '+00:00'))
                    current_time = datetime.utcnow()
                    time_diff = current_time - last_time.replace(tzinfo=None)
                    if time_diff > timedelta(minutes=self.NEW_CONVERSATION_TIMEOUT_MINUTES):
                        # logger.info(f"Time gap of {time_diff.total_seconds()/60:.1f} minutes detected, treating as new conversation")
                        return True
                except:
                    pass
        
        # Use LLM to analyze conversation continuity (if enabled)
        if self.ENABLE_LLM_CONVERSATION_DETECTION:
            return self._analyze_conversation_continuity_with_llm(user_message, current_state)
        else:
            # Fallback to simple keyword detection
            return self._fallback_conversation_detection(user_message)
    
    def _analyze_conversation_continuity_with_llm(self, user_message: str, current_state: dict) -> bool:
        """
        Use LLM to determine if the user message is starting a new conversation
        or continuing the existing one.
        """
        try:
            # Build conversation context for the LLM
            conversation_context = ""
            if current_state.get('messages'):
                # Get last 4 messages for context (to keep it focused)
                recent_messages = current_state['messages'][-4:] if len(current_state['messages']) > 4 else current_state['messages']
                for msg in recent_messages:
                    if msg.get('content') and msg.get('role') in ['user', 'assistant']:
                        conversation_context += f"{msg['role']}: {msg['content']}\n"
            
            # Create the analysis prompt
            analysis_prompt = f"""
You are analyzing conversation continuity. Determine if the user's message starts a new conversation or continues the existing one.

Recent conversation context:
{conversation_context.strip() if conversation_context else "No previous conversation"}

New user message: "{user_message}"

Analysis criteria:
- "NEW" if: greeting, new topic request, help request, topic change, reset command
- "CONTINUE" if: response to previous message, clarification, confirmation, follow-up question

Examples:
- "hello" → NEW
- "yes" → CONTINUE  
- "can you help me with something else?" → NEW
- "what about tomorrow?" → CONTINUE
- "let's start over" → NEW
- "that sounds good" → CONTINUE

Respond with ONLY "NEW" or "CONTINUE".
"""
            
            # Get LLM analysis
            analysis_messages = [
                {"role": "system", "content": "You are a conversation analysis expert. Respond with only 'NEW' or 'CONTINUE'."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            try:
                response = self.llm_client.create_chat_completion(analysis_messages)
                analysis_result = response['choices'][0]['message']['content'].strip().upper()
            except Exception as e:
                logger.warning(f"LLM analysis failed: {str(e)}")
                return self._fallback_conversation_detection(user_message)
            
            is_new_conversation = analysis_result == "NEW"
            
            # logger.info(f"LLM conversation analysis: '{analysis_result}' for message: '{user_message[:50]}...' (context: {len(conversation_context.split(chr(10)))} lines)")
            
            return is_new_conversation
            
        except Exception as e:
            logger.error(f"Failed to analyze conversation continuity with LLM: {str(e)}")
            # Fallback to simple keyword detection
            return self._fallback_conversation_detection(user_message)
    
    def _fallback_conversation_detection(self, user_message: str) -> bool:
        """
        Fallback conversation detection using simple keyword matching
        when LLM analysis fails.
        """
        new_conversation_indicators = [
            'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
            'start over', 'new conversation', 'reset', 'begin', 'let\'s start',
            'can you help me', 'i need help', 'i want to', 'i would like to'
        ]
        
        user_message_lower = user_message.lower().strip()
        
        for indicator in new_conversation_indicators:
            if indicator in user_message_lower:
                # logger.info(f"Fallback detection: found indicator '{indicator}' in message")
                return True
        
        return False

    def _get_or_create_thread_id(self, agent_id: int, user_id: str, user_message: str, existing_thread_id: str = None) -> str:
        """
        Smart thread ID management:
        - Use existing thread_id if provided
        - Create new thread_id if starting new conversation
        - Maintain continuity for ongoing conversations
        """
        if existing_thread_id:
            return existing_thread_id
        
        # Check if we should start a new conversation
        current_state = memory_service.get_latest_state(f"thread_{agent_id}_{user_id}", user_id)
        if self._detect_new_conversation(user_message, current_state):
            # Start new conversation with timestamp
            new_thread_id = f"thread_{agent_id}_{user_id}_{int(datetime.utcnow().timestamp())}"
            # logger.info(f"Detected new conversation, creating new thread_id: {new_thread_id}")
            return new_thread_id
        else:
            # Continue existing conversation
            thread_id = f"thread_{agent_id}_{user_id}"
            # logger.info(f"Continuing existing conversation with thread_id: {thread_id}")
            return thread_id

    def _create_mention_hints(self, mentions, allowed_tools):
        """Create user message hints based on @ mentions."""
        from jarvus_app.config import ALL_PIPEDREAM_APPS
        
        # Create mention-to-slug mapping from config
        mention_to_slug_mapping = {}
        for app in ALL_PIPEDREAM_APPS:
            if 'mention' in app:
                mention_to_slug_mapping[app['mention']] = app['slug']
        
        hint_tools = []
        for mention in mentions:
            tool_slug = mention_to_slug_mapping.get(mention.lower())
            if tool_slug and tool_slug in allowed_tools:
                hint_tools.append(tool_slug)
        
        if hint_tools:
            return f"TOOL HINT: Consider using these tools for this request: {', '.join(hint_tools)}"
        
        return ""

    def _select_tools_with_llm(self, user_message, allowed_tools, conversation_context=None):
        jarvus_ai = self.llm_client
        
        # Build context-aware prompt
        if conversation_context and len(conversation_context) > 1:
            # Include recent conversation context
            context_prompt = (
                "Given the following conversation context and the user's latest message, "
                "which tool(s) or tool category(ies) would you use to answer the message? "
                "Consider the full conversation context, not just the latest message in isolation. "
                "Pay special attention to:\n"
                "- If the user is confirming or continuing a previous workflow (like 'yes', 'ok', 'sure')\n"
                "- If the conversation is about creating, updating, or managing calendar events\n"
                "- If the conversation involves email, documents, or web searches\n"
                "- If the assistant previously mentioned using specific tools\n"
                "Respond with a JSON list of tool names or categories. Return the exact name that is provided. If none, return an empty list.\n\n"
                "Conversation Context:\n"
            )
            
            # Add recent conversation turns (last 4 turns to keep it focused)
            recent_context = conversation_context[-4:] if len(conversation_context) > 4 else conversation_context
            for msg in recent_context:
                if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
                    context_prompt += f"{msg['role']}: {msg['content']}\n"
            
            context_prompt += f"\nLatest User Message: {user_message}\n"
        else:
            # Fallback to original prompt for single messages
            context_prompt = (
                "Given the following user message and these tool categories, "
                "which tool(s) or tool category(ies) would you use to answer the message? "
                "Respond with a JSON list of tool names or categories. Return the exact name that is provided. If none, return an empty list.\n\n"
                f"User Message: {user_message}"
            )
        
        tool_selection_messages = [
            {"role": "system", "content": context_prompt},
            {"role": "system", "content": f"Available tool categories: {allowed_tools}"}
        ]
        tool_selection_response = jarvus_ai.create_chat_completion(tool_selection_messages)
        # print("[DEBUG] tool_selection_response:", tool_selection_response)
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
        # print("[DEBUG] needed_tools_or_categories:", needed_tools_or_categories)
        filtered_tools = [
            t for t in allowed_tools
            if t in needed_tools_or_categories or (hasattr(t, 'category') and t.category.value in needed_tools_or_categories)
        ]
        return filtered_tools

    def planner_agent(self, user_message, allowed_tools, memory_context=None):
        """
        Use the LLM to generate a step-by-step plan for the user's request.
        Returns a list of plan steps, each a dict with 'tool' and 'parameters'.
        """
        jarvus_ai = self.llm_client
        planning_prompt = Config.AGENT_PLANNING_PROMPT.format(allowed_tools=allowed_tools)
        planning_messages = [
            {"role": "system", "content": planning_prompt},
        ]
        if memory_context:
            planning_messages.append({"role": "system", "content": f"### Memory Context\n{memory_context}"})
        planning_messages.append({"role": "user", "content": user_message})
        planning_response = jarvus_ai.create_chat_completion(planning_messages, logger=logger)
        logger.info(f"Azure AI response: {planning_response}")

        def parse_plan_steps(plan_steps):
            # If plan_steps is a string, try to parse it as JSON
            if isinstance(plan_steps, str):
                try:
                    plan_steps = json.loads(plan_steps)
                except Exception as e:
                    # Optionally log or handle the error
                    print(f"Failed to parse plan steps: {e}")
                    return []
            # If plan_steps is a list, return as is
            if isinstance(plan_steps, list):
                return plan_steps
        
        filtered_plan = []
        plan = parse_plan_steps(planning_response['choices'][0]['message']['content'])
        for step in plan:
            filtered_plan.append(step)
        
        return filtered_plan
        # plan = parse_plan_from_response(planning_response)
        # # Ensure plan is a list of dicts with 'tool' and 'parameters'
        # filtered_plan = []
        # for step in plan:
        #     if isinstance(step, dict) and 'tool' in step and 'parameters' in step:
        #         filtered_plan.append(step)
        # return filtered_plan

    def _format_tool_result_for_llm(self, tool_result):
        """
        Format a tool result dict (from pipedream or other tool calls) into a string for the LLM.
        Returns a summary first, then the complete payload.
        """
        import json
        
        instruction = "Check this tool call response to see if the tool call succeeded and returned what was requested by user. If so, return the result without a calling a tool again."
        # If it's already a string, return it as is
        if isinstance(tool_result, str):
            return tool_result + "\n" + instruction
        
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
                return f"SUMMARY: {summary}\n\nCOMPLETE RESULT:\n{full_payload}\n{instruction}"
            except Exception:
                return f"SUMMARY: {summary}\n\nCOMPLETE RESULT:\n{str(tool_result)}\n{instruction}"
        
        # For any other type, convert to string
        return str(tool_result) + "\n" + instruction

    def execution_agent(self, user_id, allowed_tools, messages, tool_choice, logger):
        """Orchestrate tool calling logic for both legacy and enhanced chat handlers, with plan adherence."""
        from jarvus_app.utils.token_utils import get_valid_jwt_token
        jarvus_ai = self.llm_client
        # Ensure tools are discovered if needed (now optimized to avoid repeated discovery)
        # No longer pass session_data; tool discovery uses DB cache or in-memory registry only
        if allowed_tools:
            ensure_tools_discovered(user_id)
            # Only include SDK tools that are in allowed_tools
            tool_to_app_mapping = pipedream_tool_service.get_tool_to_app_mapping()
            all_sdk_tools = pipedream_tool_service.get_all_sdk_tools()

            sdk_tools = [
                tool for tool in all_sdk_tools
                if tool_to_app_mapping.get(tool.function.name) in allowed_tools
            ]
        
        # # Use DB-cached tool discovery for allowed app slugs
        # from jarvus_app.services.pipedream_tool_registry import get_or_discover_tools_for_user_apps
        # sdk_tools = get_or_discover_tools_for_user_apps(user_id, allowed_tools)
        # print("[DEBUG] allowed_sdk_tools", sdk_tools)
        new_messages = []
        logger.info(f"Messages passed into execution agent: {messages} (execution_agent)")
        try:
            # while True:
            logger.info("Calling Azure AI for completion (execution_agent)")
            if not allowed_tools:
                response = jarvus_ai.create_chat_completion(
                    messages=messages,
                    logger=logger
                )
            else:
                response = jarvus_ai.create_chat_completion(
                    messages=messages,
                    tools=sdk_tools,
                    tool_choice=tool_choice,
                    logger=logger
                )
            logger.info("Received response from Azure AI (execution_agent)")
            choice = response.choices[0]
            msg = choice.message
            assistant_msg = AssistantMessage(content=msg.content if msg.content is not None else "", tool_calls=msg.tool_calls)
            messages.append(assistant_msg)
            new_messages.append({'role': 'assistant', 'content': assistant_msg.content})
            if not msg.tool_calls:
                logger.info("No tool calls in response - conversation complete (execution_agent)")
            else:
                logger.info(f"Processing {len(msg.tool_calls)} tool calls (execution_agent)")
                for call in msg.tool_calls:
                    retries = 0
                    max_retries = 3
                    current_call = call
                    
                    while retries < max_retries:
                        tool_name = current_call.function.name
                        tool_args = json.loads(current_call.function.arguments) if current_call.function.arguments else {}
                        logger.info(f"Executing tool: {tool_name} with args: {tool_args} (execution_agent)")
                        try:
                            # Get the app slug for this tool from the mapping
                            app_slug = tool_to_app_mapping.get(tool_name, "google_docs")  # fallback
                            external_user_id = str(user_id)
                            jwt_token = get_valid_jwt_token()
                            tool_result = pipedream_tool_service.execute_tool(
                                external_user_id=external_user_id,
                                app_slug=app_slug,
                                tool_name=tool_name,
                                tool_args=tool_args,
                                jwt_token=jwt_token
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
                                logger.error(f"Max retries reached for tool call '{tool_name}'. Moving on. (execution_agent)")
                                break
                            logger.info("Prompting LLM again after tool call failure (execution_agent)")
                            response = jarvus_ai.create_chat_completion(
                                messages=messages,
                                tools=sdk_tools,
                                tool_choice="auto",
                                logger=logger
                            )
                            logger.info("Received response from Azure AI (retry, execution_agent)")
                            choice = response.choices[0]
                            msg = choice.message
                            assistant_msg = AssistantMessage(content=msg.content if msg.content is not None else "", tool_calls=msg.tool_calls)
                            messages.append(assistant_msg)
                            new_messages.append({'role': 'assistant', 'content': assistant_msg.content})
                            # logger.info(f"Assistant message (retry, execution_agent): {assistant_msg}")
                            if not msg.tool_calls:
                                logger.info("No tool calls in response after retry - conversation complete (execution_agent)")
                                break
                            current_call = msg.tool_calls[0]

            # Return the last assistant message
            final_assistant_message = ""
            if new_messages:
                for msg in reversed(new_messages):
                    if msg.get('role') == 'assistant' and msg.get('content'):
                        final_assistant_message = msg.get('content')
                        break
            return final_assistant_message, messages
        except Exception as e:
            logger.error(f"Error in execution_agent: {str(e)}", exc_info=True)
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

    def _cleanup_old_working_memory(self, thread_id: str, user_id: str, max_checkpoints: int = None):
        """
        Clean up old working memory checkpoints to prevent indefinite growth.
        Keeps the most recent checkpoints and removes older ones.
        """
        if max_checkpoints is None:
            max_checkpoints = self.MAX_WORKING_MEMORY_CHECKPOINTS
        """
        Clean up old working memory checkpoints to prevent indefinite growth.
        Keeps the most recent checkpoints and removes older ones.
        """
        try:
            from jarvus_app.models.memory import ShortTermMemory
            
            # Get all checkpoints for this thread, ordered by step number
            checkpoints = ShortTermMemory.query.filter_by(
                thread_id=thread_id, 
                user_id=user_id
            ).order_by(ShortTermMemory.step_number.desc()).all()
            
            # If we have more than max_checkpoints, delete the oldest ones
            if len(checkpoints) > max_checkpoints:
                checkpoints_to_delete = checkpoints[max_checkpoints:]
                for checkpoint in checkpoints_to_delete:
                    db.session.delete(checkpoint)
                db.session.commit()
                # logger.info(f"Cleaned up {len(checkpoints_to_delete)} old working memory checkpoints for thread {thread_id}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old working memory: {str(e)}")
            db.session.rollback()

    def validation_agent(self, instruction, success_criteria, agent_response, error_handling, extract=None, logger=None):
        """LLM-based validation/reflection for a workflow step, always returning a summary and extracted outputs."""
        # Compose the prompt for validation and extraction
        extract_clause = ""
        if extract:
            extract_clause = (
                f"\nAdditionally, extract the following output variables from the agent's response/tool result and return them in an 'extracted' field in the JSON. "
                f"For each variable in {extract}, extract them from the tool result and include it as-is (do not summarize or modify unless the variable explicitly requires summarization). "
                f"If the variable is not present, try to infer it from the response. "
                # f"If the variable is needs to be a summary, you may summarize it, otherwise preserve the original output."
            )
        # --- NEW: Add explicit LLM instruction to ignore/summarize unnecessary or repetitive content in any document/tool result ---
        llm_cleanup_instruction = (
            "When reviewing the tool response, you must ignore or summarize unnecessary, repetitive, or boilerplate content, excessive formatting, irrelevant metadata, and any content that does not contribute to the main purpose or meaning of the result. "
            "Focus your validation, extraction, and summary only on the main content and relevant information. Do not include unsubscribe links, copyright footers, repeated URLs, or generic disclaimers in your summary or extracted outputs. If the content is too long or verbose, summarize or truncate as needed. "
        )
        reflection_prompt = (
            "You are an expert workflow validator. "
            + llm_cleanup_instruction +
            "Given the following step instruction, success criteria, the agent's response, and the error handling instructions, "
            "determine if the step was completed successfully. If variables that need to be extracted are not present, the step should be marked as a fail and you should recommend a retry. "
            "If not, suggest what to do next. When doing so, read the error message carefully, and suggest how the tool call can be improved, using the error handling instructions if relevant. "
            "Always provide a concise 1-2 sentence summary of what was attempted and the outcome for use as context in future steps, regardless of success. "
            "Respond in JSON: {\"success\": true/false, \"reason\": \"...\", \"retry\": true/false, \"suggestion\": \"...\", \"summary\": \"...\", \"extracted\": { ... }}\n"
            "Respond with ONLY valid JSON, no comments, no extra text, no truncation."
            f"Step Instruction: {instruction}\n"
            f"Success Criteria: {success_criteria}\n"
            f"Error Handling: {error_handling}\n"
            f"{extract_clause}\n"
            f"Agent Response: {agent_response}\n"
        )
        reflection_messages = [
            {"role": "system", "content": reflection_prompt}
        ]
        try:
            logger.info("======== Validation Agent Called ========")
            reflection_response = self.llm_client.create_chat_completion(reflection_messages, logger=logger)
            import json as _json
            content = reflection_response['choices'][0]['message']['content']
            try:
                reflection = _json.loads(content)
            except Exception as e1:
                # Try to extract JSON object from the string using regex
                import re
                logger.warning(f"[AgentService] LLM returned non-JSON output, attempting to extract JSON. Raw output: {content}")
                match = re.search(r'\{[\s\S]*\}', content)
                if match:
                    json_str = match.group(0)
                    # Remove JS-style comments
                    json_str = re.sub(r'//.*', '', json_str)
                    # Remove trailing commas before } or ]
                    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
                    try:
                        reflection = _json.loads(json_str)
                    except Exception as e2:
                        logger.warning(f"[AgentService] Failed to parse cleaned JSON: {e2}. Returning fallback reflection.")
                        raise e2
                else:
                    logger.warning(f"[AgentService] No JSON object found in LLM output. Returning fallback reflection.")
                    raise e1
            return reflection
        except Exception as e:
            if logger:
                logger.warning(f"[AgentService] LLM validation failed: {str(e)}. Returning fallback reflection.")
            # Fallback: treat as failed with a basic summary
            return {
                'success': False,
                'reason': str(e),
                'retry': False,
                'suggestion': '',
                'summary': f"Validation failed: {str(e)}",
                'extracted': {}
            }

    def procedural_memory_update_agent(self, previous_procedural_memory, new_reflections_feedback, logger=None):
        """LLM-based update of procedural memory given previous memory and new reflections/feedback."""
        summary_prompt = (
            "You are an expert at maintaining procedural memory for workflow execution. "
            "Given the previous procedural memory and the following new reflections/feedback from the latest run, "
            "update and improve the procedural memory so that future executions are more reliable and efficient. "
            "Respond with the improved procedural memory content as a string.\n"
            f"Previous Procedural Memory:\n{previous_procedural_memory}\n"
            f"New Reflections/Feedback:\n{new_reflections_feedback}\n"
        )
        summary_messages = [
            {"role": "system", "content": summary_prompt}
        ]
        try:
            summary_response = self.llm_client.create_chat_completion(summary_messages, logger=logger)
            improved_content = summary_response['choices'][0]['message']['content']
            return improved_content
        except Exception as e:
            if logger:
                logger.error(f"[AgentService] Failed to update procedural memory: {str(e)}")
            return previous_procedural_memory


# Global enhanced agent service instance
agent_service = AgentService() 