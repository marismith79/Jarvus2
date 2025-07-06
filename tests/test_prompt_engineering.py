import pytest
from test_result_logger import log_test_result

@pytest.mark.usefixtures("test_client")
def test_prompt_templates(test_client):
    try:
        response = test_client.get("/api/memory/prompts/templates")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("prompt_templates", "pass", response=data)
    except Exception as e:
        log_test_result("prompt_templates", "fail", error=str(e))


def test_context_injection(test_client):
    try:
        payload = {
            "query": "What should I do for vacation?",
            "context_types": ["episodic", "semantic"],
            "max_context_length": 1000
        }
        response = test_client.post("/api/memory/prompts/inject-context", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("context_injection", "pass", response=data)
    except Exception as e:
        log_test_result("context_injection", "fail", error=str(e))


def test_memory_selection(test_client):
    try:
        payload = {
            "query": "vacation planning",
            "selection_strategy": "relevance",
            "max_memories": 5
        }
        response = test_client.post("/api/memory/prompts/select-memories", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("memory_selection", "pass", response=data)
    except Exception as e:
        log_test_result("memory_selection", "fail", error=str(e))


def test_prompt_optimization(test_client):
    try:
        payload = {
            "original_prompt": "Tell me about vacations",
            "optimization_goals": ["clarity", "specificity", "context_relevance"]
        }
        response = test_client.post("/api/memory/prompts/optimize", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("prompt_optimization", "pass", response=data)
    except Exception as e:
        log_test_result("prompt_optimization", "fail", error=str(e))


def test_prompt_evaluation(test_client):
    try:
        payload = {
            "prompt": "What should I do for vacation?",
            "evaluation_metrics": ["clarity", "specificity", "context_relevance"]
        }
        response = test_client.post("/api/memory/prompts/evaluate", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("prompt_evaluation", "pass", response=data)
    except Exception as e:
        log_test_result("prompt_evaluation", "fail", error=str(e))


def test_dynamic_prompt_generation(test_client):
    try:
        payload = {
            "task_type": "vacation_planning",
            "user_context": "I like beaches and hiking",
            "memory_context": "episodic"
        }
        response = test_client.post("/api/memory/prompts/generate", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("dynamic_prompt_generation", "pass", response=data)
    except Exception as e:
        log_test_result("dynamic_prompt_generation", "fail", error=str(e))


def test_prompt_chain_creation(test_client):
    try:
        payload = {
            "chain_name": "vacation_planning_chain",
            "steps": [
                {"type": "context_gathering", "prompt_template": "gather_vacation_context"},
                {"type": "memory_retrieval", "prompt_template": "retrieve_vacation_memories"},
                {"type": "recommendation", "prompt_template": "generate_vacation_recommendations"}
            ]
        }
        response = test_client.post("/api/memory/prompts/create-chain", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"]
        log_test_result("prompt_chain_creation", "pass", response=data)
    except Exception as e:
        log_test_result("prompt_chain_creation", "fail", error=str(e))


def test_prompt_chain_execution(test_client):
    try:
        payload = {
            "chain_id": "chain_001",
            "input": "I want to plan a vacation"
        }
        response = test_client.post("/api/memory/prompts/execute-chain", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("prompt_chain_execution", "pass", response=data)
    except Exception as e:
        log_test_result("prompt_chain_execution", "fail", error=str(e))


def test_prompt_performance_metrics(test_client):
    try:
        response = test_client.get("/api/memory/prompts/performance?chain_id=chain_001&days=30")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("prompt_performance_metrics", "pass", response=data)
    except Exception as e:
        log_test_result("prompt_performance_metrics", "fail", error=str(e))


def test_prompt_ab_testing(test_client):
    try:
        payload = {
            "prompt_a": "What should I do for vacation?",
            "prompt_b": "Based on your preferences, what vacation would you enjoy?",
            "test_duration_days": 7,
            "success_metric": "user_satisfaction"
        }
        response = test_client.post("/api/memory/prompts/ab-test", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"]
        log_test_result("prompt_ab_testing", "pass", response=data)
    except Exception as e:
        log_test_result("prompt_ab_testing", "fail", error=str(e))


def test_prompt_feedback_collection(test_client):
    try:
        payload = {
            "prompt_id": "prompt_001",
            "user_feedback": "very helpful",
            "rating": 5,
            "context": "vacation_planning"
        }
        response = test_client.post("/api/memory/prompts/feedback", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("prompt_feedback_collection", "pass", response=data)
    except Exception as e:
        log_test_result("prompt_feedback_collection", "fail", error=str(e))


def test_prompt_learning_loop(test_client):
    try:
        payload = {
            "prompt_id": "prompt_001",
            "learning_type": "reinforcement",
            "performance_data": {"accuracy": 0.85, "user_satisfaction": 4.2}
        }
        response = test_client.post("/api/memory/prompts/learn", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("prompt_learning_loop", "pass", response=data)
    except Exception as e:
        log_test_result("prompt_learning_loop", "fail", error=str(e)) 