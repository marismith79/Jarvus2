# Jarvus Agent Memory System

## Overview

The Jarvus Agent Memory System provides comprehensive memory management capabilities for storing, retrieving, editing, and improving user interactions and knowledge. The system implements a **hybrid SQL + Vector database architecture** for optimal performance, combining the strengths of relational databases for metadata management with vector databases for semantic search and content retrieval.

## Architecture Overview

### Hybrid Database Design
The memory system uses a **two-stage retrieval pattern** that optimizes both performance and accuracy:

1. **SQL Database (Primary)**: Handles metadata, relationships, access control, and transactional operations
2. **Vector Database (Secondary)**: Specializes in semantic similarity, content retrieval, and fuzzy matching

### Efficient Two-Stage Retrieval Pattern
```
1. SQL Query → Get relevant metadata/categories (fast filtering)
2. Vector Search → Only on filtered content (semantic similarity)
3. Hybrid Ranking → Combine both results (optimal relevance)
```

This approach avoids expensive vector searches on irrelevant data while maintaining semantic search capabilities.

## Memory Types

### 1. Episodic Memory
- **What:** Stores specific user-agent interactions (e.g., user actions in Chrome, feedback, workflow executions, video summaries).
- **How:** Each "episode" is a structured record of an event, action, or feedback, with context and outcome.
- **Use:** For few-shot prompting, "what happened last time," and learning from user behavior.

### 2. Semantic Memory
- **What:** Stores facts, preferences, and general knowledge extracted from user interactions (e.g., "User prefers dark mode," "Bob's email is bob@example.com").
- **How:** Compresses and generalizes observations, stores as key-value or embedding-indexed facts.
- **Use:** For retrieval-augmented generation, answering questions, and adapting to user preferences.

### 3. Procedural Memory
- **What:** Stores "how-to" knowledge, workflows, and agent's own learned strategies (e.g., "How to automate a Zoom meeting," "How to summarize a video").
- **How:** Stores step-by-step instructions, scripts, or dynamic prompts that evolve with feedback.
- **Use:** For tool use, workflow automation, and agent self-improvement.

### 4. Hierarchical Memory
- **What:** Stores contextual states, influence rules, and decision-making contexts.
- **How:** Organizes memories in hierarchical structures with influence propagation.
- **Use:** For contextual decision making, behavior adaptation, and state management.

| Type        | Content                    | Use Cases                    | Storage Format |
|-------------|----------------------------|------------------------------|----------------|
| Episodic    | User actions, events, feedback | Context, patterns, learning | memory_type='episode' |
| Semantic    | Facts, preferences, extracted info| Personalization, Q&A, context    | memory_type='fact'/'preference'|
| Procedural  | Workflows, scripts, prompts       | Automation, suggestions, self-improve | memory_type='procedure'/'workflow'|
| Hierarchical| Contextual states, influence rules| Decision making, behavior adaptation | memory_type='context' |

- **ShortTermMemory** is used for thread-level (conversation/session) context.
- **LongTermMemory** with vector storage supports semantic search for all memory types.
- **HierarchicalMemory** provides contextual influence and state management.

---

## Storage Flows

### A. Storing Observations and Feedback
- **Chrome Action:**
  - Store as an episode with details (action, target, url, result, timestamp).
  - Content stored in both SQL (metadata) and Vector DB (semantic content).
- **Feedback:**
  - Store as an episode (user response, notes, suggestion reference).
  - Vector storage enables semantic similarity search for related feedback.
- **Workflow Execution:**
  - Store as an episode (steps, result, details).
  - Optionally, store as a procedure if it's a new workflow.
- **Semantic Fact/Preference:**
  - Store as a fact or preference (e.g., user likes dark mode).
  - Vector embeddings enable finding related preferences and facts.

### B. Memory Editing & Improvement
- **Memory Merging:**
  - Combine similar memories into comprehensive ones.
  - Preserve original memory IDs and merge history.
  - Update both SQL metadata and vector content.
