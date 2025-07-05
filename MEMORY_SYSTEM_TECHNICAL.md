# Jarvus Agent Memory System — Technical Specification

## 1. Data Model Details

### 1.1 LongTermMemory Table
- **Purpose:** Stores all long-term memories (episodic, semantic, procedural)
- **Fields:**
  - `id`: Integer, primary key
  - `user_id`: Integer, foreign key to users.id
  - `namespace`: String (255), e.g., 'memories', 'agent_config'
  - `memory_id`: String (255), unique per memory (UUID)
  - `memory_data`: JSON, arbitrary dict (see below for schema examples)
  - `embedding_vector`: Text, JSON-encoded list of floats (optional, for semantic search)
  - `search_text`: Text, plain text for embedding/indexing
  - `memory_type`: String (50), e.g., 'episode', 'fact', 'preference', 'procedure', 'workflow'
  - `importance_score`: Float, for ranking/prioritization
  - `created_at`: DateTime
  - `updated_at`: DateTime
  - `last_accessed`: DateTime

#### Example `memory_data` for each type:
- **Episodic:**
  ```json
  {
    "type": "chrome_action",
    "action": "click",
    "target": "button#submit",
    "url": "https://example.com",
    "result": "success",
    "timestamp": "2024-06-01T12:00:00Z",
    "details": {"extra": "Clicked submit on login form"}
  }
  ```
- **Semantic (Fact/Preference):**
  ```json
  {
    "type": "preference",
    "text": "User prefers dark mode"
  }
  ```
- **Procedural (Workflow):**
  ```json
  {
    "type": "workflow",
    "steps": [
      {"action": "open_url", "url": "https://zoom.us"},
      {"action": "click", "target": "Start Meeting"}
    ],
    "description": "How to start a Zoom meeting",
    "created_from_execution": true
  }
  ```

### 1.2 ShortTermMemory Table
- **Purpose:** Thread/session-level context (recent messages, state)
- **Fields:**
  - `id`: Integer, primary key
  - `thread_id`: String (255), e.g., 'thread_1234'
  - `user_id`: Integer, foreign key
  - `agent_id`: Integer, foreign key
  - `state_data`: JSON, e.g., `{ "messages": [...], ... }`
  - `checkpoint_id`: String (255), for versioning
  - `step_number`: Integer, for ordering
  - `parent_checkpoint_id`: String (255), for lineage
  - `created_at`, `updated_at`: DateTime

### 1.3 MemoryEmbedding Table
- **Purpose:** Store vector embeddings for semantic search
- **Fields:**
  - `id`: Integer, primary key
  - `memory_id`: Integer, foreign key to LongTermMemory.id
  - `embedding_vector`: Text, JSON-encoded list of floats
  - `embedding_model`: String (100), e.g., 'text-embedding-3-small'
  - `embedding_dimensions`: Integer
  - `created_at`: DateTime

---

## 2. API Contract Details

### 2.1 Storage Endpoints

#### POST `/memory/chrome_action`
- **Request JSON:**
  ```json
  {
    "action": "click",
    "target": "button#submit",
    "url": "https://example.com",
    "result": "success",
    "timestamp": "2024-06-01T12:00:00Z",
    "details": {"extra": "Clicked submit on login form"}
  }
  ```
- **Behavior:**
  - Stores as `memory_type='episode'` in `LongTermMemory`.
  - `search_text` is auto-generated from action, target, url.
  - Returns `{ "memory_id": ... }`

#### POST `/memory/feedback`
- **Request JSON:**
  ```json
  {
    "suggestion_id": "12345",
    "user_response": "accepted",
    "notes": "This suggestion worked well!",
    "timestamp": "2024-06-01T12:01:00Z"
  }
  ```
- **Behavior:**
  - Stores as `memory_type='episode'`.
  - `search_text` includes user_response and notes.

#### POST `/memory/workflow_execution`
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

### 2.2 Retrieval Endpoints

#### GET `/memory/episodes?query=...&limit=5`
- **Returns:** `{ "episodes": [ ... ] }` (only `memory_type='episode'`)

#### GET `/memory/facts?query=...&limit=5`
- **Returns:** `{ "facts": [ ... ] }` (only `memory_type in ('fact', 'preference')`)

