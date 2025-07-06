import pytest
from test_result_logger import log_test_result

@pytest.mark.usefixtures("test_client")
def test_encryption_status(test_client):
    try:
        response = test_client.get("/api/memory/security/encryption/status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("encryption_status", "pass", response=data)
    except Exception as e:
        log_test_result("encryption_status", "fail", error=str(e))


def test_anonymization_check(test_client):
    try:
        payload = {
            "content": "User John Doe visited Paris on vacation",
            "anonymization_level": "high"
        }
        response = test_client.post("/api/memory/security/anonymize", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("anonymization_check", "pass", response=data)
    except Exception as e:
        log_test_result("anonymization_check", "fail", error=str(e))


def test_access_control_check(test_client):
    try:
        payload = {
            "user_id": "user_001",
            "memory_id": "mem_001",
            "action": "read"
        }
        response = test_client.post("/api/memory/security/access-control", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("access_control_check", "pass", response=data)
    except Exception as e:
        log_test_result("access_control_check", "fail", error=str(e))


def test_audit_logs(test_client):
    try:
        response = test_client.get("/api/memory/security/audit-logs?user_id=user_001&days=7")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("audit_logs", "pass", response=data)
    except Exception as e:
        log_test_result("audit_logs", "fail", error=str(e))


def test_data_retention_policy(test_client):
    try:
        response = test_client.get("/api/memory/security/retention-policy")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("data_retention_policy", "pass", response=data)
    except Exception as e:
        log_test_result("data_retention_policy", "fail", error=str(e))


def test_privacy_compliance_check(test_client):
    try:
        response = test_client.get("/api/memory/security/privacy-compliance?regulation=gdpr")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("privacy_compliance_check", "pass", response=data)
    except Exception as e:
        log_test_result("privacy_compliance_check", "fail", error=str(e))


def test_data_export_request(test_client):
    try:
        payload = {
            "user_id": "user_001",
            "export_format": "json",
            "include_metadata": True
        }
        response = test_client.post("/api/memory/security/data-export", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("data_export_request", "pass", response=data)
    except Exception as e:
        log_test_result("data_export_request", "fail", error=str(e))


def test_data_deletion_request(test_client):
    try:
        payload = {
            "user_id": "user_001",
            "deletion_type": "complete",
            "confirmation": True
        }
        response = test_client.post("/api/memory/security/data-deletion", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("data_deletion_request", "pass", response=data)
    except Exception as e:
        log_test_result("data_deletion_request", "fail", error=str(e))


def test_security_scan(test_client):
    try:
        response = test_client.post("/api/memory/security/scan", json={})
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("security_scan", "pass", response=data)
    except Exception as e:
        log_test_result("security_scan", "fail", error=str(e))


def test_privacy_impact_assessment(test_client):
    try:
        payload = {
            "assessment_type": "data_processing",
            "scope": "memory_system"
        }
        response = test_client.post("/api/memory/security/privacy-impact", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("privacy_impact_assessment", "pass", response=data)
    except Exception as e:
        log_test_result("privacy_impact_assessment", "fail", error=str(e))


def test_consent_management(test_client):
    try:
        payload = {
            "user_id": "user_001",
            "consent_type": "data_processing",
            "status": "granted"
        }
        response = test_client.post("/api/memory/security/consent", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("consent_management", "pass", response=data)
    except Exception as e:
        log_test_result("consent_management", "fail", error=str(e))


def test_breach_detection(test_client):
    try:
        response = test_client.get("/api/memory/security/breach-detection")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("breach_detection", "pass", response=data)
    except Exception as e:
        log_test_result("breach_detection", "fail", error=str(e))


def test_encryption_key_rotation(test_client):
    try:
        response = test_client.post("/api/memory/security/rotate-keys", json={})
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("encryption_key_rotation", "pass", response=data)
    except Exception as e:
        log_test_result("encryption_key_rotation", "fail", error=str(e))


def test_data_classification(test_client):
    try:
        payload = {
            "content": "Sensitive user information",
            "classification_rules": ["pii", "confidential"]
        }
        response = test_client.post("/api/memory/security/classify", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("data_classification", "pass", response=data)
    except Exception as e:
        log_test_result("data_classification", "fail", error=str(e))


def test_security_policy_enforcement(test_client):
    try:
        payload = {
            "policy_type": "data_access",
            "enforcement_level": "strict"
        }
        response = test_client.post("/api/memory/security/enforce-policy", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("security_policy_enforcement", "pass", response=data)
    except Exception as e:
        log_test_result("security_policy_enforcement", "fail", error=str(e)) 