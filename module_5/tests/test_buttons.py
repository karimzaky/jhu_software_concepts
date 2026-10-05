"""Verify button responses and busy-state gating."""

import pytest

from app import create_app

pytestmark = pytest.mark.buttons


@pytest.fixture
def button_system():
    """Provide a test client with observable fake services."""
    state = {"running": False}
    calls = {"pull": 0, "query": 0}

    def fake_pull():
        calls["pull"] += 1
        return True

    def fake_query():
        calls["query"] += 1
        return {}

    application = create_app({
        "TESTING": True,
        "GET_STATUS_FN": lambda: dict(state),
        "START_PULL_FN": fake_pull,
        "QUERY_RESULTS_FN": fake_query,
    })
    return application.test_client(), state, calls


def test_idle_pull_starts_service(button_system):
    client, _, calls = button_system

    response = client.post("/pull-data")

    assert response.status_code == 202
    assert response.get_json() == {"ok": True}
    assert calls == {"pull": 1, "query": 0}


def test_idle_update_queries_analysis(button_system):
    client, _, calls = button_system

    response = client.post("/update-analysis")

    assert response.status_code == 200
    assert response.get_json() == {"ok": True}
    assert calls == {"pull": 0, "query": 1}


@pytest.mark.parametrize("route", ["/pull-data", "/update-analysis"])
def test_busy_request_performs_no_work(button_system, route):
    client, state, calls = button_system
    state["running"] = True

    response = client.post(route)

    assert response.status_code == 409
    assert response.get_json() == {"busy": True}
    assert calls == {"pull": 0, "query": 0}