- **Memory Enhancement:**
  - Add error handling and validation to procedures.
  - Enrich semantic memories with context and confidence.
  - Add insights and causal analysis to episodes.
- **Quality Assessment:**
  - Evaluate memories across multiple dimensions.
  - Provide improvement recommendations.
- **Conflict Resolution:**
  - Detect and resolve contradictory memories.
  - Maintain data integrity and consistency.

### Example Storage API Calls
- `POST /memory/chrome_action` — Store a Chrome action as an episode.
- `POST /memory/feedback` — Store feedback as an episode.
- `POST /memory/workflow_execution` — Store workflow execution as episode/procedure.
- `POST /memory/store` — Store a semantic fact or preference.
- `POST /memory/merge` — Merge similar memories.
- `POST /memory/improve/{memory_id}` — Improve a specific memory.

---

## Retrieval Flows

### Hybrid Search Endpoints
- **Efficient Hybrid Search:**
  - `POST /api/memory/vector/efficient-search` — SQL metadata + Vector content search
  - `POST /api/memory/vector/hybrid-search` — Combined SQL + Vector approach
  - `POST /api/memory/vector/search-hierarchical` — Hierarchical context search

### Traditional Endpoints
- **Episodic:**
  - `GET /memory/episodes` — Retrieve recent or similar episodes for few-shot prompting.
- **Semantic:**
  - `GET /memory/facts` — Retrieve facts/preferences for context augmentation.
- **Procedural:**
  - `GET /memory/procedures` — Retrieve workflows/procedures for automation suggestions.
- **Quality Assessment:**
  - `GET /memory/assess-quality/{memory_id}` — Evaluate memory quality.
  - `GET /memory/quality-report` — Comprehensive quality analysis.
- **Conflict Detection:**
  - `GET /memory/detect-conflicts` — Find conflicting memories.
- **Evolution Tracking:**
  - `GET /memory/evolution/{memory_id}` — Track memory changes over time.

### Search Performance Comparison
The hybrid system provides significant performance improvements:
- **SQL-only search**: Fast metadata filtering, limited semantic capabilities
- **Vector-only search**: Excellent semantic matching, expensive on large datasets
- **Efficient hybrid search**: Optimal balance of speed and accuracy

---

## Memory Editing & Improvement System

### 1. Memory Merging & Consolidation
The system can automatically find and merge similar memories to reduce redundancy and create richer, more comprehensive knowledge.

**Features:**
- **Similarity Detection**: Automatically finds memories with high similarity scores (85%+ by default)
- **Intelligent Merging**: Combines similar memories into richer, more comprehensive ones
- **Type-Specific Merging**: Different strategies for episodic, procedural, and semantic memories
- **Metadata Preservation**: Tracks original memory IDs and merge history
- **Vector Content Updates**: Updates both SQL metadata and vector embeddings

**Example:**
```python
# Find memories about email checking
mergeable_groups = memory_service.find_mergeable_memories(
    user_id=user_id, 
    namespace='episodes', 
    similarity_threshold=0.85
)

# Merge similar email checking memories
merged_memory = memory_service.merge_memories(
    user_id=user_id,
    memory_ids=['mem_001', 'mem_002', 'mem_003'],
    merge_type='episodic'
)
```

### 2. Memory Improvement & Enhancement
Memories can be automatically enhanced to improve their quality, completeness, and usefulness.

**Features:**
- **Procedural Enhancement**: Adds error handling, validation steps, and optimization to workflows
- **Semantic Enhancement**: Enriches facts with context, confidence levels, and related concepts
- **Episodic Enhancement**: Adds insights, causal analysis, and performance metrics
- **Automatic Improvement**: AI-powered enhancement based on memory type
- **Vector Content Updates**: Updates semantic embeddings when content improves

**Example:**
```python
# Improve a workflow procedure
improved_memory = memory_service.improve_memory(
    user_id=user_id,
    memory_id='proc_001',
    improvement_type='procedural'
)

# The improved workflow now includes:
# - Validation steps after each action
# - Error handling and recovery
# - Performance metrics
# - Success verification
```

