import pytest
from test_result_logger import log_test_result

@pytest.mark.usefixtures("test_client")
def test_bulk_create_memories(test_client):
    try:
        payload = {
            "memories": [
                {
                    "content": "Memory 1 content",
                    "memory_type": "episodic",
                    "namespace": "test",
                    "tags": ["test", "bulk"]
                },
                {
                    "content": "Memory 2 content",
                    "memory_type": "semantic",
                    "namespace": "test",
                    "tags": ["test", "bulk"]
                }
            ]
        }
        response = test_client.post("/api/memory/bulk/create", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"]
        log_test_result("bulk_create_memories", "pass", response=data)
    except Exception as e:
        log_test_result("bulk_create_memories", "fail", error=str(e))


def test_bulk_update_memories(test_client):
    try:
        payload = {
            "updates": [
                {
                    "memory_id": "mem_001",
                    "updates": {"tags": ["updated", "bulk"]}
                },
                {
                    "memory_id": "mem_002",
                    "updates": {"tags": ["updated", "bulk"]}
                }
            ]
        }
        response = test_client.put("/api/memory/bulk/update", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("bulk_update_memories", "pass", response=data)
    except Exception as e:
        log_test_result("bulk_update_memories", "fail", error=str(e))


def test_bulk_delete_memories(test_client):
    try:
        payload = {
            "memory_ids": ["mem_001", "mem_002", "mem_003"]
        }
        response = test_client.delete("/api/memory/bulk/delete", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("bulk_delete_memories", "pass", response=data)
    except Exception as e:
        log_test_result("bulk_delete_memories", "fail", error=str(e))


def test_bulk_export_memories(test_client):
    try:
        payload = {
            "memory_ids": ["mem_001", "mem_002"],
            "format": "json",
            "include_metadata": True
        }
        response = test_client.post("/api/memory/bulk/export", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("bulk_export_memories", "pass", response=data)
    except Exception as e:
        log_test_result("bulk_export_memories", "fail", error=str(e))


def test_bulk_import_memories(test_client):
    try:
        payload = {
            "memories": [
                {
                    "content": "Imported memory 1",
                    "memory_type": "episodic",
                    "namespace": "imported"
                },
                {
                    "content": "Imported memory 2",
                    "memory_type": "semantic",
                    "namespace": "imported"
                }
            ],
            "conflict_resolution": "skip"
        }
        response = test_client.post("/api/memory/bulk/import", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"]
        log_test_result("bulk_import_memories", "pass", response=data)
    except Exception as e:
        log_test_result("bulk_import_memories", "fail", error=str(e))


def test_bulk_search_memories(test_client):
    try:
        payload = {
            "queries": [
                {"query": "test memory", "namespace": "test"},
                {"query": "imported content", "namespace": "imported"}
            ],
            "limit_per_query": 10
        }
        response = test_client.post("/api/memory/bulk/search", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("bulk_search_memories", "pass", response=data)
    except Exception as e:
        log_test_result("bulk_search_memories", "fail", error=str(e))


def test_bulk_tag_memories(test_client):
    try:
        payload = {
            "memory_ids": ["mem_001", "mem_002"],
            "tags": ["bulk_tagged", "test"],
            "operation": "add"
        }
        response = test_client.post("/api/memory/bulk/tag", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("bulk_tag_memories", "pass", response=data)
    except Exception as e:
        log_test_result("bulk_tag_memories", "fail", error=str(e))


def test_bulk_analyze_memories(test_client):
    try:
        payload = {
            "memory_ids": ["mem_001", "mem_002", "mem_003"],
            "analysis_types": ["quality", "similarity", "conflicts"]
        }
        response = test_client.post("/api/memory/bulk/analyze", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("bulk_analyze_memories", "pass", response=data)
    except Exception as e:
        log_test_result("bulk_analyze_memories", "fail", error=str(e))


def test_bulk_validate_memories(test_client):
    try:
        payload = {
            "memory_ids": ["mem_001", "mem_002"],
            "validation_rules": ["content_length", "required_fields", "format"]
        }
        response = test_client.post("/api/memory/bulk/validate", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("bulk_validate_memories", "pass", response=data)
    except Exception as e:
        log_test_result("bulk_validate_memories", "fail", error=str(e))


def test_bulk_cleanup_memories(test_client):
    try:
        payload = {
            "criteria": {
                "older_than_days": 30,
                "namespace": "test",
                "memory_types": ["episodic"]
            }
        }
        response = test_client.post("/api/memory/bulk/cleanup", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("bulk_cleanup_memories", "pass", response=data)
    except Exception as e:
        log_test_result("bulk_cleanup_memories", "fail", error=str(e)) 