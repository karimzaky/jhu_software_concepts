"""Verify scrape orchestration without browser calls or real waits."""

import runpy
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
import scrape

pytestmark = pytest.mark.db
URL = "https://www.thegradcafe.com/survey"
NEXT = URL + "?cursor=next"


@pytest.fixture
def flow(monkeypatch):
    services = {
        "load_data": Mock(return_value=[]),
        "_load_state": Mock(return_value=(URL, 7)),
        "_get_active_chrome_page": Mock(return_value=(
            URL, '<a href="/result/1">View</a>'
        )),
        "_navigate_chrome": Mock(),
        "_wait_for_survey_page": Mock(),
        "capture_current_page": Mock(return_value=Path("fake.html")),
        "parse_captured_page": Mock(return_value=(
            [{"url": "one"}], None
        )),
        "save_data": Mock(),
        "_save_state": Mock(),
    }
    for name, service in services.items():
        monkeypatch.setattr(scrape, name, service)
    services["sleep"] = Mock()
    monkeypatch.setattr(scrape.time, "sleep", services["sleep"])
    return services


def test_existing_target_needs_no_capture(flow):
    flow["load_data"].return_value = [{"url": "one"}, {"url": None}]
    assert scrape.scrape_data(target_records=1) == [{"url": "one"}]
    flow["_get_active_chrome_page"].assert_not_called()


def test_zero_page_limit_needs_no_capture(flow):
    assert scrape.scrape_data(target_records=10, max_pages=0) == []
    flow["capture_current_page"].assert_not_called()


def test_target_reached_saves_records_and_cursor(flow):
    flow["parse_captured_page"].return_value = (
        [{"url": "one"}, {"url": "two"}], NEXT
    )
    records = scrape.scrape_data(target_records=2)
    assert len(records) == 2
    flow["save_data"].assert_called_once_with(records)
    flow["_save_state"].assert_called_once_with(NEXT, 8)
    flow["sleep"].assert_not_called()


def test_missing_next_link_finishes_collection(flow):
    assert scrape.scrape_data(target_records=10) == [{"url": "one"}]
    flow["_save_state"].assert_called_once_with(None, 8)
    flow["sleep"].assert_not_called()


def test_overlapping_pages_resume_and_obey_page_limit(flow):
    flow["_get_active_chrome_page"].return_value = (
        URL + "?cursor=old", '<a href="/result/1">Old</a>'
    )
    final_url = URL + "?cursor=final"
    flow["parse_captured_page"].side_effect = [
        ([{"url": "one", "comments": "Earlier"}], NEXT),
        ([
            {"url": "one", "comments": "Updated"},
            {"url": "two"},
        ], final_url),
    ]

    records = scrape.scrape_data(target_records=10, max_pages=2)

    assert records == [
        {"url": "one", "comments": "Updated"}, {"url": "two"}
    ]
    assert flow["capture_current_page"].call_args_list == [
        ((7,), {}), ((8,), {})
    ]
    assert flow["_navigate_chrome"].call_count == 2
    flow["_wait_for_survey_page"].assert_any_call(
        NEXT, previous_first_result="/result/1"
    )
    flow["_save_state"].assert_called_with(final_url, 9)
    assert flow["sleep"].call_count == 2


def test_empty_parsed_page_is_rejected(flow):
    flow["parse_captured_page"].return_value = ([], NEXT)
    with pytest.raises(RuntimeError, match="No applicant records"):
        scrape.scrape_data(target_records=10)
    flow["save_data"].assert_not_called()


def test_repeated_next_url_is_rejected(flow):
    flow["parse_captured_page"].return_value = ([{"url": "one"}], URL)
    with pytest.raises(RuntimeError, match="did not advance"):
        scrape.scrape_data(target_records=10)
    flow["_save_state"].assert_not_called()


def test_cli_zero_target_does_not_access_browser(monkeypatch, capsys):
    original_exists = Path.exists

    def controlled_exists(path):
        if path in (scrape.OUTPUT_FILE, scrape.STATE_FILE):
            return False
        return original_exists(path)

    monkeypatch.setattr(Path, "exists", controlled_exists)
    browser = Mock(side_effect=AssertionError("Unexpected browser call"))
    monkeypatch.setattr(scrape.subprocess, "run", browser)
    monkeypatch.setattr(sys, "argv", [
        "scrape.py", "--target-records", "0", "--max-pages", "0",
    ])

    namespace = runpy.run_path(scrape.__file__, run_name="__main__")

    assert namespace["arguments"].target_records == 0
    assert namespace["arguments"].max_pages == 0
    assert "Starting with 0 saved records" in capsys.readouterr().out
    browser.assert_not_called()
