"""Verify browser adapter behavior with mocked responses and clocks."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import scrape

pytestmark = pytest.mark.db
URL = "https://www.thegradcafe.com/survey"
HTML = '<table><a href="/result/960001">View</a></table>'


@pytest.mark.parametrize("returncode", [0, 1])
def test_chrome_navigation(monkeypatch, returncode):
    run = Mock(return_value=SimpleNamespace(
        returncode=returncode, stderr="Chrome unavailable"
    ))
    monkeypatch.setattr(scrape.subprocess, "run", run)

    if returncode:
        with pytest.raises(RuntimeError, match="navigation failed"):
            scrape._navigate_chrome(URL)
    else:
        scrape._navigate_chrome(URL)

    args, kwargs = run.call_args
    assert args[0][0] == "osascript"
    assert args[0][-1] == URL
    assert kwargs == {
        "capture_output": True, "text": True, "check": False,
    }


@pytest.mark.parametrize("returncode,stdout,error", [
    (0, f" {URL}<<<GRADCAFE_SPLIT>>> {HTML} ", None),
    (1, "", "capture failed"),
    (0, "no separator", "usable page HTML"),
    (0, f"{URL}<<<GRADCAFE_SPLIT>>> ", "usable page HTML"),
])
def test_active_page_capture(monkeypatch, returncode, stdout, error):
    run = Mock(return_value=SimpleNamespace(
        returncode=returncode, stdout=stdout, stderr="capture error"
    ))
    monkeypatch.setattr(scrape.subprocess, "run", run)

    if error:
        with pytest.raises(RuntimeError, match=error):
            scrape._get_active_chrome_page()
    else:
        assert scrape._get_active_chrome_page() == (URL, HTML)


def test_capture_writes_html(tmp_path, monkeypatch):
    monkeypatch.setattr(
        scrape, "_get_active_chrome_page", lambda: (URL, HTML)
    )
    directory = tmp_path / "captures"
    monkeypatch.setattr(scrape, "CAPTURE_DIRECTORY", directory)

    path = scrape.capture_current_page(7)

    assert path == directory / "page_00007.html"
    assert path.read_text() == HTML


@pytest.mark.parametrize("phrase", [
    "Verify you are human",
    "Checking your browser",
    "Performing security verification",
])
def test_verification_pages_are_rejected(tmp_path, monkeypatch, phrase):
    monkeypatch.setattr(
        scrape, "_get_active_chrome_page", lambda: (URL, phrase)
    )
    directory = tmp_path / "captures"
    monkeypatch.setattr(scrape, "CAPTURE_DIRECTORY", directory)
    monkeypatch.setattr(scrape.time, "monotonic", lambda: 0)

    with pytest.raises(RuntimeError, match="verification page"):
        scrape.capture_current_page(1)
    with pytest.raises(RuntimeError, match="verification page"):
        scrape._wait_for_survey_page(URL)
    assert not directory.exists()


def test_wait_requires_new_result_on_expected_page(monkeypatch):
    old_html = '<a href="/result/960000">Old</a>'
    pages = Mock(side_effect=[
        ("https://example.com", ""),
        (URL, old_html),
        (URL, HTML),
    ])
    sleep = Mock()
    monkeypatch.setattr(scrape, "_get_active_chrome_page", pages)
    monkeypatch.setattr(scrape.time, "monotonic", lambda: 0)
    monkeypatch.setattr(scrape.time, "sleep", sleep)

    scrape._wait_for_survey_page(
        URL, previous_first_result="/result/960000"
    )

    assert pages.call_count == 3
    assert sleep.call_count == 2


def test_wait_timeout_uses_mock_clock(monkeypatch):
    clock = Mock(side_effect=[0, 0, 2])
    sleep = Mock()
    monkeypatch.setattr(scrape.time, "monotonic", clock)
    monkeypatch.setattr(scrape.time, "sleep", sleep)
    monkeypatch.setattr(
        scrape, "_get_active_chrome_page", lambda: (URL, "")
    )

    with pytest.raises(TimeoutError, match="did not render"):
        scrape._wait_for_survey_page(URL, timeout_seconds=1)

    sleep.assert_called_once_with(1.0)