### 3. Memory Quality Assessment
The system provides comprehensive quality evaluation across multiple dimensions.

**Quality Metrics:**
- **Completeness**: How much information is available
- **Accuracy**: Reliability of the information
- **Usefulness**: How actionable the memory is
- **Clarity**: How clear and understandable the memory is
- **Consistency**: How well it aligns with other memories

**Example:**
```python
# Assess individual memory quality
quality_scores = memory_service.assess_memory_quality(user_id, memory_id)
# Returns: {'completeness': 0.8, 'accuracy': 0.9, 'usefulness': 0.7, ...}

# Get comprehensive quality report
quality_report = memory_service.get_quality_report(user_id, namespace='episodes')
```

### 4. Memory Conflict Detection & Resolution
The system automatically detects and resolves conflicting memories to maintain data integrity.

**Conflict Types:**
- **Outcome Conflicts**: Same action, different results
- **Temporal Conflicts**: Inconsistent timestamps
- **Data Conflicts**: Contradictory information

**Example:**
```python
# Detect conflicts
conflicts = memory_service.detect_memory_conflicts(user_id, namespace='episodes')

# Resolve conflicts
resolutions = memory_service.resolve_memory_conflicts(user_id, conflicts)
```

### 5. Memory Evolution Tracking
All changes to memories are tracked to provide a complete audit trail.

**Features:**
- **Version History**: Tracks all changes to memories over time
- **Change Types**: Records updates, merges, improvements, and conflict resolutions
- **Evolution Timeline**: Shows how memories have evolved
- **Audit Trail**: Complete history for debugging and analysis

### 6. Bulk Operations & Automation
The system supports efficient bulk operations for large-scale memory management.

**Features:**
- **Bulk Improvement**: Improve multiple memories simultaneously
- **Auto-Consolidation**: Automatically merge similar memories
- **Batch Processing**: Efficient handling of large memory sets
- **Progress Tracking**: Monitor bulk operation progress

---

## Hierarchical Memory System ✅ IMPLEMENTED

The Hierarchical Memory System provides advanced contextual state management with influence propagation through parent-child relationships. This system allows high-level contexts (like "vacation mode") to influence all lower-level decisions and behaviors.

### Key Features

#### 1. **Contextual State Management**
- **Global Context States**: High-level states that influence all agent decisions (vacation, work mode, health status)
- **Context Inheritance Chains**: Automatic propagation of context influences through parent-child relationships
- **Context Conflict Resolution**: Priority-based resolution when multiple contexts conflict
- **Context Persistence**: Long-term storage and retrieval of contextual states

#### 2. **Influence Rule Engine**
The system uses sophisticated influence rules to modify context data:

**Rule Types:**
- **Override**: Direct replacement of values
- **Modify**: Mathematical operations on existing values
- **Add**: Addition of new values if they don't exist
- **Conditional**: If-then logic for complex decision making

**Example Influence Rules:**
```python
influence_rules = {
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
}
```

#### 3. **Context Hierarchy Management**
- **Parent-Child Relationships**: Contexts can have hierarchical relationships
- **Level Tracking**: Automatic level calculation based on hierarchy depth
- **Path Management**: Full path tracking from root to leaf contexts
- **Priority System**: Priority-based conflict resolution

#### 4. **Decision Context Aggregation**
The system automatically combines all relevant contexts for specific decisions:

```python
# Get combined context for email handling decision
decision_context = memory_service.get_combined_context_for_decision(
    user_id=user_id,
    decision_type='email_handling'
)
```

### Example Use Case: Vacation Context

