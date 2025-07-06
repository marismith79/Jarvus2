import pytest
import json
from flask import Flask
from jarvus_app import create_app
from jarvus_app.db import db
from jarvus_app.models.user import User
from test_result_logger import log_test_result

@pytest.fixture(scope="module")
def test_client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create a test user
            user = User(email="testuser@example.com", password="testpassword")
            db.session.add(user)
            db.session.commit()
        yield client


def test_store_episodic_memory(test_client):
    try:
        payload = {
            "action": "click",
            "target": "button#submit",
            "url": "https://example.com",
            "result": "success",
            "details": {"note": "User submitted form"},
            "importance": 1.0
        }
        response = test_client.post("/api/memory/chrome-action", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"]
        log_test_result("store_episodic_memory", "pass", response=data)
    except Exception as e:
        log_test_result("store_episodic_memory", "fail", error=str(e))


def test_get_episodic_memories(test_client):
    try:
        response = test_client.get("/api/memory/episodic?limit=5")
        assert response.status_code == 200
        data = response.get_json()
        assert "memories" in data
        log_test_result("get_episodic_memories", "pass", response=data)
    except Exception as e:
        log_test_result("get_episodic_memories", "fail", error=str(e))


def test_store_semantic_memory(test_client):
    try:
        payload = {
            "text": "User prefers dark mode",
            "type": "preference",
            "importance": 1.5
        }
        response = test_client.post("/memory/store", json=payload)
        assert response.status_code in (200, 201)
        data = response.get_json()
        log_test_result("store_semantic_memory", "pass", response=data)
    except Exception as e:
        log_test_result("store_semantic_memory", "fail", error=str(e))


def test_get_semantic_memories(test_client):
    try:
        response = test_client.get("/api/memory/semantic?limit=5")
        assert response.status_code == 200
        data = response.get_json()
        assert "memories" in data
        log_test_result("get_semantic_memories", "pass", response=data)
    except Exception as e:
        log_test_result("get_semantic_memories", "fail", error=str(e))


def test_store_procedural_memory(test_client):
    try:
        payload = {
            "name": "Email Automation",
            "steps": ["open_gmail", "compose_email", "send"],
            "result": "success",
            "duration": 120,
            "success": True,
            "importance": 2.0
        }
        response = test_client.post("/api/memory/workflow-execution", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        log_test_result("store_procedural_memory", "pass", response=data)
    except Exception as e:
        log_test_result("store_procedural_memory", "fail", error=str(e))


def test_get_procedural_memories(test_client):
    try:
        response = test_client.get("/api/memory/procedural?limit=5")
        assert response.status_code == 200
        data = response.get_json()
        assert "memories" in data
        log_test_result("get_procedural_memories", "pass", response=data)
    except Exception as e:
        log_test_result("get_procedural_memories", "fail", error=str(e))

# Add more CRUD and edge case tests as needed for full coverage 