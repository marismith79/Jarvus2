import pytest
from test_result_logger import log_test_result

@pytest.mark.usefixtures("test_client")
def test_efficient_hybrid_search(test_client):
    try:
        payload = {
            "query": "email automation workflow",
            "user_id": 1,
            "namespace": "episodes",
            "n_results": 5,
            "similarity_threshold": 0.7
        }
        response = test_client.post("/api/memory/vector/efficient-search", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("efficient_hybrid_search", "pass", response=data)
    except Exception as e:
        log_test_result("efficient_hybrid_search", "fail", error=str(e))


def test_vector_content_update_and_delete(test_client):
    try:
        # Assume a memory exists with user_id=1, memory_id='mem_001'
        update_payload = {
            "user_id": 1,
            "namespace": "episodes",
            "memory_id": "mem_001",
            "new_content": "Updated memory content for testing."
        }
        response = test_client.post("/api/memory/vector/update-content", json=update_payload)
        assert response.status_code == 200
        data = response.get_json()
        log_test_result("vector_content_update", "pass", response=data)

        delete_payload = {
            "user_id": 1,
            "memory_id": "mem_001"
        }
        response = test_client.delete("/api/memory/vector/delete-content", json=delete_payload)
        assert response.status_code == 200
        data = response.get_json()
        log_test_result("vector_content_delete", "pass", response=data)
    except Exception as e:
        log_test_result("vector_content_update_and_delete", "fail", error=str(e))


def test_vector_status_endpoint(test_client):
    try:
        response = test_client.get("/api/memory/vector/status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("vector_status_endpoint", "pass", response=data)
    except Exception as e:
        log_test_result("vector_status_endpoint", "fail", error=str(e)) 