**Creating a Vacation Context:**
```python
# Create main vacation context
vacation_context = memory_service.create_hierarchical_context(
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
    priority=100  # High priority to override other contexts
)

# Create child context for email preferences
email_context = memory_service.create_hierarchical_context(
    user_id=user_id,
    name="Vacation Email Preferences",
    description="Email handling preferences during vacation",
    context_data={
        "check_frequency": "once_per_day",
        "auto_reply_enabled": True,
        "urgent_only": True
    },
    parent_id=vacation_context.memory_id,
    influence_rules={
        "override": {
            "email_urgency_threshold": "critical_only",
            "response_time_expectation": "24_hours"
        }
    }
)
```

**How It Influences Decisions:**
- **Email Checking**: Reduced from every 30 minutes to once per day
- **Meeting Acceptance**: Declined automatically due to vacation mode
- **Response Times**: Extended from 2 hours to 24 hours
- **Work Priority**: Minimized to focus on relaxation

### API Endpoints

#### Hierarchical Context Management
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/memory/hierarchical/context` | POST | Create hierarchical context |
| `/api/memory/hierarchical/contexts` | GET | Get all active contexts |
| `/api/memory/hierarchical/context/<id>` | GET | Get specific context influence |
| `/api/memory/hierarchical/context/<id>` | PUT | Update context |
| `/api/memory/hierarchical/context/<id>` | DELETE | Delete context |
| `/api/memory/hierarchical/root-contexts` | GET | Get root-level contexts |
| `/api/memory/hierarchical/context/<id>/children` | GET | Get child contexts |

#### Decision Context
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/memory/hierarchical/decision-context` | POST | Get combined decision context |
| `/api/memory/hierarchical/contextualized/<namespace>` | GET | Get contextualized memories |

### Service Methods

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

### Benefits

1. **Contextual Intelligence**: Agent decisions are influenced by current context
2. **Behavioral Adaptation**: Agent behavior adapts to user's current state
3. **Priority Management**: High-priority contexts override lower-priority ones
4. **Inheritance**: Child contexts inherit and can modify parent influences
5. **Flexibility**: Complex influence rules allow sophisticated behavior modification

### Testing

A comprehensive demo is available at `tests/test_hierarchical_memory.py` that demonstrates:
- Vacation context creation and influence
- Child context inheritance
- Decision context aggregation
- Agent behavior simulation with context

---

## Prompt Engineering Strategy

When generating a response, the agent should:
1. **Retrieve relevant memories:**
    - Recent episodes (user actions, feedback, workflow executions)
    - Semantic facts/preferences
    - Procedural memories (workflows/scripts)
    - Quality-assessed memories (prefer high-quality memories)
2. **Build a context-rich prompt:**
    - Summarize and include relevant facts and recent actions.
    - List available workflows or procedures.
    - Consider memory quality scores for weighting.
    - Add the user's current message.
3. **Send the prompt to the LLM:**
    - The LLM uses this context to generate a more helpful, personalized, and proactive response.

### Example Prompt Construction

```
User Preferences and Facts:
- User prefers dark mode
- Bob's email is bob@example.com

Recent User Actions and Feedback:
- Chrome: click button#submit on https://example.com (success)
- Feedback: accepted (This suggestion worked well!)
- Workflow: wf_001 result: success

Available Workflows/Procedures:
- How to start a Zoom meeting (steps: 2, quality: 0.9)

Memory Quality Insights:
- High-quality procedural memory available for Zoom meetings
- Recent email checking pattern detected (3 similar episodes merged)

User says: Can you help me start a Zoom meeting?
How should the agent respond or assist?
```

---

## API Endpoints Summary

### Storage Endpoints
| Endpoint                      | Method | Purpose                                 |
|-------------------------------|--------|-----------------------------------------|
| /memory/chrome_action         | POST   | Store a Chrome action (episodic)        |
| /memory/feedback              | POST   | Store feedback (episodic)               |
| /memory/workflow_execution    | POST   | Store workflow execution (episodic/proc)|
| /memory/store                 | POST   | Store semantic fact/preference          |

