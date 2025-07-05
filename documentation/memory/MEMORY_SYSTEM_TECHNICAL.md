# Jarvus Agent Memory System — Technical Implementation

## Overview

This document provides technical implementation details for the Jarvus Agent Memory System, including storage/retrieval flows, API endpoints, database schemas, and the comprehensive memory editing & improvement system.

## Database Schema

### Core Memory Tables

#### LongTermMemory
```sql
CREATE TABLE long_term_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    namespace VARCHAR(50) NOT NULL,
    memory_id VARCHAR(36) UNIQUE NOT NULL,
    memory_data JSON NOT NULL,
    memory_type VARCHAR(20) NOT NULL DEFAULT 'fact',
    importance_score FLOAT DEFAULT 1.0,
    search_text TEXT,
    embedding_vector BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### ShortTermMemory (Checkpointing)
```sql
CREATE TABLE short_term_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id VARCHAR(36) NOT NULL,
    user_id INTEGER NOT NULL,
    agent_id INTEGER NOT NULL,
    checkpoint_id VARCHAR(36) UNIQUE NOT NULL,
    parent_checkpoint_id VARCHAR(36),
    state_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);
```

#### MemoryEmbedding (Vector Search)
```sql
CREATE TABLE memory_embedding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id VARCHAR(36) NOT NULL,
    user_id INTEGER NOT NULL,
    embedding_vector BLOB NOT NULL,
    embedding_model VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (memory_id) REFERENCES long_term_memory(memory_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### HierarchicalMemory (Context Management)
```sql
CREATE TABLE hierarchical_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    memory_id VARCHAR(36) UNIQUE NOT NULL,
    parent_id VARCHAR(36),
    level INTEGER DEFAULT 0,
    path VARCHAR(255),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    context_data JSON NOT NULL,
    influence_rules JSON NOT NULL,
    memory_type VARCHAR(20) DEFAULT 'context',
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (parent_id) REFERENCES hierarchical_memory(memory_id)
);
```

## API Endpoints

### 1. Storage Endpoints

#### POST `/memory/chrome-action`
- **Purpose:** Store a Chrome action as episodic memory
- **Request JSON:**
  ```json
  {
    "type": "chrome_action",
    "action": "click",
    "target": "button#submit",
    "url": "https://example.com",
    "result": "success",
    "timestamp": "2024-06-01T12:00:00Z",
    "details": {"note": "User submitted form"}
  }
  ```
- **Behavior:**
  - Always stores as `memory_type='episode'`.
  - `search_text` is JSON-serialized episode data.
  - `importance_score` defaults to 2.0 for actions.

#### POST `/memory/feedback`
- **Purpose:** Store user feedback as episodic memory
- **Request JSON:**
  ```json
  {
    "user_response": "accepted",
    "suggestion_reference": "sugg_001",
    "notes": "This suggestion worked well!",
    "timestamp": "2024-06-01T12:01:00Z"
  }
  ```
- **Behavior:**
  - Always stores as `memory_type='episode'`.
  - `importance_score` defaults to 3.0 for feedback.

#### POST `/memory/workflow-execution`
- **Purpose:** Store workflow execution as episodic/procedural memory
- **Request JSON:**
  ```json
  {
    "workflow_id": "wf_001",
    "steps": [
      {"action": "open_url", "url": "https://zoom.us"},
      {"action": "click", "target": "Start Meeting"}
    ],
    "result": "success",
    "timestamp": "2024-06-01T12:02:00Z",
    "details": {"note": "Started a Zoom meeting"},
    "store_as_procedure": true,
    "description": "How to start a Zoom meeting"
  }
  ```
- **Behavior:**
  - Always stores as `memory_type='episode'`.
  - If `store_as_procedure` is true, also stores as `memory_type='procedure'`.

#### POST `/memory/store`
- **Purpose:** Store semantic fact/preference
- **Request JSON:**
  ```json
  {
    "text": "User prefers dark mode",
    "type": "preference",
    "importance": 1.5
  }
  ```
- **Behavior:**
  - Stores as `memory_type` from `type` field (e.g., 'fact', 'preference').
  - `search_text` is the text field.

### 2. Retrieval Endpoints

#### GET `/memory/episodes?query=...&limit=5`
- **Returns:** `{ "episodes": [ ... ] }` (only `memory_type='episode'`)

#### GET `/memory/facts?query=...&limit=5`
- **Returns:** `{ "facts": [ ... ] }` (only `memory_type in ('fact', 'preference')`)

#### GET `/memory/procedures?query=...&limit=5`
- **Returns:** `{ "procedures": [ ... ] }` (only `memory_type in ('procedure', 'workflow')`)

- **All retrieval endpoints** support substring search on `search_text` and limit results.

### 3. Memory Editing & Improvement Endpoints

#### GET `/memory/find-mergeable?namespace=episodes&similarity=0.85`
- **Purpose:** Find memories that can be merged based on similarity
- **Returns:** `{ "mergeable_groups": [ ... ], "total_groups": N }`

#### POST `/memory/merge`
- **Purpose:** Merge multiple memories into a single, improved memory
- **Request JSON:**
  ```json
  {
    "memory_ids": ["mem_001", "mem_002", "mem_003"],
    "merge_type": "episodic"
  }
  ```
- **Returns:** `{ "merged_memory": {...}, "message": "..." }`

#### POST `/memory/improve/{memory_id}`
- **Purpose:** Improve a specific memory with enhanced content
- **Request JSON:**
  ```json
  {
    "improvement_type": "procedural"
  }
  ```
- **Returns:** `{ "improved_memory": {...}, "message": "..." }`

#### GET `/memory/assess-quality/{memory_id}`
- **Purpose:** Assess the quality of a memory across multiple dimensions
- **Returns:** `{ "quality_scores": {...}, "overall_score": 0.8, "suggested_improvements": [...] }`

#### GET `/memory/quality-report?namespace=episodes&limit=50`
- **Purpose:** Get a comprehensive quality report for all memories
- **Returns:** `{ "quality_report": {...} }`

#### GET `/memory/detect-conflicts?namespace=episodes`
- **Purpose:** Detect conflicts between memories
- **Returns:** `{ "conflicts": [...], "total_conflicts": N }`

#### POST `/memory/resolve-conflicts`
- **Purpose:** Resolve detected memory conflicts
- **Request JSON:**
  ```json
  {
    "conflicts": [...]
  }
  ```
- **Returns:** `{ "resolutions": [...], "resolved_count": N }`

#### GET `/memory/evolution/{memory_id}`
- **Purpose:** Get the evolution history of a memory
- **Returns:** `{ "evolution": [...], "total_changes": N }`

#### POST `/memory/bulk-improve`
- **Purpose:** Improve multiple memories in batch
- **Request JSON:**
  ```json
  {
    "memory_ids": ["mem_001", "mem_002", "mem_003"],
    "improvement_type": "auto"
  }
  ```
- **Returns:** `{ "improved_count": N, "failed_count": N, "results": [...] }`

#### POST `/memory/auto-consolidate?namespace=episodes&similarity=0.8`
- **Purpose:** Automatically consolidate similar memories
- **Returns:** `{ "consolidated_count": N, "results": [...] }`

### 4. Hierarchical Memory Endpoints ✅ IMPLEMENTED

#### POST `/api/memory/hierarchical/context`
- **Purpose:** Create a hierarchical context that can influence other memories
- **Request JSON:**
  ```json
  {
    "name": "Vacation Mode",
    "description": "User is on vacation - should prioritize relaxation",
    "context_data": {
      "status": "on_vacation",
      "start_date": "2024-06-01",
      "end_date": "2024-06-15",
      "location": "Hawaii"
    },
    "parent_id": null,
    "influence_rules": {
      "override": {
        "work_urgency": "low",
        "response_style": "relaxed"
      },
      "modify": {
        "email_check_frequency": {"operation": "multiply", "value": 0.25}
      },
      "add": {
        "vacation_aware": true
      }
    },
    "memory_type": "context",
    "priority": 100
  }
  ```
- **Returns:** `{ "context": {...}, "message": "..." }`

#### GET `/api/memory/hierarchical/contexts`
- **Purpose:** Get all active contexts for a user
- **Returns:** `{ "contexts": [...], "total_contexts": N }`

#### GET `/api/memory/hierarchical/context/<memory_id>`
- **Purpose:** Get specific context influence and data
- **Returns:** `{ "context": {...}, "influence": {...} }`

#### PUT `/api/memory/hierarchical/context/<memory_id>`
- **Purpose:** Update a hierarchical context
- **Request JSON:**
  ```json
  {
    "context_data": {...},
    "influence_rules": {...},
    "is_active": true,
    "priority": 50
  }
  ```
- **Returns:** `{ "context": {...}, "message": "..." }`

#### DELETE `/api/memory/hierarchical/context/<memory_id>`
- **Purpose:** Delete a hierarchical context and all its descendants
- **Returns:** `{ "success": true, "message": "..." }`

#### GET `/api/memory/hierarchical/root-contexts`
- **Purpose:** Get all root-level contexts for a user
- **Returns:** `{ "contexts": [...], "total_roots": N }`

#### GET `/api/memory/hierarchical/context/<memory_id>/children`
- **Purpose:** Get all children of a context
- **Returns:** `{ "children": [...], "total_children": N }`

#### POST `/api/memory/hierarchical/decision-context`
- **Purpose:** Get combined decision context from all active contexts
- **Request JSON:**
  ```json
  {
    "decision_type": "email_handling"
  }
  ```
- **Returns:** `{ "context": {...}, "applied_contexts": [...] }`

#### GET `/api/memory/hierarchical/contextualized/<namespace>`
- **Purpose:** Get memories with contextual influence applied
- **Query Parameters:**
  - `query`: Optional search query
  - `context_id`: Optional context memory ID to apply influence
  - `limit`: Number of memories to return (default: 10)
- **Returns:** `{ "memories": [...], "context_influence": {...} }`

## Storage/Retrieval Logic

### 1. Storage
- **All storage endpoints** call `memory_service.store_memory()` with appropriate fields.
- **If embedding is enabled:**
  - The `search_text` is embedded (e.g., using OpenAI or local model).
  - The embedding is stored in `embedding_vector` and/or `MemoryEmbedding`.
- **Importance score** is set based on event type or user input.
- **Timestamps** are set to current UTC if not provided.

### 2. Retrieval
- **All retrieval endpoints** call `memory_service.search_memories()`.
- **If query is provided:**
  - Substring search on `search_text` (default).
  - If embeddings are enabled, semantic similarity search is performed (cosine similarity on vectors).
- **Results** are filtered by `memory_type` and sorted by `importance_score` and `last_accessed`.

### 3. Memory Editing
- **Similarity Calculation**: Uses difflib.SequenceMatcher for text similarity
- **Quality Assessment**: Multi-dimensional scoring across completeness, accuracy, usefulness, clarity, consistency
- **Conflict Detection**: Identifies contradictory memories based on content analysis
- **Improvement Process**: Type-specific enhancement (procedural, semantic, episodic)

## Memory Lifecycle

### 1. Creation
- Created via API endpoints or internal service calls.
- Each memory is assigned a UUID (`memory_id`).
- Embeddings are generated if semantic search is enabled.

### 2. Access
- Each retrieval updates `last_accessed`.
- Access patterns can be used for memory pruning or summarization.

### 3. Update
- Memories can be updated by re-calling `store_memory` with the same `memory_id`.
- For facts/preferences, this allows user edits.
- Memory editing operations create enhanced versions.

### 4. Deletion
- Memories can be deleted via API or admin tools.
- Deletion cascades to embeddings.

### 5. Merging & Consolidation
- Similar memories are identified using similarity thresholds.
- Merged memories preserve original IDs and merge history.
- Original memories are marked as merged but not deleted.

### 6. Quality Assessment & Improvement
- Memories are continuously assessed for quality.
- Low-quality memories can be automatically improved.
- Quality metrics influence retrieval prioritization.

## Embedding and Semantic Search

### 1. Embedding Generation
- **When storing:**
  - If `search_text` is present and embedding is enabled, generate embedding vector.
  - Store in `embedding_vector` (LongTermMemory) and/or `MemoryEmbedding`.
- **Supported models:**
  - OpenAI (e.g., `text-embedding-3-small`)
  - Local models (e.g., SentenceTransformers)

### 2. Semantic Search
- **On retrieval:**
  - If query is provided and embedding is enabled, embed the query.
  - Compute cosine similarity with stored vectors.
  - Return top-N most similar memories.
- **Fallback:**
  - If no embedding, use substring search on `search_text`.

## Memory Editing Implementation

### 1. Memory Merging
```python
def merge_memories(self, user_id: int, memory_ids: List[str], merge_type: str = 'episodic'):
    """Merge multiple memories into a single, improved memory"""
    memories = [self.get_memory(user_id, 'episodes', mid) for mid in memory_ids]
    
    if merge_type == 'episodic':
        merged_data = self._merge_episodic_memories(memories)
    elif merge_type == 'procedural':
        merged_data = self._merge_procedural_memories(memories)
    else:
        merged_data = self._merge_semantic_memories(memories)
    
    # Store merged memory with higher importance
    merged_memory = self.store_memory(
        user_id=user_id,
        namespace='merged',
        memory_data=merged_data,
        memory_type=f'merged_{merge_type}',
        importance_score=avg_importance * 1.2
    )
    
    # Mark originals as merged
    for memory in memories:
        memory.memory_data['merged_into'] = merged_memory.memory_id
        memory.memory_data['merge_timestamp'] = datetime.utcnow().isoformat()
    
    return merged_memory
```

### 2. Memory Improvement
```python
def improve_memory(self, user_id: int, memory_id: str, improvement_type: str = 'auto'):
    """Improve a specific memory with enhanced content"""
    memory = self.get_memory(user_id, 'episodes', memory_id)
    
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
    memory.importance_score *= 1.1
    memory.updated_at = datetime.utcnow()
    
    return memory
```

### 3. Quality Assessment
```python
def assess_memory_quality(self, user_id: int, memory_id: str) -> Dict[str, float]:
    """Assess the quality of a memory across multiple dimensions"""
    memory = self.get_memory(user_id, 'episodes', memory_id)
    
    quality_scores = {
        'completeness': self._assess_completeness(memory),
        'accuracy': self._assess_accuracy(memory),
        'usefulness': self._assess_usefulness(memory),
        'clarity': self._assess_clarity(memory),
        'consistency': self._assess_consistency(memory)
    }
    
    return quality_scores
```

### 4. Conflict Detection
```python
def detect_memory_conflicts(self, user_id: int, namespace: str) -> List[Dict[str, Any]]:
    """Detect conflicts between memories"""
    memories = self.search_memories(user_id, namespace, limit=100)
    conflicts = []
    
    for i, memory1 in enumerate(memories):
        for memory2 in memories[i+1:]:
            if self._has_memory_conflict(memory1, memory2):
                conflicts.append({
                    'memory1_id': memory1.memory_id,
                    'memory2_id': memory2.memory_id,
                    'conflict_type': self._classify_conflict(memory1, memory2),
                    'severity': self._assess_conflict_severity(memory1, memory2)
                })
    
    return conflicts
```

## Hierarchical Memory Implementation ✅ IMPLEMENTED

### 1. Hierarchical Context Creation
```python
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
    return context
```

### 2. Influence Rule Application
```python
def apply_influence_rules(self, context: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    """Apply influence rules to modify context"""
    modified_context = context.copy()
    
    for rule_type, rule_data in rules.items():
        if rule_type == 'override':
            # Direct override of values
            for key, value in rule_data.items():
                modified_context[key] = value
        elif rule_type == 'modify':
            # Modify existing values
            for key, modification in rule_data.items():
                if key in modified_context:
                    if isinstance(modification, dict) and 'operation' in modification:
                        op = modification['operation']
                        value = modification.get('value')
                        
                        if op == 'multiply':
                            modified_context[key] *= value
                        elif op == 'add':
                            modified_context[key] += value
                        elif op == 'set':
                            modified_context[key] = value
                    else:
                        modified_context[key] = modification
        elif rule_type == 'add':
            # Add new values if they don't exist
            for key, value in rule_data.items():
                if key not in modified_context:
                    modified_context[key] = value
    
    return modified_context
```

### 3. Context Inheritance
```python
def get_influence_context(self) -> Dict[str, Any]:
    """Get the combined influence context from this memory and its ancestors"""
    context = self.context_data.copy()
    ancestors = self.get_ancestors(self.memory_id, self.user_id)
    
    # Apply ancestor influences (higher level contexts override lower level ones)
    for ancestor in reversed(ancestors):  # Start from root
        if ancestor.influence_rules:
            context = self.apply_influence_rules(context, ancestor.influence_rules)
    
    return context
```

### 4. Decision Context Aggregation
```python
def get_combined_context_for_decision(
    self, 
    user_id: int, 
    decision_type: str
) -> Dict[str, Any]:
    """Get all relevant contexts for a specific decision type"""
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
```

### 5. Hierarchical Memory Service Methods
```python
# Context creation and management
memory_service.create_hierarchical_context(user_id, name, description, context_data, parent_id, influence_rules)
memory_service.get_active_contexts(user_id)
memory_service.get_root_contexts(user_id)
memory_service.get_context_children(memory_id, user_id)
memory_service.update_context(user_id, memory_id, context_data, influence_rules)
memory_service.delete_context(user_id, memory_id)

# Context influence and decision making
memory_service.get_context_influence(memory_id, user_id)
memory_service.get_combined_context_for_decision(user_id, decision_type)
memory_service.get_contextualized_memories(user_id, namespace, context_memory_id)
```

## Prompt Engineering Implementation

### 1. Retrieval for Prompt Construction
- **Before generating a response:**
  - Retrieve:
    - Recent episodes (e.g., last 3-5)
    - Relevant facts/preferences (semantic)
    - Available procedures/workflows
    - Quality-assessed memories (prefer high-quality)
  - Filter and summarize as needed (e.g., only include most recent or most important).

### 2. Prompt Template Example
```python
prompt_parts = []
if facts:
    prompt_parts.append("User Preferences and Facts:")
    for fact in facts:
        prompt_parts.append(f"- {fact['data'].get('text', '')}")
if episodes:
    prompt_parts.append("\nRecent User Actions and Feedback:")
    for ep in episodes:
        summary = ep['data']
        if summary.get('type') == 'chrome_action':
            prompt_parts.append(f"- Chrome: {summary.get('action')} {summary.get('target')} on {summary.get('url')} ({summary.get('result')})")
        elif summary.get('type') == 'feedback':
            prompt_parts.append(f"- Feedback: {summary.get('user_response')} ({summary.get('notes', '')})")
        elif summary.get('type') == 'workflow_execution':
            prompt_parts.append(f"- Workflow: {summary.get('workflow_id')} result: {summary.get('result')}")
if procedures:
    prompt_parts.append("\nAvailable Workflows/Procedures:")
    for proc in procedures:
        desc = proc['data'].get('description', '')
        steps = proc['data'].get('steps', [])
        quality = proc.get('quality_score', 0.5)
        prompt_parts.append(f"- {desc} (steps: {len(steps)}, quality: {quality})")
if quality_insights:
    prompt_parts.append("\nMemory Quality Insights:")
    for insight in quality_insights:
        prompt_parts.append(f"- {insight}")
prompt_parts.append(f"\nUser says: {user_message}")
prompt_parts.append("How should the agent respond or assist?")
prompt = "\n".join(prompt_parts)
```

### 3. LLM Call
- The constructed prompt is sent to the LLM (e.g., via OpenAI, Azure, or local model).
- The LLM uses the context to generate a response, suggest workflows, or ask clarifying questions.

## Security and Privacy Considerations
- **User data isolation:** All memories are namespaced and user_id-scoped.
- **Sensitive data:** Avoid storing PII in plain text; consider encryption for sensitive fields.
- **Access control:** Only authenticated users can access their own memories.
- **Audit logging:** All memory creation, update, and deletion events should be logged for traceability.
- **Memory editing:** All editing operations are logged with user attribution and timestamps.

## Extensibility and Future Work
- **New memory types:** Add new `memory_type` values and schemas as needed.
- **Automated summarization:** Periodically compress old episodes into semantic/procedural memories.
- **User-facing memory management:** Allow users to view, edit, and delete their own memories.
- **Cross-agent sharing:** Enable sharing of anonymized procedures/facts for collective learning.
- **Advanced semantic search:** Integrate with vector databases for large-scale memory retrieval.
- **LLM-powered merging:** Use AI to create more intelligent merged memories.
- **Memory synthesis:** Create new memories by combining existing ones.
- **Predictive improvement:** Anticipate and prevent quality issues.

## Testing

### Memory System Tests
- `tests/test_memory_system.py` - Basic memory operations
- `tests/test_memory_editing.py` - Comprehensive memory editing capabilities
- `tests/test_hierarchical_memory.py` - Hierarchical memory functionality

### Test Coverage
- Memory creation and storage
- Memory retrieval and search
- Memory merging and consolidation
- Memory improvement and enhancement
- Quality assessment and scoring
- Conflict detection and resolution
- Evolution tracking
- Bulk operations
- API endpoint functionality
- Error handling and edge cases 