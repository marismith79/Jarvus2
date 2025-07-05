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
from ..models.memory import ShortTermMemory, LongTermMemory, MemoryEmbedding, HierarchicalMemory
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
        memory_id: Optional[str] = None,
        importance_score: float = 1.0,
        search_text: Optional[str] = None
    ) -> LongTermMemory:
        """Store a long-term memory"""
        try:
            # Generate memory ID if not provided
            if not memory_id:
                memory_id = str(uuid.uuid4())
            
            # Create or update memory
            memory = LongTermMemory.get_memory(user_id, namespace, memory_id)
            if memory:
                # Update existing memory
                memory.memory_data = memory_data
                memory.memory_type = memory_type
                memory.importance_score = importance_score
                memory.search_text = search_text
                memory.updated_at = datetime.utcnow()
            else:
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
            logger.info(f"Stored memory {memory_id} in namespace {namespace}")
            return memory
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to store memory: {str(e)}")
            raise
    
    def store_episodic_memory(
        self, 
        user_id: int, 
        episode_type: str, 
        episode_data: Dict[str, Any],
        importance_score: float = 1.0
    ) -> LongTermMemory:
        """Store an episodic memory (user action, feedback, etc.)"""
        return self.store_memory(
            user_id=user_id,
            namespace='episodes',
            memory_data={
                'type': episode_type,
                'data': episode_data,
                'timestamp': datetime.utcnow().isoformat()
            },
            memory_type='episode',
            importance_score=importance_score,
            search_text=json.dumps(episode_data)
        )
    
    def store_semantic_memory(
        self, 
        user_id: int, 
        fact_type: str, 
        fact_data: Dict[str, Any],
        importance_score: float = 1.0
    ) -> LongTermMemory:
        """Store a semantic memory (fact, preference, etc.)"""
        return self.store_memory(
            user_id=user_id,
            namespace='semantic',
            memory_data={
                'type': fact_type,
                'data': fact_data
            },
            memory_type='fact',
            importance_score=importance_score,
            search_text=json.dumps(fact_data)
        )
    
    def store_procedural_memory(
        self, 
        user_id: int, 
        procedure_name: str, 
        procedure_data: Dict[str, Any],
        importance_score: float = 1.0
    ) -> LongTermMemory:
        """Store a procedural memory (workflow, how-to, etc.)"""
        return self.store_memory(
            user_id=user_id,
            namespace='procedures',
            memory_data={
                'name': procedure_name,
                'data': procedure_data
            },
            memory_type='procedure',
            importance_score=importance_score,
            search_text=json.dumps(procedure_data)
        )
    
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
    
    # --- Hierarchical Memory (Contextual State Management) ---
    
    def create_hierarchical_context(
        self,
        user_id: int,
        name: str,
        description: str,
        context_data: Dict[str, Any],
        parent_id: Optional[str] = None,
        influence_rules: Optional[Dict[str, Any]] = None,
        memory_type: str = 'context',
        priority: int = 0
    ) -> HierarchicalMemory:
        """Create a hierarchical context that can influence other memories"""
        try:
            memory_id = str(uuid.uuid4())
            
            # Calculate level and path
            level = 0
            path = name
            
            if parent_id:
                parent = HierarchicalMemory.query.filter_by(
                    memory_id=parent_id, 
                    user_id=user_id
                ).first()
                if parent:
                    level = parent.level + 1
                    path = f"{parent.path}/{name}" if parent.path else name
            
            context = HierarchicalMemory(
                user_id=user_id,
                memory_id=memory_id,
                parent_id=parent_id,
                level=level,
                path=path,
                name=name,
                description=description,
                context_data=context_data,
                influence_rules=influence_rules or {},
                memory_type=memory_type,
                priority=priority
            )
            
            db.session.add(context)
            db.session.commit()
            
            logger.info(f"Created hierarchical context {name} at level {level}")
            return context
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create hierarchical context: {str(e)}")
            raise
    
    def get_active_contexts(self, user_id: int) -> List[HierarchicalMemory]:
        """Get all active contexts for a user"""
        try:
            contexts = HierarchicalMemory.get_active_contexts(user_id)
            return contexts
        except Exception as e:
            logger.error(f"Failed to get active contexts: {str(e)}")
            return []
    
    def get_context_influence(self, memory_id: str, user_id: int) -> Dict[str, Any]:
        """Get the combined influence context from a memory and its ancestors"""
        try:
            memory = HierarchicalMemory.query.filter_by(
                memory_id=memory_id, 
                user_id=user_id
            ).first()
            
            if memory:
                return memory.get_influence_context()
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get context influence: {str(e)}")
            return {}
    
    def get_root_contexts(self, user_id: int) -> List[HierarchicalMemory]:
        """Get all root-level contexts for a user"""
        try:
            return HierarchicalMemory.get_root_contexts(user_id)
        except Exception as e:
            logger.error(f"Failed to get root contexts: {str(e)}")
            return []
    
    def get_context_children(self, memory_id: str, user_id: int) -> List[HierarchicalMemory]:
        """Get all children of a context"""
        try:
            return HierarchicalMemory.get_children(memory_id, user_id)
        except Exception as e:
            logger.error(f"Failed to get context children: {str(e)}")
            return []
    
    def update_context(
        self,
        user_id: int,
        memory_id: str,
        context_data: Optional[Dict[str, Any]] = None,
        influence_rules: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
        priority: Optional[int] = None
    ) -> Optional[HierarchicalMemory]:
        """Update a hierarchical context"""
        try:
            context = HierarchicalMemory.query.filter_by(
                memory_id=memory_id, 
                user_id=user_id
            ).first()
            
            if context:
                if context_data is not None:
                    context.context_data = context_data
                if influence_rules is not None:
                    context.influence_rules = influence_rules
                if is_active is not None:
                    context.is_active = is_active
                if priority is not None:
                    context.priority = priority
                
                context.updated_at = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"Updated hierarchical context {memory_id}")
                return context
            
            return None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update context: {str(e)}")
            return None
    
    def delete_context(self, user_id: int, memory_id: str) -> bool:
        """Delete a hierarchical context and all its descendants"""
        try:
            context = HierarchicalMemory.query.filter_by(
                memory_id=memory_id, 
                user_id=user_id
            ).first()
            
            if context:
                # Get all descendants
                descendants = HierarchicalMemory.get_descendants(memory_id, user_id)
                
                # Delete descendants first
                for descendant in descendants:
                    db.session.delete(descendant)
                
                # Delete the context itself
                db.session.delete(context)
                db.session.commit()
                
                logger.info(f"Deleted context {memory_id} and {len(descendants)} descendants")
                return True
            
            return False
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete context: {str(e)}")
            return False
    
    def get_contextualized_memories(
        self, 
        user_id: int, 
        namespace: str, 
        query: Optional[str] = None,
        context_memory_id: Optional[str] = None,
        limit: int = 10
    ) -> Tuple[List[LongTermMemory], Dict[str, Any]]:
        """Get memories with contextual influence applied"""
        try:
            # Get base memories
            memories = self.search_memories(user_id, namespace, query, limit)
            
            # Get contextual influence if specified
            context_influence = {}
            if context_memory_id:
                context_influence = self.get_context_influence(context_memory_id, user_id)
            
            return memories, context_influence
            
        except Exception as e:
            logger.error(f"Failed to get contextualized memories: {str(e)}")
            return [], {}
    
    def create_vacation_context_example(self, user_id: int) -> HierarchicalMemory:
        """Example: Create a vacation context that influences all other decisions"""
        vacation_context = self.create_hierarchical_context(
            user_id=user_id,
            name="Vacation Mode",
            description="User is on vacation - should prioritize relaxation and minimize work",
            context_data={
                "status": "on_vacation",
                "start_date": "2024-06-01",
                "end_date": "2024-06-15",
                "location": "Hawaii",
                "work_priority": "minimal"
            },
            influence_rules={
                "override": {
                    "work_urgency": "low",
                    "response_style": "relaxed",
                    "automation_level": "high"
                },
                "modify": {
                    "email_check_frequency": {"operation": "multiply", "value": 0.25},
                    "meeting_suggestions": {"operation": "multiply", "value": 0.1},
                    "task_priority": {"operation": "multiply", "value": 0.3}
                },
                "add": {
                    "vacation_aware": True,
                    "relaxation_focus": True
                }
            },
            memory_type="context",
            priority=100  # High priority to override other contexts
        )
        
        # Create child contexts that inherit vacation influence
        email_prefs = self.create_hierarchical_context(
            user_id=user_id,
            name="Vacation Email Preferences",
            description="Email handling preferences during vacation",
            context_data={
                "check_frequency": "once_per_day",
                "auto_reply_enabled": True,
                "urgent_only": True,
                "batch_processing": True
            },
            parent_id=vacation_context.memory_id,
            influence_rules={
                "override": {
                    "email_urgency_threshold": "critical_only",
                    "response_time_expectation": "24_hours"
                }
            }
        )
        
        return vacation_context
    
    def get_combined_context_for_decision(
        self, 
        user_id: int, 
        decision_type: str
    ) -> Dict[str, Any]:
        """Get all relevant contexts for a specific decision type"""
        try:
            # Get all active contexts
            active_contexts = self.get_active_contexts(user_id)
            
            # Start with base context
            combined_context = {
                "decision_type": decision_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Apply contexts in order (root to leaf, priority order)
            for context in active_contexts:
                if context.influence_rules:
                    combined_context = context.apply_influence_rules(
                        combined_context, 
                        context.influence_rules
                    )
            
            return combined_context
            
        except Exception as e:
            logger.error(f"Failed to get combined context: {str(e)}")
            return {"decision_type": decision_type}


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