#### GET `/memory/procedures?query=...&limit=5`
- **Returns:** `{ "procedures": [ ... ] }` (only `memory_type in ('procedure', 'workflow')`)

- **All retrieval endpoints** support substring search on `search_text` and limit results.

---

## 3. Storage/Retrieval Logic

### 3.1 Storage
- **All storage endpoints** call `memory_service.store_memory()` with appropriate fields.
- **If embedding is enabled:**
  - The `search_text` is embedded (e.g., using OpenAI or local model).
  - The embedding is stored in `embedding_vector` and/or `MemoryEmbedding`.
- **Importance score** is set based on event type or user input.
- **Timestamps** are set to current UTC if not provided.

### 3.2 Retrieval
- **All retrieval endpoints** call `memory_service.search_memories()`.
- **If query is provided:**
  - Substring search on `search_text` (default).
  - If embeddings are enabled, semantic similarity search is performed (cosine similarity on vectors).
- **Results** are filtered by `memory_type` and sorted by `importance_score` and `last_accessed`.

---

## 4. Memory Lifecycle

### 4.1 Creation
- Created via API endpoints or internal service calls.
- Each memory is assigned a UUID (`memory_id`).
- Embeddings are generated if semantic search is enabled.

### 4.2 Access
- Each retrieval updates `last_accessed`.
- Access patterns can be used for memory pruning or summarization.

### 4.3 Update
- Memories can be updated by re-calling `store_memory` with the same `memory_id`.
- For facts/preferences, this allows user edits.

### 4.4 Deletion
- Memories can be deleted via API or admin tools.
- Deletion cascades to embeddings.

### 4.5 Compression/Summarization (Future)
- Old episodes can be summarized and merged into semantic/procedural memories.
- LLMs can be used to generate summaries or extract facts from episodes.

---

## 5. Embedding and Semantic Search

### 5.1 Embedding Generation
- **When storing:**
  - If `search_text` is present and embedding is enabled, generate embedding vector.
  - Store in `embedding_vector` (LongTermMemory) and/or `MemoryEmbedding`.
- **Supported models:**
  - OpenAI (e.g., `text-embedding-3-small`)
  - Local models (e.g., SentenceTransformers)

### 5.2 Semantic Search
- **On retrieval:**
  - If query is provided and embedding is enabled, embed the query.
  - Compute cosine similarity with stored vectors.
  - Return top-N most similar memories.
- **Fallback:**
  - If no embedding, use substring search on `search_text`.

---

## 6. Prompt Engineering Implementation

### 6.1 Retrieval for Prompt Construction
- **Before generating a response:**
  - Retrieve:
    - Recent episodes (e.g., last 3-5)
    - Relevant facts/preferences (semantic)
    - Available procedures/workflows
- **Filter and summarize** as needed (e.g., only include most recent or most important).

### 6.2 Prompt Template Example
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
        prompt_parts.append(f"- {desc} (steps: {len(steps)})")
prompt_parts.append(f"\nUser says: {user_message}")
prompt_parts.append("How should the agent respond or assist?")
prompt = "\n".join(prompt_parts)
```

### 6.3 LLM Call
- The constructed prompt is sent to the LLM (e.g., via OpenAI, Azure, or local model).
- The LLM uses the context to generate a response, suggest workflows, or ask clarifying questions.

---

## 7. Security and Privacy Considerations
- **User data isolation:** All memories are namespaced and user_id-scoped.
- **Sensitive data:** Avoid storing PII in plain text; consider encryption for sensitive fields.
- **Access control:** Only authenticated users can access their own memories.
- **Audit logging:** All memory creation, update, and deletion events should be logged for traceability.

---

## 8. Extensibility and Future Work
- **New memory types:** Add new `memory_type` values and schemas as needed.
- **Automated summarization:** Periodically compress old episodes into semantic/procedural memories.
- **User-facing memory management:** Allow users to view, edit, and delete their own memories.
- **Cross-agent sharing:** Enable sharing of anonymized procedures/facts for collective learning.
- **Advanced semantic search:** Integrate with vector databases for large-scale memory retrieval. 