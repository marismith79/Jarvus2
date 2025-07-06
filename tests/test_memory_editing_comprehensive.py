import pytest
from test_result_logger import log_test_result

@pytest.mark.usefixtures("test_client")
def test_find_mergeable_memories(test_client):
    try:
        response = test_client.get("/api/memory/find-mergeable?namespace=episodes&similarity=0.85")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("find_mergeable_memories", "pass", response=data)
    except Exception as e:
        log_test_result("find_mergeable_memories", "fail", error=str(e))


def test_merge_memories(test_client):
    try:
        payload = {
            "memory_ids": ["mem_001", "mem_002", "mem_003"],
            "merge_type": "episodic"
        }
        response = test_client.post("/api/memory/merge", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"]
        log_test_result("merge_memories", "pass", response=data)
    except Exception as e:
        log_test_result("merge_memories", "fail", error=str(e))


def test_improve_memory(test_client):
    try:
        payload = {
            "improvement_type": "procedural"
        }
        response = test_client.post("/api/memory/improve/mem_001", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("improve_memory", "pass", response=data)
    except Exception as e:
        log_test_result("improve_memory", "fail", error=str(e))


def test_assess_memory_quality(test_client):
    try:
        response = test_client.get("/api/memory/assess-quality/mem_001")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("assess_memory_quality", "pass", response=data)
    except Exception as e:
        log_test_result("assess_memory_quality", "fail", error=str(e))


def test_quality_report(test_client):
    try:
        response = test_client.get("/api/memory/quality-report?namespace=episodes&limit=50")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("quality_report", "pass", response=data)
    except Exception as e:
        log_test_result("quality_report", "fail", error=str(e))


def test_detect_conflicts(test_client):
    try:
        response = test_client.get("/api/memory/detect-conflicts?namespace=episodes")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("detect_conflicts", "pass", response=data)
    except Exception as e:
        log_test_result("detect_conflicts", "fail", error=str(e))


def test_resolve_conflicts(test_client):
    try:
        payload = {
            "conflicts": [
                {
                    "memory1_id": "mem_001",
                    "memory2_id": "mem_002",
                    "conflict_type": "data_conflict",
                    "severity": "medium"
                }
            ]
        }
        response = test_client.post("/api/memory/resolve-conflicts", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("resolve_conflicts", "pass", response=data)
    except Exception as e:
        log_test_result("resolve_conflicts", "fail", error=str(e))


def test_memory_evolution(test_client):
    try:
        response = test_client.get("/api/memory/evolution/mem_001")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("memory_evolution", "pass", response=data)
    except Exception as e:
        log_test_result("memory_evolution", "fail", error=str(e))


def test_bulk_improve(test_client):
    try:
        payload = {
            "memory_ids": ["mem_001", "mem_002", "mem_003"],
            "improvement_type": "auto"
        }
        response = test_client.post("/api/memory/bulk-improve", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("bulk_improve", "pass", response=data)
    except Exception as e:
        log_test_result("bulk_improve", "fail", error=str(e))


def test_auto_consolidate(test_client):
    try:
        response = test_client.post("/api/memory/auto-consolidate?namespace=episodes&similarity=0.85", json={})
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("auto_consolidate", "pass", response=data)
    except Exception as e:
        log_test_result("auto_consolidate", "fail", error=str(e)) 