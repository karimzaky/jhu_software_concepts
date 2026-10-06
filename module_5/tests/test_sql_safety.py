"""Verify identifier allowlists, limit bounds, and malicious applicant values."""

import psycopg
import pytest
from psycopg import sql

from app import create_app
from load_data import load_records
from sql_safety import (
    APPLICANT_COLUMNS,
    build_count_statement,
    build_insert_statement,
    clamp_limit,
)

pytestmark = pytest.mark.db


@pytest.mark.parametrize(
    "value,expected",
    [
        (1, 1),
        (100, 100),
        (0, 1),
        (-50, 1),
        (1000000, 100),
        ("5", 5),
        ("999999", 100),
        ("1; DROP TABLE applicants", 1),
        (None, 1),
        (True, 1),
        (1.5, 1),
        ("invalid", 1),
    ],
)
def test_limits_are_bounded(value, expected):
    assert clamp_limit(value) == expected


def test_default_limit_is_bounded():
    assert clamp_limit() == 100


@pytest.mark.parametrize(
    "table,columns",
    [
        ("applicants; DROP TABLE applicants", APPLICANT_COLUMNS),
        ("applicants", ("url) VALUES ('attack'); --",)),
    ],
)
def test_unapproved_identifiers_are_rejected(table, columns):
    with pytest.raises(ValueError, match="approved"):
        build_insert_statement(table, columns)


def test_insert_uses_quoted_identifiers_and_placeholders():
    statement = build_insert_statement()
    assert isinstance(statement, sql.Composed)
    rendered = statement.as_string()
    assert 'INSERT INTO "applicants"' in rendered
    assert all('"' + column + '"' in rendered for column in APPLICANT_COLUMNS)
    assert rendered.count("%s") == len(APPLICANT_COLUMNS)


def test_count_limit_is_bound_separately():
    statement, params = build_count_statement(1000000)
    assert statement.as_string() == 'SELECT COUNT(*) FROM "applicants" LIMIT %s'
    assert params == (100,)


def test_pull_treats_sql_payload_as_data(postgres_db):
    payload = "'); DROP TABLE applicants; --"
    records = [
        {
            "url": "https://www.thegradcafe.com/result/980001",
            "program": payload,
            "comments": "' OR 1=1 --",
        }
    ]

    def start_pull():
        load_records(records)
        return True

    application = create_app(
        {
            "TESTING": True,
            "GET_STATUS_FN": lambda: {"running": False},
            "START_PULL_FN": start_pull,
        }
    )
    response = application.test_client().post("/pull-data")
    assert response.status_code == 202
    assert payload not in response.get_data(as_text=True)
    with psycopg.connect(postgres_db) as connection:
        row = connection.execute("SELECT program, comments FROM applicants LIMIT 1").fetchone()
        statement, params = build_count_statement()
        total = connection.execute(statement, params).fetchone()[0]
    assert row == (payload, "' OR 1=1 --")
    assert total == 1
