"""
Memory Service for Agent Memory Management
Implements short-term memory (thread-level persistence) and long-term memory (cross-thread persistence)
similar to LangGraph's memory system but adapted for Flask-SQLAlchemy.
"""

import uuid
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..db import db
from ..models.memory import ShortTermMemory, LongTermMemory, MemoryEmbedding
from ..llm.client import JarvusAIClient

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for managing agent memory using database-backed storage"""
    
    def __init__(self):
        self.llm_client = JarvusAIClient()
    
    # --- Short-Term Memory (Thread-Level Persistence) ---
    
    def save_checkpoint(
        self, 
        thread_id: str, 
        user_id: int, 
        agent_id: int, 
        state_data: Dict[str, Any],
        checkpoint_id: Optional[str] = None,
        parent_checkpoint_id: Optional[str] = None
    ) -> ShortTermMemory:
        """Save a checkpoint for short-term memory"""
        try:
            # Get the latest step number for this thread
            latest = ShortTermMemory.get_latest_checkpoint(thread_id, user_id)
            step_number = (latest.step_number + 1) if latest else 0
            
            # Generate checkpoint ID if not provided
            if not checkpoint_id:
                checkpoint_id = str(uuid.uuid4())
            
            checkpoint = ShortTermMemory(
                thread_id=thread_id,
                user_id=user_id,
                agent_id=agent_id,
                state_data=state_data,
                checkpoint_id=checkpoint_id,
                step_number=step_number,
                parent_checkpoint_id=parent_checkpoint_id
            )
            
            db.session.add(checkpoint)
            db.session.commit()
            
            logger.info(f"Saved checkpoint {checkpoint_id} for thread {thread_id} at step {step_number}")
            return checkpoint
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save checkpoint: {str(e)}")
            raise
    
    def get_latest_state(self, thread_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get the latest state for a thread"""
        checkpoint = ShortTermMemory.get_latest_checkpoint(thread_id, user_id)
        return checkpoint.state_data if checkpoint else None
    
    def get_state_history(self, thread_id: str, user_id: int) -> List[Dict[str, Any]]:
        """Get the complete state history for a thread"""
        checkpoints = ShortTermMemory.get_checkpoint_history(thread_id, user_id)
        return [checkpoint.to_dict() for checkpoint in checkpoints]
    
    def delete_thread(self, thread_id: str, user_id: int) -> bool:
        """Delete all checkpoints for a thread"""
        try:
            checkpoints = ShortTermMemory.query.filter_by(
                thread_id=thread_id, 
                user_id=user_id
            ).all()
            
            for checkpoint in checkpoints:
                db.session.delete(checkpoint)
            
            db.session.commit()
            logger.info(f"Deleted {len(checkpoints)} checkpoints for thread {thread_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete thread {thread_id}: {str(e)}")
            return False
    
    # --- Long-Term Memory (Cross-Thread Persistence) ---
    
    def store_memory(
        self,
        user_id: int,
        namespace: str,
        memory_data: Dict[str, Any],
        memory_type: str = 'fact',
        importance_score: float = 1.0,
        search_text: Optional[str] = None,
        memory_id: Optional[str] = None
    ) -> LongTermMemory:
        """Store a new memory in long-term storage"""
        try:
            if not memory_id:
                memory_id = str(uuid.uuid4())
            
            # Check if memory already exists
            existing = LongTermMemory.get_memory(user_id, namespace, memory_id)
            if existing:
                # Update existing memory
                existing.memory_data.update(memory_data)
                existing.importance_score = importance_score
                existing.last_accessed = datetime.utcnow()
                if search_text:
                    existing.search_text = search_text
                db.session.commit()
                logger.info(f"Updated existing memory {memory_id} in namespace {namespace}")
                return existing
            
            # Create new memory
            memory = LongTermMemory(
                user_id=user_id,
                namespace=namespace,
                memory_id=memory_id,
                memory_data=memory_data,
                memory_type=memory_type,
                importance_score=importance_score,
                search_text=search_text
            )
            
            db.session.add(memory)
            db.session.commit()
            
            logger.info(f"Stored new memory {memory_id} in namespace {namespace}")
            return memory
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to store memory: {str(e)}")
            raise
    
    def search_memories(
        self, 
        user_id: int, 
        namespace: str, 
        query: Optional[str] = None, 
        limit: int = 10
    ) -> List[LongTermMemory]:
        """Search memories by namespace and optional query"""
        try:
            memories = LongTermMemory.search_memories(user_id, namespace, query, limit)
            
            # Update access times for retrieved memories
            for memory in memories:
                memory.update_access_time()
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories: {str(e)}")
            return []
    
    def get_memory(self, user_id: int, namespace: str, memory_id: str) -> Optional[LongTermMemory]:
        """Get a specific memory by ID"""
        try:
            memory = LongTermMemory.get_memory(user_id, namespace, memory_id)
            if memory:
                memory.update_access_time()
            return memory
        except Exception as e:
            logger.error(f"Failed to get memory {memory_id}: {str(e)}")
            return None
    
    def delete_memory(self, user_id: int, namespace: str, memory_id: str) -> bool:
        """Delete a specific memory"""
        try:
            memory = LongTermMemory.get_memory(user_id, namespace, memory_id)
            if memory:
                db.session.delete(memory)
                db.session.commit()
                logger.info(f"Deleted memory {memory_id} from namespace {namespace}")
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete memory {memory_id}: {str(e)}")
            return False
    
    # --- Memory Integration with LLM ---
    
    def get_context_for_conversation(
        self, 
        user_id: int, 
        thread_id: str, 
        current_message: str,
        max_memories: int = 5
    ) -> str:
        """Get relevant context from both short-term and long-term memory"""
        context_parts = []
        
        # Get short-term memory (conversation history)
        latest_state = self.get_latest_state(thread_id, user_id)
        if latest_state and 'messages' in latest_state:
            # Get last few messages for context
            messages = latest_state['messages'][-6:]  # Last 3 exchanges
            if messages:
                context_parts.append("## Recent Conversation")
                for msg in messages:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    if content:
                        context_parts.append(f"{role.title()}: {content}")
        
        # Get long-term memories relevant to current message
        memories = self.search_memories(
            user_id=user_id,
            namespace="memories",
            query=current_message,
            limit=max_memories
        )
        
        if memories:
            context_parts.append("## Relevant Memories")
            for memory in memories:
                memory_text = memory.memory_data.get('text', '')
                if memory_text:
                    context_parts.append(f"- {memory_text}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def extract_and_store_memories(
        self, 
        user_id: int, 
        conversation_messages: List[Dict[str, str]],
        agent_id: int
    ) -> List[str]:
        """Extract potential memories from conversation and store them"""
        stored_memories = []
        
        # Simple memory extraction logic - can be enhanced with LLM
        for message in conversation_messages:
            content = message.get('content', '').lower()
            role = message.get('role', '')
            
            # Look for memory triggers
            if role == 'user' and any(trigger in content for trigger in ['remember', 'my name is', 'i am', 'i like', 'i prefer']):
                # Extract potential memory
                memory_text = message.get('content', '')
                
                # Determine memory type and importance
                memory_type = 'fact'
                importance = 1.0
                
                if 'name' in content:
                    memory_type = 'identity'
                    importance = 2.0
                elif any(word in content for word in ['like', 'love', 'prefer']):
                    memory_type = 'preference'
                    importance = 1.5
                
                # Store the memory
                try:
                    memory = self.store_memory(
                        user_id=user_id,
                        namespace="memories",
                        memory_data={'text': memory_text, 'source': 'conversation'},
                        memory_type=memory_type,
                        importance_score=importance,
                        search_text=memory_text
                    )
                    stored_memories.append(memory.memory_id)
                    logger.info(f"Extracted and stored memory: {memory_text[:50]}...")
                except Exception as e:
                    logger.error(f"Failed to store extracted memory: {str(e)}")
        
        return stored_memories


class MemoryConfig:
    """Configuration for memory management"""
    
    def __init__(self, thread_id: str, user_id: int, agent_id: int):
        self.thread_id = thread_id
        self.user_id = user_id
        self.agent_id = agent_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to configuration dictionary"""
        return {
            "configurable": {
                "thread_id": self.thread_id,
                "user_id": self.user_id,
                "agent_id": self.agent_id
            }
        }


# Global memory service instance
memory_service = MemoryService() 