"""Verify loader configuration, parsing, and file input."""

import json
from datetime import date
from unittest.mock import Mock

import psycopg
import pytest

import load_data
import scrape_manager

pytestmark = pytest.mark.db


@pytest.mark.parametrize("password", ["", "test-only-password"])
def test_connection_uses_db_settings_without_url(monkeypatch, password):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = {
        "DB_NAME": "example_test",
        "DB_USER": "test_user",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_PASSWORD": password,
    }
    for name, value in settings.items():
        monkeypatch.setenv(name, value)

    connect = Mock()
    monkeypatch.setattr(load_data.psycopg, "connect", connect)
    assert load_data.get_connection() is connect.return_value

    expected = {
        "dbname": "example_test",
        "user": "test_user",
        "host": "localhost",
        "port": "5432",
    }
    if password:
        expected["password"] = password
    connect.assert_called_once_with(**expected)


@pytest.mark.parametrize("value,expected", [
    (None, None),
    ("invalid date", None),
    ("Added on Sep 29, 2026", date(2026, 9, 29)),
    ("Sep 29, 2026", date(2026, 9, 29)),
])
def test_date_parsing(value, expected):
    assert load_data.parse_date(value) == expected


@pytest.mark.parametrize("value,expected", [
    (None, None),
    ("not reported", None),
    ("GPA 3.8", 3.8),
    ("GPA 9.0", None),
])
def test_bounded_number_parsing(value, expected):
    assert load_data.parse_bounded_number(value, 0, 4.33) == expected


def test_loader_rejects_non_list():
    with pytest.raises(ValueError, match="list of records"):
        load_data.load_records(records={})


def test_loader_reads_json_and_skips_missing_urls(
    postgres_db, tmp_path, monkeypatch
):
    source = tmp_path / "applicants.json"
    source.write_text(json.dumps([
        {"url": "https://www.thegradcafe.com/result/930001"},
        {"url": None},
        {"url": "   "},
    ]))
    monkeypatch.setattr(load_data, "DATA_FILE", source)

    assert load_data.load_records() == 1

    with psycopg.connect(postgres_db) as connection:
        urls = connection.execute("SELECT url FROM applicants").fetchall()
    assert urls == [("https://www.thegradcafe.com/result/930001",)]


def test_worker_database_count_uses_real_postgres(postgres_db):
    load_data.load_records(records=[
        {"url": "https://www.thegradcafe.com/result/930002"},
        {"url": "https://www.thegradcafe.com/result/930003"},
    ])
    assert scrape_manager._database_record_count() == 2
