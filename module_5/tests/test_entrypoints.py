"""Verify service entry points and database console utilities."""

import io
import json
import runpy
from pathlib import Path
from unittest.mock import Mock

import psycopg
import pytest

import app
import load_data
import models
import orm_queries
import query_data

pytestmark = pytest.mark.db


@pytest.mark.web
@pytest.mark.parametrize("debug", [False, True])
def test_app_script_uses_expected_server_settings(monkeypatch, debug):
    run = Mock()
    monkeypatch.setattr(app.Flask, "run", run)
    monkeypatch.setenv("FLASK_DEBUG", str(debug).lower())

    runpy.run_path(app.__file__, run_name="__main__")

    run.assert_called_once_with(
        host="127.0.0.1", port=5000, debug=debug
    )


def test_loader_script_inserts_local_input(
    postgres_db, monkeypatch, capsys
):
    records = [{
        "url": "https://www.thegradcafe.com/result/940001",
        "program": "Computer Science, Example University",
    }]
    original_open = Path.open

    def controlled_open(path, *args, **kwargs):
        if path == load_data.DATA_FILE:
            return io.StringIO(json.dumps(records))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", controlled_open)
    runpy.run_path(load_data.__file__, run_name="__main__")

    with psycopg.connect(postgres_db) as connection:
        assert connection.execute(
            "SELECT url FROM applicants"
        ).fetchall() == [(records[0]["url"],)]
    assert "New records inserted: 1" in capsys.readouterr().out


@pytest.fixture
def populated_queries(orm_query, monkeypatch):
    base = {
        "program": "Computer Science, Johns Hopkins University",
        "status": "Accepted",
        "term": "Fall 2026",
        "US/International": "American",
        "Degree": "Masters",
        "GPA": "3.8",
        "GRE": "160",
        "GRE V": "155",
        "GRE AW": "4",
        "llm-generated-program": "Computer Science",
        "llm-generated-university": "Johns Hopkins University",
    }
    first = dict(base, url="https://www.thegradcafe.com/result/940002")
    second = dict(base, url="https://www.thegradcafe.com/result/940003")
    second["US/International"] = "International"
    third = dict(
        base,
        url="https://www.thegradcafe.com/result/940004",
        term="Fall 2025",
    )
    load_data.load_records(records=[first, second, third])
    monkeypatch.setattr(models, "SESSION_FACTORY", orm_queries.SESSION_FACTORY)
    return orm_query


def test_model_representation():
    applicant = models.Applicant(
        p_id=7, program="Computer Science", status="Accepted"
    )
    assert repr(applicant) == (
        "Applicant(p_id=7, program='Computer Science', status='Accepted')"
    )


def test_model_connection_reports_count(populated_queries, capsys):
    models.test_model_connection()
    assert "SQLAlchemy Applicant count: 3" in capsys.readouterr().out


def test_model_script_accepts_database_url(postgres_db, capsys):
    namespace = runpy.run_path(models.__file__, run_name="__main__")
    try:
        assert "SQLAlchemy Applicant count: 0" in capsys.readouterr().out
    finally:
        namespace["engine"].dispose()


@pytest.mark.parametrize("entrypoint", ["function", "script"])
def test_orm_console_output(populated_queries, capsys, entrypoint):
    if entrypoint == "function":
        orm_queries.main()
    else:
        runpy.run_path(orm_queries.__file__, run_name="__main__")
    output = capsys.readouterr().out
    assert "Fall 2026 applicant count: 2" in output
    assert "100.00%" in output
    assert "Original Question" in output


@pytest.mark.parametrize("entrypoint", ["function", "script"])
def test_raw_sql_console_output(populated_queries, capsys, entrypoint):
    if entrypoint == "function":
        query_data.run_raw_sql_queries()
    else:
        runpy.run_path(query_data.__file__, run_name="__main__")
    output = capsys.readouterr().out
    assert "Fall 2026 applicant count: 2" in output
    assert "Question 11" in output
    assert "100.00%" in output
