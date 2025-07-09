"""
Enhanced Agent Service with Memory Management
Integrates short-term and long-term memory with agent interactions.
"""

import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from flask_login import current_user
from flask import abort

from ..db import db
from ..models.history import History, InteractionHistory
from ..models.memory import ShortTermMemory, LongTermMemory
from .memory_service import memory_service, MemoryConfig
from ..llm.client import JarvusAIClient

logger = logging.getLogger(__name__)


class EnhancedAgentService:
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
    
    def process_message_with_memory(
        self, 
        agent_id: int, 
        user_id: int, 
        user_message: str,
        thread_id: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Process a message with full memory context"""
        
        # Generate thread ID if not provided
        if not thread_id:
            thread_id = f"thread_{agent_id}_{user_id}_{int(datetime.utcnow().timestamp())}"
        
        agent = self.get_agent(agent_id, user_id)
        
        # Get memory context
        memory_context = memory_service.get_context_for_conversation(
            user_id=user_id,
            thread_id=thread_id,
            current_message=user_message
        )
        
        # Get current conversation state
        current_state = memory_service.get_latest_state(thread_id, user_id)
        if not current_state:
            current_state = {
                'messages': [],
                'agent_id': agent_id,
                'user_id': user_id,
                'thread_id': thread_id
            }
        
        # Add user message to state
        current_state['messages'].append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Prepare messages for LLM with memory context
        messages = []
        
        # Add system message with memory context
        system_message = f"""You are a helpful AI assistant with access to user memories and conversation history.

{memory_context if memory_context else "No specific memories or context available."}

Please be helpful, accurate, and remember important information about the user when appropriate."""
        
        messages.append({'role': 'system', 'content': system_message})
        
        # Add conversation history (last 10 messages to avoid token limits)
        conversation_messages = current_state['messages'][-10:]
        for msg in conversation_messages:
            if msg.get('content'):
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        # Get response from LLM
        try:
            response = self.llm_client.create_chat_completion(
                messages=messages,
                max_tokens=2048,
                temperature=0.7
            )
            
            if 'error' in response:
                logger.error(f"LLM error: {response['error']}")
                assistant_message = "I apologize, but I'm experiencing technical difficulties. Please try again."
            else:
                assistant_message = response.get('assistant', {}).get('content', 'I apologize, but I couldn\'t generate a response.')
            
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")
            assistant_message = "I apologize, but I'm experiencing technical difficulties. Please try again."
        
        # Add assistant response to state
        current_state['messages'].append({
            'role': 'assistant',
            'content': assistant_message,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Save checkpoint for short-term memory
        try:
            memory_service.save_checkpoint(
                thread_id=thread_id,
                user_id=user_id,
                agent_id=agent_id,
                state_data=current_state
            )
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {str(e)}")
        
        # Extract and store memories from the conversation
        try:
            conversation_messages = current_state['messages'][-2:]  # Last exchange
            # Attempt to extract tool_call and feedback from the last exchange
            tool_call = None
            feedback = None
            # Look for a tool call in the assistant's message (if structured)
            if conversation_messages and len(conversation_messages) == 2:
                user_msg, assistant_msg = conversation_messages
                # Example: tool call info is in assistant_msg['tool_call'] or similar
                if isinstance(assistant_msg, dict):
                    tool_call = assistant_msg.get('tool_call')
                    feedback = user_msg.get('feedback')  # If user gave feedback after tool use
            stored_memories = memory_service.extract_and_store_memories(
                user_id=user_id,
                conversation_messages=conversation_messages,
                agent_id=agent_id,
                tool_call=tool_call,
                feedback=feedback
            )
            if stored_memories:
                logger.info(f"Stored {len(stored_memories)} new memories")
        except Exception as e:
            logger.error(f"Failed to extract memories: {str(e)}")
        
        # Update agent's message history (for backward compatibility)
        agent.messages = current_state['messages']
        db.session.commit()
        
        # Save interaction for display
        try:
            self._save_interaction(agent, user_message, assistant_message)
        except Exception as e:
            logger.error(f"Failed to save interaction: {str(e)}")
        
        return assistant_message, {
            'thread_id': thread_id,
            'stored_memories': stored_memories if 'stored_memories' in locals() else [],
            'memory_context_used': bool(memory_context)
        }
    
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
    
    def get_agent_memory_context(self, agent_id: int, user_id: int, thread_id: str) -> Dict[str, Any]:
        """Get comprehensive memory context for an agent"""
        try:
            # Get short-term memory
            short_term_state = memory_service.get_latest_state(thread_id, user_id)
            short_term_history = memory_service.get_state_history(thread_id, user_id)
            
            # Get long-term memories
            long_term_memories = memory_service.search_memories(
                user_id=user_id,
                namespace="memories",
                limit=20
            )
            
            return {
                'short_term': {
                    'current_state': short_term_state,
                    'history': short_term_history
                },
                'long_term': {
                    'memories': [memory.to_dict() for memory in long_term_memories],
                    'total_count': len(long_term_memories)
                },
                'thread_id': thread_id,
                'agent_id': agent_id,
                'user_id': user_id
            }
        except Exception as e:
            logger.error(f"Failed to get memory context: {str(e)}")
            return {
                'short_term': {'current_state': None, 'history': []},
                'long_term': {'memories': [], 'total_count': 0},
                'thread_id': thread_id,
                'agent_id': agent_id,
                'user_id': user_id,
                'error': str(e)
            }
    
    def delete_agent_memory(self, agent_id: int, user_id: int) -> bool:
        """Delete all memory associated with an agent"""
        try:
            # Delete short-term memory for all threads of this agent
            short_term_memories = ShortTermMemory.query.filter_by(
                agent_id=agent_id,
                user_id=user_id
            ).all()
            
            for memory in short_term_memories:
                db.session.delete(memory)
            
            # Delete long-term memories associated with this agent
            long_term_memories = LongTermMemory.query.filter_by(
                user_id=user_id,
                namespace="memories"
            ).all()
            
            # Filter memories that mention this agent
            for memory in long_term_memories:
                memory_data = memory.memory_data or {}
                if memory_data.get('agent_id') == agent_id:
                    db.session.delete(memory)
            
            db.session.commit()
            logger.info(f"Deleted memory for agent {agent_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete agent memory: {str(e)}")
            return False
    
    def search_memories(self, user_id: int, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search user memories"""
        try:
            memories = memory_service.search_memories(
                user_id=user_id,
                namespace="memories",
                query=query,
                limit=limit
            )
            return [memory.to_dict() for memory in memories]
        except Exception as e:
            logger.error(f"Failed to search memories: {str(e)}")
            return []
    
    def store_user_memory(
        self, 
        user_id: int, 
        memory_text: str, 
        memory_type: str = 'fact',
        importance: float = 1.0
    ) -> Optional[str]:
        """Store a user memory"""
        try:
            memory = memory_service.store_memory(
                user_id=user_id,
                namespace="memories",
                memory_data={'text': memory_text, 'source': 'manual'},
                memory_type=memory_type,
                importance_score=importance,
                search_text=memory_text
            )
            return memory.memory_id
        except Exception as e:
            logger.error(f"Failed to store user memory: {str(e)}")
            return None


# Global enhanced agent service instance
enhanced_agent_service = EnhancedAgentService() 