# Jarvus Agent Memory System

## Overview

The Jarvus agent memory system is designed to enable rich, context-aware, and adaptive behavior for general-purpose agents. It supports multiple types of memory inspired by cognitive science—**episodic, semantic, and procedural**—to help the agent learn from user interactions, store and retrieve knowledge, and automate workflows.

---

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

---

## Data Model

All memory types are stored in the `LongTermMemory` table, differentiated by the `memory_type` field:

| Memory Type   | Example Data Stored                | Use Case                        | Model Field         |
|---------------|-----------------------------------|----------------------------------|---------------------|
| Episodic      | User actions, feedback, executions| Few-shot, context, learning      | memory_type='episode'|
| Semantic      | Facts, preferences, extracted info| Personalization, Q&A, context    | memory_type='fact'/'preference'|
| Procedural    | Workflows, scripts, prompts       | Automation, suggestions, self-improve | memory_type='procedure'/'workflow'|

- **ShortTermMemory** is used for thread-level (conversation/session) context.
- **MemoryEmbedding** supports semantic search for facts and episodes.

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

### Example Storage API Calls
- `POST /memory/chrome_action` — Store a Chrome action as an episode.
- `POST /memory/feedback` — Store feedback as an episode.
- `POST /memory/workflow_execution` — Store workflow execution as episode/procedure.
- `POST /memory/store` — Store a semantic fact or preference.

---

## Retrieval Flows

- **Episodic:**
  - `GET /memory/episodes` — Retrieve recent or similar episodes for few-shot prompting.
- **Semantic:**
  - `GET /memory/facts` — Retrieve facts/preferences for context augmentation.
- **Procedural:**
  - `GET /memory/procedures` — Retrieve workflows/procedures for automation suggestions.

---

## Prompt Engineering Strategy

When generating a response, the agent should:
1. **Retrieve relevant memories:**
    - Recent episodes (user actions, feedback, workflow executions)
    - Semantic facts/preferences
    - Procedural memories (workflows/scripts)
2. **Build a context-rich prompt:**
    - Summarize and include relevant facts and recent actions.
    - List available workflows or procedures.
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
- How to start a Zoom meeting (steps: 2)

User says: Can you help me start a Zoom meeting?
How should the agent respond or assist?
```

---

## Extensibility
- **New event types** (e.g., video summaries, new tool actions) can be added by storing them as episodes with appropriate `memory_data`.
- **Semantic search** can be enabled for all memory types by embedding and indexing the `search_text` field.
- **Procedural memory** can be refined by allowing the agent to update or merge workflows based on user feedback or new executions.

---

## API Endpoints Summary

| Endpoint                      | Method | Purpose                                 |
|-------------------------------|--------|-----------------------------------------|
| /memory/chrome_action         | POST   | Store a Chrome action (episodic)        |
| /memory/feedback              | POST   | Store feedback (episodic)               |
| /memory/workflow_execution    | POST   | Store workflow execution (episodic/proc)|
| /memory/store                 | POST   | Store semantic fact/preference          |
| /memory/episodes              | GET    | Retrieve episodic memories              |
| /memory/facts                 | GET    | Retrieve semantic memories              |
| /memory/procedures            | GET    | Retrieve procedural memories            |

---

## Best Practices
- **Always compress and summarize** observations before storing to avoid bloat.
- **Use importance scores** to prioritize what gets retrieved or surfaced to the agent.
- **Regularly review and merge** old episodes into semantic/procedural memories for efficiency.
- **Leverage embeddings** for semantic search and similarity-based retrieval.

---

## Future Directions
- **Automated memory compression:** Use LLMs to summarize and merge old episodes.
- **User-editable memory:** Allow users to view and edit their own facts/preferences.
- **Memory visualization:** Build UI to show the agent's "mind" and memory traces.
- **Cross-agent memory:** Share anonymized procedures or facts between agents for collective learning. 