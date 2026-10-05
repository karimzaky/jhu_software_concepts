"""Test route errors and worker state without Chrome or real threads."""

import json
import threading
from unittest.mock import Mock

import pytest
import scrape_manager

pytestmark = pytest.mark.buttons


def fail_service():
    raise RuntimeError("controlled service failure")


@pytest.mark.parametrize(
    "method,route",
    [("get", "/analysis"), ("post", "/update-analysis")],
)
def test_query_failure_returns_500(application, method, route):
    application.config["QUERY_RESULTS_FN"] = fail_service
    response = getattr(application.test_client(), method)(route)
    assert response.status_code == 500
    if method == "post":
        assert response.get_json() == {"ok": False}
    else:
        assert b"Analysis unavailable" in response.data


def test_pull_service_rejects_racing_request(application):
    start = Mock(return_value=False)
    application.config["START_PULL_FN"] = start
    response = application.test_client().post("/pull-data")
    assert response.status_code == 409
    assert response.get_json() == {"busy": True}
    start.assert_called_once_with()


@pytest.fixture
def manager(monkeypatch):
    monkeypatch.setattr(scrape_manager, "SCRAPE_LOCK", threading.Lock())
    monkeypatch.setattr(scrape_manager, "STATUS_LOCK", threading.Lock())
    monkeypatch.setattr(scrape_manager, "_scrape_status", {
        "running": False,
        "message": "Idle",
        "last_added": None,
        "last_finished": None,
        "error": None,
    })
    monkeypatch.setattr(
        scrape_manager, "_json_record_count", Mock(return_value=2)
    )
    monkeypatch.setattr(
        scrape_manager, "_database_record_count",
        Mock(side_effect=[2, 3]),
    )
    monkeypatch.setattr(
        scrape_manager, "scrape_data", Mock(return_value=[{}, {}, {}])
    )
    monkeypatch.setattr(
        scrape_manager, "load_records", Mock(return_value=1)
    )
    return scrape_manager


def test_status_is_a_copy(manager):
    snapshot = manager.get_scrape_status()
    snapshot["running"] = True
    assert manager.get_scrape_status()["running"] is False


def test_worker_success_releases_lock(manager):
    manager.SCRAPE_LOCK.acquire()
    manager._pull_data_worker()
    status = manager.get_scrape_status()
    assert status["running"] is False
    assert status["error"] is None
    assert status["last_added"] == 1
    assert status["last_finished"] is not None
    assert not manager.SCRAPE_LOCK.locked()
    manager.scrape_data.assert_called_once_with(
        target_records=22, max_pages=1
    )
    manager.load_records.assert_called_once()


@pytest.mark.parametrize("dependency", ["scrape_data", "load_records"])
def test_worker_failure_clears_busy_and_releases_lock(manager, dependency):
    getattr(manager, dependency).side_effect = RuntimeError(
        "controlled worker failure"
    )
    manager.SCRAPE_LOCK.acquire()
    manager._pull_data_worker()
    status = manager.get_scrape_status()
    assert status["running"] is False
    assert status["error"] == "controlled worker failure"
    assert status["last_added"] == 0
    assert not manager.SCRAPE_LOCK.locked()
    if dependency == "scrape_data":
        manager.load_records.assert_not_called()


def test_worker_accepts_duplicate_records(manager):
    manager._database_record_count.side_effect = [2, 2]
    manager.load_records.return_value = 0
    manager.SCRAPE_LOCK.acquire()
    manager._pull_data_worker()
    status = manager.get_scrape_status()
    assert status["error"] is None
    assert status["last_added"] == 0
    assert not manager.SCRAPE_LOCK.locked()


def test_busy_manager_does_not_create_thread(manager, monkeypatch):
    thread = Mock()
    monkeypatch.setattr(manager.threading, "Thread", thread)
    manager.SCRAPE_LOCK.acquire()
    assert manager.start_data_pull() is False
    thread.assert_not_called()
    manager.SCRAPE_LOCK.release()


def test_thread_launch_failure_releases_lock(manager, monkeypatch):
    thread = Mock()
    thread.return_value.start.side_effect = RuntimeError(
        "thread launch failed"
    )
    monkeypatch.setattr(manager.threading, "Thread", thread)
    with pytest.raises(RuntimeError, match="thread launch failed"):
        manager.start_data_pull()
    assert not manager.SCRAPE_LOCK.locked()
    assert manager.get_scrape_status()["running"] is False


def test_thread_is_started_with_worker_target(manager, monkeypatch):
    thread = Mock()
    monkeypatch.setattr(manager.threading, "Thread", thread)
    assert manager.start_data_pull() is True
    thread.assert_called_once_with(
        target=manager._pull_data_worker,
        name="gradcafe-data-pull",
        daemon=True,
    )
    thread.return_value.start.assert_called_once_with()
    assert manager.get_scrape_status()["running"] is True
    manager.SCRAPE_LOCK.release()


@pytest.mark.parametrize("payload,expected", [([{}, {}], 2), ({}, None)])
def test_json_record_count_validation(
    tmp_path, monkeypatch, payload, expected
):
    path = tmp_path / "applicants.json"
    path.write_text(json.dumps(payload))
    monkeypatch.setattr(scrape_manager, "DATA_FILE", path)
    if expected is None:
        with pytest.raises(ValueError, match="JSON list"):
            scrape_manager._json_record_count()
    else:
        assert scrape_manager._json_record_count() == expected
