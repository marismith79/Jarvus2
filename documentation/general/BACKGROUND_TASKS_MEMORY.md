# Background Memory Storing with Celery in Jarvus

## Overview

To ensure a responsive user experience, Jarvus offloads slow or heavy operations—such as extracting and storing agent memories—to a background task queue using [Celery](https://docs.celeryq.dev/). This allows the web server to return responses to users immediately, while memory processing happens asynchronously in a separate worker process.

## Why Use Celery?
- **Responsiveness:** Users get chatbot responses instantly, without waiting for memory extraction/storage.
- **Reliability:** Background tasks are retried on failure and can be monitored.
- **Scalability:** Heavy workloads are distributed across multiple worker processes or machines.

## How It Works
1. **User sends a message** to the chatbot.
2. **The chatbot responds immediately** with the assistant's reply.
3. **Memory extraction and storage** (episodic, semantic, procedural) is triggered as a Celery background task, using the conversation and tool call data.

## Implementation Details

### 1. Celery Setup
- Celery is configured to use Redis as both the broker and result backend.
- The Celery app is defined in `jarvus_app/celery_app.py`.

### 2. Defining the Task
- The background task is defined in `jarvus_app/services/agent_service.py` as `store_memories_from_interaction_task`.
- This task calls the memory service's `extract_and_store_memories` method.

### 3. Triggering the Task
- Instead of calling memory extraction synchronously, the agent service now calls the Celery task using `.delay()`.
- The user receives the chatbot response immediately.

### 4. Running the Worker
- Start a Celery worker in your project root:
  ```sh
  celery -A jarvus_app.celery_app.celery worker --loglevel=info
  ```
- Ensure Redis is running and accessible at `redis://localhost:6379/0` (or update the URL as needed).

## Developer Setup

1. **Install dependencies:**
   ```sh
   pip install celery[redis] redis
   ```
2. **Start Redis:**
   - On macOS: `brew install redis && brew services start redis`
   - Or use Docker: `docker run -p 6379:6379 redis`
3. **Start the Celery worker:**
   ```sh
   celery -A jarvus_app.celery_app.celery worker --loglevel=info
   ```
4. **Run your Flask app as usual.**

## Configuration
- The Celery broker and backend URLs are set in `jarvus_app/celery_app.py`. Update these if your Redis instance is elsewhere.

## Troubleshooting
- If tasks are not running, ensure the Celery worker is active and connected to Redis.
- Check logs for errors in the worker process.

## References
- [Celery Documentation](https://docs.celeryq.dev/)
- [Flask + Celery Guide](https://flask.palletsprojects.com/en/latest/patterns/celery/) 