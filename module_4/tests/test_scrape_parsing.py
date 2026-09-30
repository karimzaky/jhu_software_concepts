"""Verify offline scraper parsing, URL validation, and saved state."""

import json
from urllib.parse import parse_qs, urlparse

import pytest
import scrape

pytestmark = pytest.mark.db


def test_survey_cursor_is_encoded():
    assert scrape.build_survey_url() == "https://www.thegradcafe.com/survey"
    url = scrape.build_survey_url("cursor with & symbols")
    assert parse_qs(urlparse(url).query) == {
        "cursor": ["cursor with & symbols"]
    }


@pytest.mark.parametrize("url", [
    "http://www.thegradcafe.com/survey",
    "https://example.com/survey",
    "https://www.thegradcafe.com/signin",
    "https://www.thegradcafe.com/result/1",
])
def test_non_survey_urls_are_rejected(url):
    with pytest.raises(ValueError):
        scrape._validate_public_url(url)


@pytest.mark.parametrize("status,field", [
    ("Accepted on Sep 29", "acceptance_date"),
    ("Rejected on Sep 29", "rejection_date"),
    ("Wait listed on Sep 29", "waitlist_date"),
    ("Interview on Sep 29", "interview_date"),
])
def test_decision_date_extraction(status, field):
    record = {"status": status}
    scrape._add_status_date(record)
    assert record[field] == "Sep 29"


@pytest.mark.parametrize("degree", ["Masters", None])
@pytest.mark.parametrize("has_next", [True, False])
def test_page_parsing(tmp_path, degree, has_next):
    degree_html = f"<span>{degree}</span>" if degree else ""
    next_html = '<a href="/survey?cursor=next">Next</a>' if has_next else ""
    badges = "".join(
        f"<div>{value}</div>"
        for value in [
            "Pending", "Fall 2026", "International",
            "GRE AW 4", "GRE V 155", "GRE 160", "GPA 3.8", "Other",
        ]
    )
    html = f"""
    <table><tbody>
      <tr><td>Ignore this row</td></tr>
      <tr>
        <td>Example University</td>
        <td><span>Computer Science</span>{degree_html}</td>
        <td>Sep 29, 2026</td>
        <td>Pending</td>
        <td><a href="/result/950001">View</a></td>
      </tr>
      <tr><td colspan="5"><div>{badges}</div>
        <p>Helpful comment</p>
      </td></tr>
    </tbody></table>
    {next_html}
    """
    path = tmp_path / "page.html"
    path.write_text(html)

    records, next_url = scrape.parse_captured_page(path)

    assert len(records) == 1
    record = records[0]
    assert record["program"] == "Computer Science, Example University"
    assert record["program_name"] == "Computer Science"
    assert record["university"] == "Example University"
    assert record["Degree"] == degree
    assert record["date_added"] == "Added on Sep 29, 2026"
    assert record["url"] == "https://www.thegradcafe.com/result/950001"
    assert record["comments"] == "Helpful comment"
    assert record["term"] == "Fall 2026"
    assert record["US/International"] == "International"
    for field, expected in {
        "GRE AW": "GRE AW 4", "GRE V": "GRE V 155",
        "GRE": "GRE 160", "GPA": "GPA 3.8",
    }.items():
        assert record[field] == expected
    assert record["acceptance_date"] is None
    expected_next = (
        "https://www.thegradcafe.com/survey?cursor=next"
        if has_next else None
    )
    assert next_url == expected_next


def test_missing_table_is_rejected(tmp_path):
    path = tmp_path / "page.html"
    path.write_text("<html>No results</html>")
    with pytest.raises(ValueError, match="results table"):
        scrape.parse_captured_page(path)


def test_state_round_trip_and_validation(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    monkeypatch.setattr(scrape, "STATE_FILE", path)

    assert scrape._load_state() == (scrape.build_survey_url(), 1)
    next_url = scrape.build_survey_url("next")
    scrape._save_state(next_url, 7)
    assert scrape._load_state() == (next_url, 7)
    assert not path.with_suffix(".tmp").exists()

    path.write_text(json.dumps({"next_url": None}))
    with pytest.raises(ValueError, match="no next URL"):
        scrape._load_state()


def test_first_result_detection():
    assert scrape._first_result_path(
        '<a href="/result/950001">View</a>'
    ) == "/result/950001"
    assert scrape._first_result_path("<p>No results</p>") is None


def test_json_file_validation(tmp_path):
    path = tmp_path / "data.json"
    assert scrape.load_data(path) == []

    scrape.save_data([{"url": "example"}], path)
    assert scrape.load_data(path) == [{"url": "example"}]
    assert not path.with_suffix(".tmp").exists()

    path.write_text("{}")
    with pytest.raises(ValueError, match="JSON list"):
        scrape.load_data(path)