### Retrieval Endpoints
| Endpoint                      | Method | Purpose                                 |
|-------------------------------|--------|-----------------------------------------|
| /memory/episodes              | GET    | Retrieve episodic memories              |
| /memory/facts                 | GET    | Retrieve semantic memories              |
| /memory/procedures            | GET    | Retrieve procedural memories            |

### Memory Editing Endpoints
| Endpoint                      | Method | Purpose                                 |
|-------------------------------|--------|-----------------------------------------|
| /memory/find-mergeable        | GET    | Find memories that can be merged        |
| /memory/merge                 | POST   | Merge multiple memories                 |
| /memory/improve/{memory_id}   | POST   | Improve a specific memory               |
| /memory/assess-quality/{memory_id} | GET | Assess memory quality               |
| /memory/quality-report        | GET    | Get comprehensive quality report        |
| /memory/detect-conflicts      | GET    | Detect memory conflicts                 |
| /memory/resolve-conflicts     | POST   | Resolve memory conflicts                |
| /memory/evolution/{memory_id} | GET    | Get memory evolution history            |
| /memory/bulk-improve          | POST   | Bulk improve multiple memories          |
| /memory/auto-consolidate      | POST   | Auto-consolidate similar memories       |

### Vector Search Endpoints
| Endpoint                      | Method | Purpose                                 |
|-------------------------------|--------|-----------------------------------------|
| /api/memory/vector/efficient-search | POST | SQL metadata + Vector content search |
| /api/memory/vector/hybrid-search | POST | Combined SQL + Vector approach |
| /api/memory/vector/search-hierarchical | POST | Hierarchical context search |
| /api/memory/vector/update-content | POST | Update memory content in vector DB |
| /api/memory/vector/delete-content | DELETE | Delete memory content from vector DB |
| /api/memory/vector/content/{vector_id} | GET | Get memory content by vector ID |

### Hierarchical Memory Endpoints
| Endpoint                      | Method | Purpose                                 |
|-------------------------------|--------|-----------------------------------------|
| /api/memory/hierarchical/context | POST | Create hierarchical context |
| /api/memory/hierarchical/contexts | GET | Get all active contexts |
| /api/memory/hierarchical/context/<id> | GET | Get specific context influence |
| /api/memory/hierarchical/context/<id> | PUT | Update context |
| /api/memory/hierarchical/context/<id> | DELETE | Delete context |
| /api/memory/hierarchical/root-contexts | GET | Get root-level contexts |
| /api/memory/hierarchical/context/<id>/children | GET | Get child contexts |
| /api/memory/hierarchical/decision-context | POST | Get combined decision context |
| /api/memory/hierarchical/contextualized/<namespace> | GET | Get contextualized memories |

---

## Extensibility
- **New event types** (e.g., video summaries, new tool actions) can be added by storing them as episodes with appropriate `memory_data`.
- **Semantic search** can be enabled for all memory types by embedding and indexing the `search_text` field.
- **Procedural memory** can be refined by allowing the agent to update or merge workflows based on user feedback or new executions.
- **Memory editing** capabilities can be extended with new improvement types and quality metrics.

---

## High Level Overview of Context Engineering
- **Write Context:** Long-term Memories(across agent sessions), Scratchpad (within agent session), State (within agent session)
- **Select Context:** Retrieval of working memory, state, long term memory
- **Trim Context:** Summarize or remove irrelevant context (Only pass in the most relevant context)
- **Isolate Context:** Partition context in state, Hold context in environment, Partition across multiple agents

---

## Vector Database Integration

### ChromaDB Implementation
The system uses ChromaDB as the vector database with the following features:

- **Persistent Storage**: ChromaDB persists embeddings to disk for reliability
- **Sentence Transformers**: Uses 'all-MiniLM-L6-v2' for efficient embeddings
- **Separate Collections**: Different collections for memory content and context content
- **Metadata Filtering**: Efficient filtering by user_id, namespace, memory_type

