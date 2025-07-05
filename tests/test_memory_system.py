import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000/memory"
SESSION = requests.Session()  # Use this if you need to persist cookies/auth

def pretty_print(title, data):
    print(f"\n=== {title} ===")
    print(json.dumps(data, indent=2))

# 1. Store a Chrome action (episodic)
chrome_action = {
    "action": "click",
    "target": "button#submit",
    "url": "https://example.com",
    "result": "success",
    "timestamp": datetime.utcnow().isoformat(),
    "details": {"extra": "Clicked submit on login form"}
}
resp = SESSION.post(f"{BASE_URL}/chrome_action", json=chrome_action)
pretty_print("Store Chrome Action", resp.json())

# 2. Store feedback (episodic)
feedback = {
    "suggestion_id": "12345",
    "user_response": "accepted",
    "notes": "This suggestion worked well!",
    "timestamp": datetime.utcnow().isoformat()
}
resp = SESSION.post(f"{BASE_URL}/feedback", json=feedback)
pretty_print("Store Feedback", resp.json())

# 3. Store a workflow execution (episodic + procedural)
workflow = {
    "workflow_id": "wf_001",
    "steps": [
        {"action": "open_url", "url": "https://zoom.us"},
        {"action": "click", "target": "Start Meeting"}
    ],
    "result": "success",
    "timestamp": datetime.utcnow().isoformat(),
    "details": {"note": "Started a Zoom meeting"},
    "store_as_procedure": True,
    "description": "How to start a Zoom meeting"
}
resp = SESSION.post(f"{BASE_URL}/workflow_execution", json=workflow)
pretty_print("Store Workflow Execution", resp.json())

# 4. Store a semantic fact (preference)
fact = {
    "text": "User prefers dark mode",
    "type": "preference",
    "importance": 1.5
}
resp = SESSION.post(f"{BASE_URL}/store", json=fact)
pretty_print("Store Semantic Fact", resp.json())

# 5. Retrieve recent episodes
resp = SESSION.get(f"{BASE_URL}/episodes", params={"limit": 3})
episodes = resp.json().get("episodes", [])
pretty_print("Retrieve Episodes", episodes)

# 6. Retrieve facts/preferences
resp = SESSION.get(f"{BASE_URL}/facts", params={"limit": 3})
facts = resp.json().get("facts", [])
pretty_print("Retrieve Facts", facts)

# 7. Retrieve procedures/workflows
resp = SESSION.get(f"{BASE_URL}/procedures", params={"limit": 3})
procedures = resp.json().get("procedures", [])
pretty_print("Retrieve Procedures", procedures)

# 8. Prompt Engineering Example
def build_agent_prompt(episodes, facts, procedures, user_message):
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
    return "\n".join(prompt_parts)

# Example usage:
user_message = "Can you help me start a Zoom meeting?"
prompt = build_agent_prompt(episodes, facts, procedures, user_message)
pretty_print("Agent Prompt", {"prompt": prompt})

# (You would now send this prompt to your LLM for response generation)