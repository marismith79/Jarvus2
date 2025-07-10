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
from .vector_memory_service import VectorMemoryService

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for managing agent memory using database-backed storage with vector search"""
    
    def __init__(self, enable_vector_search: bool = True):
        self.llm_client = JarvusAIClient()
        self.enable_vector_search = enable_vector_search
        
        # Initialize vector service if enabled
        if self.enable_vector_search:
            try:
                self.vector_service = VectorMemoryService()
                logger.info("Vector memory service initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize vector service: {str(e)}. Falling back to relational-only search.")
                self.enable_vector_search = False
                self.vector_service = None
        else:
            self.vector_service = None
    
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
        """Store a long-term memory with content in vector DB and metadata in SQL"""
        try:
            # Generate memory ID if not provided
            if not memory_id:
                memory_id = str(uuid.uuid4())
            
            # Create or update memory in SQL (metadata only)
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
            
            # Store content in vector database if vector search is enabled
            if self.enable_vector_search and self.vector_service:
                try:
                    # Prepare content text for vector storage
                    content_text = search_text or json.dumps(memory_data)
                    
                    # Store content in vector DB
                    vector_id = self.vector_service.store_memory_content(memory, content_text)
                    
                    # Store vector_id reference in SQL metadata (optional)
                    if not memory.memory_data.get('vector_id'):
                        memory.memory_data['vector_id'] = vector_id
                        db.session.commit()
                    
                except Exception as e:
                    logger.warning(f"Failed to store memory content in vector DB: {str(e)}")
            
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
        logger.info(f"store_episodic_memory called: user_id={user_id}, episode_type={episode_type}, episode_data={episode_data}")
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
        logger.info(f"store_semantic_memory called: user_id={user_id}, fact_type={fact_type}, fact_data={fact_data}")
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
        logger.info(f"store_procedural_memory called: user_id={user_id}, procedure_name={procedure_name}, procedure_data={procedure_data}")
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
        limit: int = 10,
        search_type: str = 'efficient_hybrid'  # 'efficient_hybrid', 'vector', 'sql_only'
    ) -> List[LongTermMemory]:
        """Search memories using efficient hybrid approach: SQL metadata + Vector content"""
        try:
            if not query:
                # No query provided, use SQL search only
                memories = LongTermMemory.search_memories(user_id, namespace, None, limit)
            elif self.enable_vector_search and self.vector_service and search_type in ['efficient_hybrid', 'vector']:
                # Use efficient hybrid search
                if search_type == 'efficient_hybrid':
                    # SQL filters metadata first, then vector searches content
                    vector_results = self.vector_service.efficient_hybrid_search(
                        query, user_id, namespace, limit
                    )
                else:
                    # Pure vector search (fallback)
                    vector_results = self.vector_service.efficient_hybrid_search(
                        query, user_id, namespace, limit
                    )
                
                # Convert vector results to memory objects
                memories = []
                for result in vector_results:
                    memory_id = result['memory_id']
                    memory = LongTermMemory.get_memory(user_id, namespace, memory_id)
                    if memory:
                        memories.append(memory)
                
                # Update access times
                for memory in memories:
                    memory.update_access_time()
                    
            else:
                # Fallback to SQL search only
                memories = LongTermMemory.search_memories(user_id, namespace, query, limit)
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories: {str(e)}")
            # Fallback to SQL search
            return LongTermMemory.search_memories(user_id, namespace, query, limit)
    
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
        """Create a hierarchical context with content in vector DB and metadata in SQL"""
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
            
            # Store context content in vector database if vector search is enabled
            if self.enable_vector_search and self.vector_service:
                try:
                    # Prepare content text for vector storage
                    content_text = f"{name}: {description} {json.dumps(context_data)}"
                    
                    # Store content in vector DB
                    vector_id = self.vector_service.store_context_content(context, content_text)
                    
                    # Store vector_id reference in context metadata (optional)
                    if not context.context_data.get('vector_id'):
                        context.context_data['vector_id'] = vector_id
                        db.session.commit()
                    
                except Exception as e:
                    logger.warning(f"Failed to store context content in vector DB: {str(e)}")
            
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
        """Delete a hierarchical context"""
        try:
            context = HierarchicalMemory.query.filter_by(
                memory_id=memory_id, 
                user_id=user_id
            ).first()
            
            if context:
                # Recursively delete child contexts
                children = self.get_context_children(memory_id, user_id)
                for child in children:
                    self.delete_context(user_id, child.memory_id)
                
                db.session.delete(context)
                db.session.commit()
                
                logger.info(f"Deleted hierarchical context {memory_id}")
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

    # --- Memory Editing & Improvement System ---
    
    def find_mergeable_memories(self, user_id: int, namespace: str, similarity_threshold: float = 0.85) -> List[List[LongTermMemory]]:
        """Find memories that can be merged based on similarity"""
        try:
            memories = self.search_memories(user_id, namespace, limit=100)
            mergeable_groups = []
            
            for i, memory1 in enumerate(memories):
                group = [memory1]
                for memory2 in memories[i+1:]:
                    similarity = self._calculate_memory_similarity(memory1, memory2)
                    if similarity > similarity_threshold:
                        group.append(memory2)
                
                if len(group) > 1:
                    mergeable_groups.append(group)
            
            return mergeable_groups
            
        except Exception as e:
            logger.error(f"Failed to find mergeable memories: {str(e)}")
            return []
    
    def merge_memories(self, user_id: int, memory_ids: List[str], merge_type: str = 'episodic') -> Optional[LongTermMemory]:
        """Merge multiple memories into a single, improved memory"""
        try:
            memories = []
            for memory_id in memory_ids:
                memory = self.get_memory(user_id, 'episodes', memory_id)
                if memory:
                    memories.append(memory)
            
            if len(memories) <= 1:
                return memories[0] if memories else None
            
            if merge_type == 'episodic':
                merged_data = self._merge_episodic_memories(memories)
            elif merge_type == 'procedural':
                merged_data = self._merge_procedural_memories(memories)
            else:
                merged_data = self._merge_semantic_memories(memories)
            
            # Calculate average importance score
            avg_importance = sum(m.importance_score for m in memories) / len(memories)
            
            # Store merged memory
            merged_memory = self.store_memory(
                user_id=user_id,
                namespace='merged',
                memory_data=merged_data,
                memory_type=f'merged_{merge_type}',
                importance_score=avg_importance * 1.2,  # Boost importance for merged memory
                search_text=json.dumps(merged_data)
            )
            
            # Mark original memories as merged
            for memory in memories:
                memory.memory_data['merged_into'] = merged_memory.memory_id
                memory.memory_data['merge_timestamp'] = datetime.utcnow().isoformat()
                db.session.commit()
            
            logger.info(f"Merged {len(memories)} memories into {merged_memory.memory_id}")
            return merged_memory
            
        except Exception as e:
            logger.error(f"Failed to merge memories: {str(e)}")
            return None
    
    def improve_memory(self, user_id: int, memory_id: str, improvement_type: str = 'auto') -> Optional[LongTermMemory]:
        """Improve a specific memory with enhanced content"""
        try:
            memory = self.get_memory(user_id, 'episodes', memory_id)
            if not memory:
                return None
            
            if improvement_type == 'auto':
                improved_data = self._auto_improve_memory(memory)
            elif improvement_type == 'procedural':
                improved_data = self._improve_procedural_memory(memory)
            elif improvement_type == 'semantic':
                improved_data = self._improve_semantic_memory(memory)
            else:
                improved_data = self._improve_episodic_memory(memory)
            
            # Update memory with improvements
            memory.memory_data.update(improved_data)
            memory.importance_score *= 1.1  # Slight boost for improved memory
            memory.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Improved memory {memory_id}")
            return memory
            
        except Exception as e:
            logger.error(f"Failed to improve memory: {str(e)}")
            return None
    
    def assess_memory_quality(self, user_id: int, memory_id: str) -> Dict[str, float]:
        """Assess the quality of a memory across multiple dimensions"""
        try:
            memory = self.get_memory(user_id, 'episodes', memory_id)
            if not memory:
                return {}
            
            quality_scores = {
                'completeness': self._assess_completeness(memory),
                'accuracy': self._assess_accuracy(memory),
                'usefulness': self._assess_usefulness(memory),
                'clarity': self._assess_clarity(memory),
                'consistency': self._assess_consistency(memory)
            }
            
            return quality_scores
            
        except Exception as e:
            logger.error(f"Failed to assess memory quality: {str(e)}")
            return {}
    
    def detect_memory_conflicts(self, user_id: int, namespace: str) -> List[Dict[str, Any]]:
        """Detect conflicts between memories"""
        try:
            memories = self.search_memories(user_id, namespace, limit=100)
            conflicts = []
            
            for i, memory1 in enumerate(memories):
                for memory2 in memories[i+1:]:
                    if self._has_memory_conflict(memory1, memory2):
                        conflicts.append({
                            'memory1_id': memory1.memory_id,
                            'memory2_id': memory2.memory_id,
                            'memory1_data': memory1.memory_data,
                            'memory2_data': memory2.memory_data,
                            'conflict_type': self._classify_conflict(memory1, memory2),
                            'severity': self._assess_conflict_severity(memory1, memory2)
                        })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Failed to detect memory conflicts: {str(e)}")
            return []
    
    def resolve_memory_conflicts(self, user_id: int, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve memory conflicts intelligently"""
        try:
            resolutions = []
            
            for conflict in conflicts:
                memory1 = self.get_memory(user_id, 'episodes', conflict['memory1_id'])
                memory2 = self.get_memory(user_id, 'episodes', conflict['memory2_id'])
                
                if memory1 and memory2:
                    resolution = self._resolve_single_conflict(memory1, memory2, conflict)
                    resolutions.append(resolution)
            
            return resolutions
            
        except Exception as e:
            logger.error(f"Failed to resolve memory conflicts: {str(e)}")
            return []
    
    def get_memory_evolution(self, user_id: int, memory_id: str) -> List[Dict[str, Any]]:
        """Get the evolution history of a memory"""
        try:
            # This would require a separate versioning table in a full implementation
            # For now, we'll return basic evolution data from memory metadata
            memory = self.get_memory(user_id, 'episodes', memory_id)
            if not memory:
                return []
            
            evolution = []
            if memory.updated_at and memory.updated_at != memory.created_at:
                evolution.append({
                    'timestamp': memory.updated_at.isoformat(),
                    'change_type': 'update',
                    'description': 'Memory was updated'
                })
            
            if 'merged_into' in memory.memory_data:
                evolution.append({
                    'timestamp': memory.memory_data.get('merge_timestamp'),
                    'change_type': 'merged',
                    'description': f"Merged into {memory.memory_data['merged_into']}"
                })
            
            return evolution
            
        except Exception as e:
            logger.error(f"Failed to get memory evolution: {str(e)}")
            return []
    
    # --- Private Helper Methods for Memory Editing ---
    
    def _calculate_memory_similarity(self, memory1: LongTermMemory, memory2: LongTermMemory) -> float:
        """Calculate similarity between two memories"""
        try:
            # Simple text similarity for now - could be enhanced with embeddings
            text1 = json.dumps(memory1.memory_data)
            text2 = json.dumps(memory2.memory_data)
            
            # Use difflib for similarity calculation
            import difflib
            similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
            
            return similarity
            
        except Exception as e:
            logger.error(f"Failed to calculate memory similarity: {str(e)}")
            return 0.0
    
    def _merge_episodic_memories(self, memories: List[LongTermMemory]) -> Dict[str, Any]:
        """Merge episodic memories into a comprehensive memory"""
        try:
            # Extract common patterns and unique details
            common_elements = {}
            unique_details = []
            
            for memory in memories:
                episode_data = memory.memory_data.get('data', {})
                episode_type = episode_data.get('type', 'unknown')
                
                if episode_type not in common_elements:
                    common_elements[episode_type] = []
                common_elements[episode_type].append(episode_data)
                
                unique_details.append({
                    'memory_id': memory.memory_id,
                    'timestamp': episode_data.get('timestamp'),
                    'details': episode_data
                })
            
            # Create merged memory structure
            merged_data = {
                'type': 'merged_episode',
                'original_count': len(memories),
                'original_memory_ids': [m.memory_id for m in memories],
                'merge_timestamp': datetime.utcnow().isoformat(),
                'common_patterns': common_elements,
                'unique_details': unique_details,
                'frequency': len(memories),
                'time_span': {
                    'earliest': min(m.created_at for m in memories),
                    'latest': max(m.created_at for m in memories)
                }
            }
            
            return merged_data
            
        except Exception as e:
            logger.error(f"Failed to merge episodic memories: {str(e)}")
            return {}
    
    def _merge_procedural_memories(self, memories: List[LongTermMemory]) -> Dict[str, Any]:
        """Merge procedural memories into an improved workflow"""
        try:
            all_steps = []
            success_rates = []
            
            for memory in memories:
                procedure_data = memory.memory_data.get('data', {})
                steps = procedure_data.get('steps', [])
                all_steps.extend(steps)
                
                success_rate = procedure_data.get('success_rate', 0.5)
                success_rates.append(success_rate)
            
            # Create improved workflow
            merged_data = {
                'type': 'improved_procedure',
                'original_count': len(memories),
                'original_memory_ids': [m.memory_id for m in memories],
                'merge_timestamp': datetime.utcnow().isoformat(),
                'improved_steps': self._optimize_workflow_steps(all_steps),
                'average_success_rate': sum(success_rates) / len(success_rates),
                'improvement_metrics': {
                    'step_count_reduction': len(all_steps) - len(self._optimize_workflow_steps(all_steps)),
                    'expected_success_improvement': 0.1  # Placeholder
                }
            }
            
            return merged_data
            
        except Exception as e:
            logger.error(f"Failed to merge procedural memories: {str(e)}")
            return {}
    
    def _merge_semantic_memories(self, memories: List[LongTermMemory]) -> Dict[str, Any]:
        """Merge semantic memories into enhanced knowledge"""
        try:
            all_facts = []
            
            for memory in memories:
                fact_data = memory.memory_data.get('data', {})
                all_facts.append(fact_data)
            
            merged_data = {
                'type': 'enhanced_knowledge',
                'original_count': len(memories),
                'original_memory_ids': [m.memory_id for m in memories],
                'merge_timestamp': datetime.utcnow().isoformat(),
                'enhanced_facts': all_facts,
                'confidence_level': self._calculate_combined_confidence(memories),
                'related_concepts': self._extract_related_concepts(all_facts)
            }
            
            return merged_data
            
        except Exception as e:
            logger.error(f"Failed to merge semantic memories: {str(e)}")
            return {}
    
    def _auto_improve_memory(self, memory: LongTermMemory) -> Dict[str, Any]:
        """Automatically improve a memory based on its type"""
        try:
            memory_type = memory.memory_type
            
            if memory_type == 'procedure':
                return self._improve_procedural_memory(memory)
            elif memory_type == 'fact':
                return self._improve_semantic_memory(memory)
            else:
                return self._improve_episodic_memory(memory)
                
        except Exception as e:
            logger.error(f"Failed to auto-improve memory: {str(e)}")
            return {}
    
    def _improve_procedural_memory(self, memory: LongTermMemory) -> Dict[str, Any]:
        """Improve a procedural memory with better workflow steps"""
        try:
            procedure_data = memory.memory_data.get('data', {})
            current_steps = procedure_data.get('steps', [])
            
            # Add error handling and validation steps
            improved_steps = []
            for i, step in enumerate(current_steps):
                improved_steps.append(step)
                
                # Add validation step after each action
                if step.get('action') in ['click', 'input', 'navigate']:
                    improved_steps.append({
                        'action': 'validate',
                        'description': f"Verify {step.get('action')} was successful",
                        'validation_type': 'success_check'
                    })
            
            # Add final success validation
            improved_steps.append({
                'action': 'final_validation',
                'description': 'Verify overall workflow success',
                'validation_type': 'completion_check'
            })
            
            return {
                'improved_steps': improved_steps,
                'improvement_timestamp': datetime.utcnow().isoformat(),
                'improvement_type': 'procedural_enhancement'
            }
            
        except Exception as e:
            logger.error(f"Failed to improve procedural memory: {str(e)}")
            return {}
    
    def _improve_semantic_memory(self, memory: LongTermMemory) -> Dict[str, Any]:
        """Improve a semantic memory with additional context"""
        try:
            fact_data = memory.memory_data.get('data', {})
            
            enhanced_context = {
                'confidence_level': fact_data.get('confidence', 0.8),
                'source_information': fact_data.get('source', 'user_input'),
                'temporal_context': memory.created_at.isoformat(),
                'usage_frequency': 1,  # Would be calculated from access patterns
                'related_concepts': [],
                'practical_applications': []
            }
            
            return {
                'enhanced_context': enhanced_context,
                'improvement_timestamp': datetime.utcnow().isoformat(),
                'improvement_type': 'semantic_enhancement'
            }
            
        except Exception as e:
            logger.error(f"Failed to improve semantic memory: {str(e)}")
            return {}
    
    def _improve_episodic_memory(self, memory: LongTermMemory) -> Dict[str, Any]:
        """Improve an episodic memory with better insights"""
        try:
            episode_data = memory.memory_data.get('data', {})
            
            enhanced_insights = {
                'causal_analysis': 'Why this happened',
                'lessons_learned': 'Key insights from this experience',
                'future_implications': 'How this affects future decisions',
                'performance_metrics': {
                    'success': episode_data.get('result') == 'success',
                    'duration': episode_data.get('duration'),
                    'efficiency': 'high'  # Would be calculated
                }
            }
            
            return {
                'enhanced_insights': enhanced_insights,
                'improvement_timestamp': datetime.utcnow().isoformat(),
                'improvement_type': 'episodic_enhancement'
            }
            
        except Exception as e:
            logger.error(f"Failed to improve episodic memory: {str(e)}")
            return {}
    
    def _assess_completeness(self, memory: LongTermMemory) -> float:
        """Assess how complete a memory is"""
        try:
            data = memory.memory_data
            required_fields = ['type', 'data']
            present_fields = sum(1 for field in required_fields if field in data)
            
            # Check data richness
            data_richness = len(str(data)) / 1000  # Normalize by expected size
            
            return min(1.0, (present_fields / len(required_fields) + data_richness) / 2)
            
        except Exception as e:
            logger.error(f"Failed to assess completeness: {str(e)}")
            return 0.5
    
    def _assess_accuracy(self, memory: LongTermMemory) -> float:
        """Assess the accuracy of a memory"""
        try:
            # This would require more sophisticated analysis
            # For now, use a simple heuristic based on memory type and age
            base_accuracy = 0.8
            
            if memory.memory_type == 'procedure':
                base_accuracy = 0.9  # Procedures tend to be more accurate
            elif memory.memory_type == 'fact':
                base_accuracy = 0.85  # Facts are generally reliable
            
            # Adjust for age (newer memories might be more accurate)
            age_factor = 1.0 - (datetime.utcnow() - memory.created_at).days / 365
            age_factor = max(0.5, min(1.0, age_factor))
            
            return base_accuracy * age_factor
            
        except Exception as e:
            logger.error(f"Failed to assess accuracy: {str(e)}")
            return 0.7
    
    def _assess_usefulness(self, memory: LongTermMemory) -> float:
        """Assess how useful a memory is"""
        try:
            # Use importance score and access patterns
            usefulness = memory.importance_score / 5.0  # Normalize to 0-1
            
            # Boost for frequently accessed memories
            if memory.last_accessed:
                days_since_access = (datetime.utcnow() - memory.last_accessed).days
                if days_since_access < 7:
                    usefulness *= 1.2
                elif days_since_access > 30:
                    usefulness *= 0.8
            
            return min(1.0, usefulness)
            
        except Exception as e:
            logger.error(f"Failed to assess usefulness: {str(e)}")
            return 0.6
    
    def _assess_clarity(self, memory: LongTermMemory) -> float:
        """Assess how clear and understandable a memory is"""
        try:
            data_str = json.dumps(memory.memory_data)
            
            # Simple clarity metrics
            word_count = len(data_str.split())
            readability = min(1.0, word_count / 100)  # More words = more detailed
            
            # Check for structured data
            structure_score = 0.5
            if isinstance(memory.memory_data, dict) and len(memory.memory_data) > 2:
                structure_score = 0.8
            
            return (readability + structure_score) / 2
            
        except Exception as e:
            logger.error(f"Failed to assess clarity: {str(e)}")
            return 0.6
    
    def _assess_consistency(self, memory: LongTermMemory) -> float:
        """Assess consistency with other memories"""
        try:
            # This would require comparing with other memories
            # For now, return a default score
            return 0.8
            
        except Exception as e:
            logger.error(f"Failed to assess consistency: {str(e)}")
            return 0.7
    
    def _has_memory_conflict(self, memory1: LongTermMemory, memory2: LongTermMemory) -> bool:
        """Check if two memories have conflicts"""
        try:
            # Simple conflict detection based on similar content but different outcomes
            data1 = memory1.memory_data
            data2 = memory2.memory_data
            
            # Check for same action but different results
            if (data1.get('type') == data2.get('type') and 
                data1.get('data', {}).get('action') == data2.get('data', {}).get('action') and
                data1.get('data', {}).get('result') != data2.get('data', {}).get('result')):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check memory conflict: {str(e)}")
            return False
    
    def _classify_conflict(self, memory1: LongTermMemory, memory2: LongTermMemory) -> str:
        """Classify the type of conflict between memories"""
        try:
            data1 = memory1.memory_data
            data2 = memory2.memory_data
            
            if data1.get('data', {}).get('result') != data2.get('data', {}).get('result'):
                return 'outcome_conflict'
            elif data1.get('data', {}).get('timestamp') != data2.get('data', {}).get('timestamp'):
                return 'temporal_conflict'
            else:
                return 'data_conflict'
                
        except Exception as e:
            logger.error(f"Failed to classify conflict: {str(e)}")
            return 'unknown_conflict'
    
    def _assess_conflict_severity(self, memory1: LongTermMemory, memory2: LongTermMemory) -> str:
        """Assess the severity of a memory conflict"""
        try:
            # Simple severity assessment
            if self._classify_conflict(memory1, memory2) == 'outcome_conflict':
                return 'high'
            elif self._classify_conflict(memory1, memory2) == 'temporal_conflict':
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.error(f"Failed to assess conflict severity: {str(e)}")
            return 'medium'
    
    def _resolve_single_conflict(self, memory1: LongTermMemory, memory2: LongTermMemory, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a single memory conflict"""
        try:
            # Simple conflict resolution strategy
            # Prefer the more recent memory with higher importance
            if memory1.importance_score > memory2.importance_score:
                preferred_memory = memory1
                resolved_data = memory1.memory_data
            else:
                preferred_memory = memory2
                resolved_data = memory2.memory_data
            
            resolution = {
                'conflict_id': f"{memory1.memory_id}_{memory2.memory_id}",
                'resolution_strategy': 'prefer_higher_importance',
                'preferred_memory_id': preferred_memory.memory_id,
                'resolved_data': resolved_data,
                'resolution_timestamp': datetime.utcnow().isoformat()
            }
            
            return resolution
            
        except Exception as e:
            logger.error(f"Failed to resolve single conflict: {str(e)}")
            return {}
    
    def _optimize_workflow_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize workflow steps by removing redundancy and improving sequence"""
        try:
            # Simple optimization: remove duplicate steps
            seen_actions = set()
            optimized_steps = []
            
            for step in steps:
                action_key = f"{step.get('action')}_{step.get('target', '')}"
                if action_key not in seen_actions:
                    optimized_steps.append(step)
                    seen_actions.add(action_key)
            
            return optimized_steps
            
        except Exception as e:
            logger.error(f"Failed to optimize workflow steps: {str(e)}")
            return steps
    
    def _calculate_combined_confidence(self, memories: List[LongTermMemory]) -> float:
        """Calculate combined confidence from multiple memories"""
        try:
            confidences = []
            for memory in memories:
                confidence = memory.memory_data.get('data', {}).get('confidence', 0.8)
                confidences.append(confidence)
            
            return sum(confidences) / len(confidences) if confidences else 0.8
            
        except Exception as e:
            logger.error(f"Failed to calculate combined confidence: {str(e)}")
            return 0.8
    
    def _extract_related_concepts(self, facts: List[Dict[str, Any]]) -> List[str]:
        """Extract related concepts from facts"""
        try:
            # Simple concept extraction
            concepts = set()
            for fact in facts:
                text = json.dumps(fact)
                # Extract potential concepts (simplified)
                words = text.split()
                for word in words:
                    if len(word) > 5 and word.isalpha():
                        concepts.add(word.lower())
            
            return list(concepts)[:10]  # Limit to top 10
            
        except Exception as e:
            logger.error(f"Failed to extract related concepts: {str(e)}")
            return []

    def search_hierarchical_contexts_vector(
        self, 
        query: str, 
        user_id: int, 
        n_results: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search hierarchical contexts using efficient SQL + Vector approach"""
        if not self.enable_vector_search or not self.vector_service:
            logger.warning("Vector search not enabled, returning empty results")
            return []
        
        try:
            return self.vector_service.search_contexts_efficient(
                query, user_id, n_results, similarity_threshold
            )
        except Exception as e:
            logger.error(f"Failed to search hierarchical contexts with vector: {str(e)}")
            return []
    
    def efficient_semantic_search(
        self, 
        query: str, 
        user_id: int, 
        namespace: str, 
        n_results: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Efficient semantic search using SQL metadata filtering + Vector content search"""
        if not self.enable_vector_search or not self.vector_service:
            logger.warning("Vector search not enabled, returning empty results")
            return []
        
        try:
            return self.vector_service.efficient_hybrid_search(
                query, user_id, namespace, n_results, similarity_threshold
            )
        except Exception as e:
            logger.error(f"Failed to perform efficient semantic search: {str(e)}")
            return []
    
    def get_memory_content_by_vector_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get memory content directly from vector database by vector ID"""
        if not self.enable_vector_search or not self.vector_service:
            return None
        
        try:
            return self.vector_service.get_memory_by_vector_id(vector_id)
        except Exception as e:
            logger.error(f"Failed to get memory content by vector ID: {str(e)}")
            return None
    
    def update_memory_content(
        self, 
        user_id: int, 
        namespace: str, 
        memory_id: str, 
        new_content: str
    ) -> bool:
        """Update memory content in vector database"""
        if not self.enable_vector_search or not self.vector_service:
            return False
        
        try:
            # Get memory from SQL
            memory = LongTermMemory.get_memory(user_id, namespace, memory_id)
            if not memory:
                return False
            
            # Update content in vector DB
            success = self.vector_service.update_memory_content(memory, new_content)
            
            if success:
                # Update search_text in SQL if needed
                if memory.search_text != new_content:
                    memory.search_text = new_content
                    memory.updated_at = datetime.utcnow()
                    db.session.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update memory content: {str(e)}")
            return False
    
    def delete_memory_with_vector(
        self, 
        user_id: int, 
        namespace: str, 
        memory_id: str
    ) -> bool:
        """Delete memory from both SQL and vector databases"""
        try:
            # Delete from SQL database
            success = self.delete_memory(user_id, namespace, memory_id)
            
            # Delete from vector database if enabled
            if success and self.enable_vector_search and self.vector_service:
                try:
                    self.vector_service.delete_memory_content(user_id, memory_id)
                except Exception as e:
                    logger.warning(f"Failed to delete memory content from vector DB: {str(e)}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete memory with vector: {str(e)}")
            return False
    
    def delete_hierarchical_context_with_vector(
        self, 
        user_id: int, 
        memory_id: str
    ) -> bool:
        """Delete hierarchical context from both SQL and vector databases"""
        try:
            # Delete from SQL database
            success = self.delete_context(user_id, memory_id)
            
            # Delete from vector database if enabled
            if success and self.enable_vector_search and self.vector_service:
                try:
                    self.vector_service.delete_context_content(user_id, memory_id)
                except Exception as e:
                    logger.warning(f"Failed to delete context content from vector DB: {str(e)}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete hierarchical context with vector: {str(e)}")
            return False

    def get_importance_score_from_llm(self, memory_type: str, memory_content: str, conversation_text: str = None, user_goal: str = None) -> (float, str):
        """
        Use the LLM to rate the importance of a memory, given its type, content, and context.
        Returns a tuple: (importance_score, justification)
        """
        prompt = f"""
You are an AI assistant helping to organize a user's memories. Here is the context:

- Memory type: {memory_type}
- Memory content: {memory_content}
"""
        if conversation_text:
            prompt += f"\n- Conversation or event: {conversation_text}"
        if user_goal:
            prompt += f"\n- User's current goal: {user_goal}"
        prompt += """

On a scale from 1 (not important) to 5 (very important), how important is this memory for the user's future actions or understanding? Respond with a single number and a brief reason, e.g. '4: This is a key user preference.'
"""

        response = self.llm_client.format_response(self.llm_client.create_chat_completion([
            self.llm_client.format_message("system", "You are an expert at evaluating the importance of user memories for an AI assistant."),
            self.llm_client.format_message("user", prompt)
        ], max_tokens=64, temperature=0.2))
        content = response.get('content', '')
        import re
        match = re.match(r"(\d(?:\.\d+)?)[^\d]*(.*)", content.strip())
        if match:
            score = float(match.group(1))
            justification = match.group(2).strip()
        else:
            score = 3.0
            justification = content.strip() or "No justification provided."
        # Normalize to 1.0-5.0, then to 0.2-1.0 for storage if desired
        normalized_score = max(1.0, min(5.0, score))
        return normalized_score, justification

    def extract_and_store_memories(
        self,
        user_id: int,
        conversation_messages: list,
        agent_id: int = None,
        tool_call: dict = None,
        feedback: str = None,
        user_goal: str = None
    ) -> list:
        """
        Compress/summarize and store episodic, semantic, and procedural memories from a conversation.
        - Store the conversation as an episodic memory (summarized).
        - Extract and store semantic facts about the user.
        - If a tool was used, store the workflow and feedback as procedural memory.
        - After storing, improve and merge memories as appropriate.
        Returns a list of stored/updated memory objects.
        """
        logger.info(f"extract_and_store_memories called: user_id={user_id}, agent_id={agent_id}, tool_call={tool_call}, feedback={feedback}")
        stored_memories = []
        # 1. Summarize conversation for episodic memory
        conversation_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in conversation_messages if msg.get('content')
        ])
        summary_prompt = (
            "Summarize the following conversation as an episode, focusing on key events, actions, and outcomes. "
            "Be concise but capture important details.\n\nConversation:\n" + conversation_text
        )
        summary = self.llm_client.format_response(self.llm_client.create_chat_completion([
            self.llm_client.format_message("system", "You are a helpful assistant that summarizes conversations for memory storage."),
            self.llm_client.format_message("user", summary_prompt)
        ]))
        episode_summary = summary.get('content', conversation_text)
        # Get importance for episodic memory
        episodic_score, episodic_justification = self.get_importance_score_from_llm(
            memory_type="episodic",
            memory_content=episode_summary,
            conversation_text=conversation_text,
            user_goal=user_goal
        )
        episodic_memory = self.store_episodic_memory(
            user_id=user_id,
            episode_type="conversation",
            episode_data={
                "summary": episode_summary,
                "raw": conversation_text,
                "agent_id": agent_id,
                "importance_justification": episodic_justification
            },
            importance_score=episodic_score
        )
        stored_memories.append(episodic_memory)

        # 2. Extract semantic facts
        semantic_prompt = (
            "From the following conversation, extract any facts, preferences, or information about the user that should be stored as semantic memory. "
            "Return a JSON list of facts, each as an object with 'type' and 'data'. If none, return an empty list.\n\nConversation:\n" + conversation_text
        )
        semantic_response = self.llm_client.format_response(self.llm_client.create_chat_completion([
            self.llm_client.format_message("system", "You extract user facts for semantic memory in JSON format."),
            self.llm_client.format_message("user", semantic_prompt)
        ]))
        import json as _json
        facts = []
        try:
            facts = _json.loads(semantic_response.get('assistant', {}).get('content', '[]'))
        except Exception:
            pass
        for fact in facts:
            fact_type = fact.get('type', 'fact')
            fact_data = fact.get('data', fact)
            # Get importance for semantic memory
            semantic_score, semantic_justification = self.get_importance_score_from_llm(
                memory_type=fact_type,
                memory_content=str(fact_data),
                conversation_text=conversation_text,
                user_goal=user_goal
            )
            semantic_memory = self.store_semantic_memory(
                user_id=user_id,
                fact_type=fact_type,
                fact_data={**fact_data, "importance_justification": semantic_justification},
                importance_score=semantic_score
            )
            stored_memories.append(semantic_memory)

        # 3. Store procedural memory if tool was used
        if tool_call:
            procedure_name = tool_call.get('name', 'tool_usage')
            procedure_data = {
                'tool': tool_call,
                'conversation': conversation_text,
                'feedback': feedback
            }
            # Get importance for procedural memory
            procedural_score, procedural_justification = self.get_importance_score_from_llm(
                memory_type="procedure",
                memory_content=str(procedure_data),
                conversation_text=conversation_text,
                user_goal=user_goal
            )
            procedural_memory = self.store_procedural_memory(
                user_id=user_id,
                procedure_name=procedure_name,
                procedure_data={**procedure_data, "importance_justification": procedural_justification},
                importance_score=procedural_score
            )
            stored_memories.append(procedural_memory)

        # 4. Memory editing/improvement: improve and merge similar memories
        # Improve procedural memories
        for mem in stored_memories:
            if getattr(mem, 'memory_type', None) == 'procedure':
                self.improve_memory(user_id, mem.memory_id, improvement_type='procedural')
        # Merge similar episodic, semantic, and procedural memories
        for ns, mtype in [('episodes', 'episodic'), ('semantic', 'semantic'), ('procedures', 'procedural')]:
            mergeable = self.find_mergeable_memories(user_id, ns)
            for group in mergeable:
                if len(group) > 1:
                    self.merge_memories(user_id, [m.memory_id for m in group], merge_type=mtype)

        return stored_memories

    def get_context_for_conversation(
        self,
        user_id: int,
        thread_id: str = None,
        current_message: str = None,
        max_memories: int = 5,
        max_tokens: int = 1500,
        as_sections: bool = True
    ):
        """
        Retrieve and summarize the most relevant episodic, semantic, and procedural memories for a user and thread.
        Returns a dict of context sections for LLM input, or a string if as_sections=False (legacy).
        """
        logger.info(f"get_context_for_conversation called: user_id={user_id}, thread_id={thread_id}, current_message={current_message}")
        # 1. Retrieve relevant memories (hybrid/vector search if available)
        # Episodic (recent conversations)
        episodic_memories = self.search_memories(
            user_id=user_id,
            namespace='episodes',
            limit=max_memories,
            search_type='efficient_hybrid'
        )
        # Semantic (facts/preferences)
        semantic_memories = self.search_memories(
            user_id=user_id,
            namespace='semantic',
            limit=max_memories,
            search_type='efficient_hybrid'
        )
        # Procedural (workflows/tool use)
        procedural_memories = self.search_memories(
            user_id=user_id,
            namespace='procedures',
            limit=max_memories,
            search_type='efficient_hybrid'
        )
        # 2. Summarize and format context sections as lists of strings
        episodic_section = []
        if episodic_memories:
            for m in episodic_memories:
                date = m.created_at.strftime('%b %d') if hasattr(m, 'created_at') else ''
                summary = m.memory_data.get('summary')
                if summary and isinstance(summary, str):
                    episodic_section.append(f"\u2022 {date}: {summary}")
        semantic_section = []
        if semantic_memories:
            for m in semantic_memories:
                src = m.memory_data.get('source', '')
                data = m.memory_data.get('data', m.memory_data)
                if isinstance(data, str):
                    if src:
                        semantic_section.append(f"[From {src}] {data}")
                    else:
                        semantic_section.append(data)
                elif isinstance(data, dict):
                    for key in ['fact', 'summary', 'description', 'value']:
                        if key in data and isinstance(data[key], str):
                            if src:
                                semantic_section.append(f"[From {src}] {data[key]}")
                            else:
                                semantic_section.append(data[key])
                            break
        procedural_section = []
        if procedural_memories:
            for m in procedural_memories:
                data = m.memory_data.get('data', m.memory_data)
                if isinstance(data, dict) and 'code' in data and isinstance(data['code'], str):
                    procedural_section.append(f"```python\n{data['code']}\n```")
                elif isinstance(data, dict):
                    for key in ['summary', 'description', 'name']:
                        if key in data and isinstance(data[key], str):
                            procedural_section.append(data[key])
                            break
                elif isinstance(data, str):
                    procedural_section.append(data)
        if as_sections:
            return {
                'episodic': episodic_section,
                'semantic': semantic_section,
                'procedural': procedural_section
            }
        # Legacy: return a single string
        context_sections = []
        if episodic_section:
            context_sections.append("[Recent Episodes]\n" + "\n".join(episodic_section))
        if semantic_section:
            context_sections.append("[User Facts & Preferences]\n" + "\n".join(semantic_section))
        if procedural_section:
            context_sections.append("[Procedures & Tool Use]\n" + "\n".join(procedural_section))
        role_section = (
            "[Role]\nYou are a helpful AI assistant for this user. Use the following context to answer as accurately and personally as possible."
        )
        context = "\n\n".join([role_section] + context_sections)
        max_chars = max_tokens * 4
        if len(context) > max_chars:
            context = context[:max_chars] + "\n..."
        return context


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