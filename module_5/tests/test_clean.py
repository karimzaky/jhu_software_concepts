"""Verify cleaning and validation using controlled local records."""

import json
import runpy
import sys

import pytest
import clean

pytestmark = pytest.mark.db

URL = "https://www.thegradcafe.com/result/920001"


@pytest.mark.parametrize("value,expected", [
    (None, None),
    (3.8, 3.8),
    (" \n\t ", None),
    (" A&nbsp; &amp;   B ", "A & B"),
])
def test_text_cleaning(value, expected):
    assert clean._clean_text(value) == expected


def test_source_fields_are_preserved():
    original = {
        "url": URL,
        "program": " Original   program ",
        "program_name": " CS &amp; AI ",
        "university": " Original University ",
        "comments": "  Helpful&nbsp; comment  ",
    }
    result = clean.clean_data([original])[0]

    for field in clean.TRACEABILITY_FIELDS:
        assert result[field] == original[field]
    assert result["comments"] == "Helpful comment"
    assert set(clean.EXPECTED_FIELDS) <= set(result)
    assert result["GPA"] is None
    assert original["comments"] == "  Helpful&nbsp; comment  "


@pytest.mark.parametrize("url", [
    None,
    123,
    "http://www.thegradcafe.com/result/1",
    "https://example.com/result/1",
    "https://www.thegradcafe.com/profile/1",
    "https://www.thegradcafe.com/result/abc",
])
def test_invalid_urls_are_rejected(url):
    with pytest.raises(ValueError):
        clean.clean_data([{"url": url}])


def test_non_object_record_is_rejected():
    with pytest.raises(ValueError, match="Record 2"):
        clean.clean_data([{"url": URL}, "invalid record"])


def test_duplicate_url_uses_last_record():
    result = clean.clean_data([
        {"url": URL, "comments": "Earlier"},
        {"url": URL, "comments": "Later"},
    ])
    assert len(result) == 1
    assert result[0]["comments"] == "Later"


@pytest.mark.parametrize("entrypoint", ["function", "script"])
def test_clean_cli_writes_cleaned_json(
    tmp_path, monkeypatch, capsys, entrypoint
):
    source = tmp_path / "input.json"
    destination = tmp_path / "output.json"
    source.write_text(json.dumps([
        {"url": URL, "comments": " Earlier "},
        {"url": URL, "comments": " Updated&nbsp; comment "},
    ]))
    monkeypatch.setattr(sys, "argv", [
        "clean.py", "--input", str(source),
        "--output", str(destination),
    ])

    if entrypoint == "function":
        clean.main()
    else:
        runpy.run_path(clean.__file__, run_name="__main__")

    records = json.loads(destination.read_text())
    assert len(records) == 1
    assert records[0]["comments"] == "Updated comment"
    assert "Duplicates removed: 1" in capsys.readouterr().out