### Vector Storage Strategy
```python
# Memory content collection
memory_collection = client.get_or_create_collection("memory_content")

# Context content collection  
context_collection = client.get_or_create_collection("context_content")

# Efficient storage with metadata
collection.add(
    embeddings=[embedding],
    documents=[content_text],
    metadatas=[{
        'memory_id': memory.memory_id,
        'user_id': memory.user_id,
        'namespace': memory.namespace,
        'memory_type': memory.memory_type,
        'content_hash': hash(content_text)
    }],
    ids=[vector_id]
)
```

### Efficient Hybrid Search Implementation
```python
def efficient_hybrid_search(query, user_id, namespace, n_results=10):
    # Step 1: SQL metadata filtering (fast)
    sql_candidates = get_sql_candidates(user_id, namespace, query)
    
    # Step 2: Vector search only on filtered content (efficient)
    vector_results = search_vector_content(query, memory_ids, n_results)
    
    # Step 3: Combine and rank results
    combined_results = combine_sql_vector_results(sql_candidates, vector_results)
    
    return combined_results
```

### Performance Benefits
- **Reduced Vector Search Cost**: Only searches relevant content subsets
- **Faster Metadata Queries**: SQL handles filtering efficiently
- **Better Scalability**: Scales independently for metadata and content
- **Optimal Resource Usage**: Balances CPU and memory usage

---

## Security & Privacy

### Data Protection
- **User Isolation**: All memories are isolated by user_id
- **Access Control**: Role-based access control for memory operations
- **Encryption**: Sensitive data can be encrypted at rest and in transit
- **Audit Logging**: Complete audit trail for memory access and modifications

### Privacy Features
- **Data Expiration**: Configurable expiration policies for sensitive data
- **Anonymization**: Optional anonymization of personal information
- **Consent Management**: User control over memory storage and retention
- **Compliance**: GDPR and privacy regulation compliance features

---

## Monitoring & Observability

### Performance Metrics
- **Search Latency**: Track hybrid search performance
- **Vector Search Cost**: Monitor vector database resource usage
- **Memory Usage**: Track storage growth and optimization opportunities
- **Quality Metrics**: Monitor memory quality over time

### Health Monitoring
- **Database Health**: Monitor SQL and vector database status
- **Service Availability**: Track memory service uptime
- **Error Rates**: Monitor failure rates and error patterns
- **Resource Utilization**: Track CPU, memory, and storage usage

---

## Best Practices

### 1. Memory Organization
- Use appropriate namespaces for different memory types
- Set meaningful importance scores for memory prioritization
- Regularly clean up outdated or low-quality memories

### 2. Search Optimization
- Use efficient hybrid search for complex queries
- Leverage SQL filtering for simple metadata queries
- Set appropriate similarity thresholds for vector search

### 3. Performance Tuning
- Monitor vector database performance and scale as needed
- Optimize embedding model selection for your use case
- Use batch operations for large-scale memory management

### 4. Quality Management
- Regularly assess memory quality and improve low-quality memories
- Merge similar memories to reduce redundancy
- Resolve conflicts promptly to maintain data integrity

---

## Future Enhancements

### Planned Features
- **Knowledge Graph Integration**: Add graph relationships between memories
- **Advanced Memory Synthesis**: AI-powered memory creation and synthesis
- **Distributed Memory**: Support for distributed memory storage
- **Memory Compression**: Advanced compression and summarization techniques

### Research Directions
- **Multi-Modal Memory**: Support for images, audio, and video memories
- **Temporal Reasoning**: Advanced time-based memory organization
- **Collaborative Memory**: Shared memory across multiple agents
- **Memory Intelligence**: Self-improving memory systems

---

## High Level Overview of Context Engineering
- **Write Context:** Long-term Memories(across agent sessions), Scratchpad (within agent session), State (within 
agent session)
- **Select Context:** Retreival of working memory, state, long term memory
- **Trim Context:** Summarize or remove irrelevant context (Only pass in the most relevant context)
- **Isolate Context:** Partition context in state, Hold context in environment, Partition across multiple agents