# Jarvus Agent Memory System

## Overview

The Jarvus Agent Memory System provides comprehensive memory management capabilities for storing, retrieving, editing, and improving user interactions and knowledge. The system supports multiple memory types, hierarchical organization, and intelligent memory operations.

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


| Type        | Content                    | Use Cases                    | Storage Format |
|-------------|----------------------------|------------------------------|----------------|
| Episodic    | User actions, events, feedback | Context, patterns, learning | memory_type='episode' |
| Semantic    | Facts, preferences, extracted info| Personalization, Q&A, context    | memory_type='fact'/'preference'|
| Procedural  | Workflows, scripts, prompts       | Automation, suggestions, self-improve | memory_type='procedure'/'workflow'|
| Hierarchical| Contextual states, influence rules| Decision making, behavior adaptation | memory_type='context' |

- **ShortTermMemory** is used for thread-level (conversation/session) context.
- **MemoryEmbedding** supports semantic search for facts and episodes.
- **HierarchicalMemory** provides contextual influence and state management.

---

## Storage Flows

### A. Storing Observations and Feedback
- **Chrome Action:**
  - Store as an episode with details (action, target, url, result, timestamp).
- **Feedback:**
  - Store as an episode (user response, notes, suggestion reference).
- **Workflow Execution:**
  - Store as an episode (steps, result, details).
  - Optionally, store as a procedure if it's a new workflow.
- **Semantic Fact/Preference:**
  - Store as a fact or preference (e.g., user likes dark mode).

### B. Memory Editing & Improvement
- **Memory Merging:**
  - Combine similar memories into comprehensive ones.
  - Preserve original memory IDs and merge history.
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

---

## Memory Editing & Improvement System

### 1. Memory Merging & Consolidation
The system can automatically find and merge similar memories to reduce redundancy and create richer, more comprehensive knowledge.

**Features:**
- **Similarity Detection**: Automatically finds memories with high similarity scores (85%+ by default)
- **Intelligent Merging**: Combines similar memories into richer, more comprehensive ones
- **Type-Specific Merging**: Different strategies for episodic, procedural, and semantic memories
- **Metadata Preservation**: Tracks original memory IDs and merge history

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

---

## Extensibility
- **New event types** (e.g., video summaries, new tool actions) can be added by storing them as episodes with appropriate `memory_data`.
- **Semantic search** can be enabled for all memory types by embedding and indexing the `search_text` field.
- **Procedural memory** can be refined by allowing the agent to update or merge workflows based on user feedback or new executions.
- **Memory editing** capabilities can be extended with new improvement types and quality metrics.

---

## Best Practices
- **Always compress and summarize** observations before storing to avoid bloat.
- **Use importance scores** to prioritize what gets retrieved or surfaced to the agent.
- **Regularly review and merge** old episodes into semantic/procedural memories for efficiency.
- **Leverage embeddings** for semantic search and similarity-based retrieval.
- **Monitor memory quality** and improve low-quality memories.
- **Resolve conflicts** to maintain data integrity.
- **Track memory evolution** for debugging and analysis.

---

## Future Directions
- **Automated memory compression:** Use LLMs to summarize and merge old episodes.
- **User-editable memory:** Allow users to view and edit their own facts/preferences.
- **Memory visualization:** Build UI to show the agent's "mind" and memory traces.
- **Cross-agent memory:** Share anonymized procedures or facts between agents for collective learning.
- **Advanced LLM-powered merging:** Use AI to create more intelligent merged memories.
- **Memory synthesis:** Create new memories by combining existing ones.
- **Predictive improvement:** Anticipate and prevent quality issues. 