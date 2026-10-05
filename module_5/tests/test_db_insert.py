"""Verify that pull requests write applicant records to PostgreSQL."""

import psycopg
import pytest

from app import create_app
from load_data import load_records

pytestmark = pytest.mark.db


def test_pull_inserts_scraper_rows(postgres_db):
    records = [
        {
            "program": "Computer Science, Johns Hopkins University",
            "url": "https://www.thegradcafe.com/result/900001",
            "status": "Accepted",
            "term": "Fall 2026",
            "date_added": "Sep 29, 2026",
            "US/International": "American",
            "Degree": "Masters",
            "GPA": "3.8",
        },
        {
            "program": "Computer Science, Example University",
            "url": "https://www.thegradcafe.com/result/900002",
            "status": "Rejected",
            "term": "Fall 2026",
            "date_added": "Sep 29, 2026",
            "US/International": "International",
            "Degree": "PhD",
            "GPA": "3.6",
        },
    ]

    def fake_scraper():
        return records

    def start_test_pull():
        load_records(records=fake_scraper())
        return True

    application = create_app({
        "TESTING": True,
        "GET_STATUS_FN": lambda: {"running": False},
        "START_PULL_FN": start_test_pull,
    })

    with psycopg.connect(postgres_db) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM applicants"
        ).fetchone()[0] == 0

    response = application.test_client().post("/pull-data")
    assert response.status_code == 202
    assert response.get_json() == {"ok": True}

    with psycopg.connect(postgres_db) as connection:
        rows = connection.execute(
            "SELECT program, url, status, term, date_added "
            "FROM applicants ORDER BY url"
        ).fetchall()

    assert len(rows) == 2
    assert [row[1] for row in rows] == [record["url"] for record in records]
    assert all(value is not None for row in rows for value in row)


def test_duplicate_pulls_do_not_duplicate_rows(postgres_db):
    records = [
        {"url": "https://www.thegradcafe.com/result/900003"},
        {"url": "https://www.thegradcafe.com/result/900004"},
    ]
    inserted_counts = []

    def start_test_pull():
        inserted_counts.append(load_records(records=records))
        return True

    application = create_app({
        "TESTING": True,
        "GET_STATUS_FN": lambda: {"running": False},
        "START_PULL_FN": start_test_pull,
    })
    client = application.test_client()

    for _ in range(2):
        response = client.post("/pull-data")
        assert response.status_code == 202
        assert response.get_json() == {"ok": True}

    with psycopg.connect(postgres_db) as connection:
        total, unique = connection.execute(
            "SELECT COUNT(*), COUNT(DISTINCT url) FROM applicants"
        ).fetchone()

    assert inserted_counts == [2, 0]
    assert total == unique == 2


def test_failed_insert_rolls_back_entire_batch(postgres_db, monkeypatch):
    import load_data

    original_prepare = load_data.prepare_record

    def prepare_with_invalid_second_row(record):
        values = list(original_prepare(record))
        if record.get("break_insert"):
            values[3] = None  # URL is NOT NULL in the existing schema.
        return tuple(values)

    monkeypatch.setattr(
        load_data, "prepare_record", prepare_with_invalid_second_row
    )
    records = [
        {"url": "https://www.thegradcafe.com/result/900005"},
        {
            "url": "https://www.thegradcafe.com/result/900006",
            "break_insert": True,
        },
    ]

    def start_test_pull():
        load_records(records=records)
        return True

    application = create_app({
        "TESTING": True,
        "GET_STATUS_FN": lambda: {"running": False},
        "START_PULL_FN": start_test_pull,
    })

    response = application.test_client().post("/pull-data")
    assert response.status_code == 500
    assert response.get_json() == {"ok": False}

    with psycopg.connect(postgres_db) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM applicants"
        ).fetchone()[0]
    assert count == 0


def test_query_returns_expected_dictionary(orm_query):
    load_records(records=[
        {
            "url": "https://www.thegradcafe.com/result/900007",
            "term": "Fall 2026",
            "US/International": "American",
            "GPA": "3.8",
        },
        {
            "url": "https://www.thegradcafe.com/result/900008",
            "term": "Fall 2026",
            "US/International": "International",
            "GPA": "3.6",
        },
    ])

    results = orm_query()

    expected_keys = {
        "question_1", "question_2", "question_3",
        "question_4", "question_5", "question_6",
        "question_7", "question_8", "question_9",
        "original_question", "question_11",
    }
    assert isinstance(results, dict)
    assert set(results) == expected_keys
    assert results["question_1"] == 2
    assert results["question_2"] == pytest.approx(50.0)
    assert results["question_3"][0] == pytest.approx(3.7)
