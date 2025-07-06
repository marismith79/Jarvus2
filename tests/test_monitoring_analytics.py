import pytest
from test_result_logger import log_test_result

@pytest.mark.usefixtures("test_client")
def test_performance_metrics(test_client):
    try:
        response = test_client.get("/api/memory/monitoring/performance?namespace=episodes&days=7")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("performance_metrics", "pass", response=data)
    except Exception as e:
        log_test_result("performance_metrics", "fail", error=str(e))


def test_usage_stats(test_client):
    try:
        response = test_client.get("/api/memory/monitoring/usage?namespace=episodes&period=weekly")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("usage_stats", "pass", response=data)
    except Exception as e:
        log_test_result("usage_stats", "fail", error=str(e))


def test_error_tracking(test_client):
    try:
        response = test_client.get("/api/memory/monitoring/errors?severity=high&days=7")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("error_tracking", "pass", response=data)
    except Exception as e:
        log_test_result("error_tracking", "fail", error=str(e))


def test_health_checks(test_client):
    try:
        response = test_client.get("/api/memory/monitoring/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("health_checks", "pass", response=data)
    except Exception as e:
        log_test_result("health_checks", "fail", error=str(e))


def test_analytics_dashboard(test_client):
    try:
        response = test_client.get("/api/memory/analytics/dashboard?namespace=episodes")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("analytics_dashboard", "pass", response=data)
    except Exception as e:
        log_test_result("analytics_dashboard", "fail", error=str(e))


def test_alerting_configuration(test_client):
    try:
        payload = {
            "alert_type": "performance_degradation",
            "threshold": 0.8,
            "notification_channels": ["email", "slack"]
        }
        response = test_client.post("/api/memory/monitoring/alerts/configure", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("alerting_configuration", "pass", response=data)
    except Exception as e:
        log_test_result("alerting_configuration", "fail", error=str(e))


def test_system_metrics(test_client):
    try:
        response = test_client.get("/api/memory/monitoring/system-metrics")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("system_metrics", "pass", response=data)
    except Exception as e:
        log_test_result("system_metrics", "fail", error=str(e))


def test_user_activity_analytics(test_client):
    try:
        response = test_client.get("/api/memory/analytics/user-activity?user_id=user_001&days=30")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("user_activity_analytics", "pass", response=data)
    except Exception as e:
        log_test_result("user_activity_analytics", "fail", error=str(e))


def test_memory_growth_analytics(test_client):
    try:
        response = test_client.get("/api/memory/analytics/growth?namespace=episodes&period=monthly")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("memory_growth_analytics", "pass", response=data)
    except Exception as e:
        log_test_result("memory_growth_analytics", "fail", error=str(e))


def test_quality_trends_analytics(test_client):
    try:
        response = test_client.get("/api/memory/analytics/quality-trends?namespace=episodes&days=90")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("quality_trends_analytics", "pass", response=data)
    except Exception as e:
        log_test_result("quality_trends_analytics", "fail", error=str(e))


def test_search_effectiveness_analytics(test_client):
    try:
        response = test_client.get("/api/memory/analytics/search-effectiveness?namespace=episodes")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("search_effectiveness_analytics", "pass", response=data)
    except Exception as e:
        log_test_result("search_effectiveness_analytics", "fail", error=str(e))


def test_cost_analytics(test_client):
    try:
        response = test_client.get("/api/memory/analytics/costs?namespace=episodes&period=monthly")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("cost_analytics", "pass", response=data)
    except Exception as e:
        log_test_result("cost_analytics", "fail", error=str(e))


def test_alert_history(test_client):
    try:
        response = test_client.get("/api/memory/monitoring/alerts/history?days=30")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("alert_history", "pass", response=data)
    except Exception as e:
        log_test_result("alert_history", "fail", error=str(e))


def test_performance_baseline(test_client):
    try:
        response = test_client.get("/api/memory/monitoring/performance-baseline?namespace=episodes")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("performance_baseline", "pass", response=data)
    except Exception as e:
        log_test_result("performance_baseline", "fail", error=str(e))


def test_capacity_planning_analytics(test_client):
    try:
        response = test_client.get("/api/memory/analytics/capacity-planning?namespace=episodes&forecast_days=90")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"]
        log_test_result("capacity_planning_analytics", "pass", response=data)
    except Exception as e:
        log_test_result("capacity_planning_analytics", "fail", error=str(e)) 