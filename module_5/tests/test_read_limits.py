"""Verify analysis reads are bounded without truncating aggregate inputs."""

from unittest.mock import Mock

import psycopg
import pytest
from sqlalchemy.dialects import postgresql

import orm_queries
from load_data import load_records
from query_data import ANALYSIS_STATEMENTS, build_analysis_statement

pytestmark = pytest.mark.db


@pytest.mark.parametrize("number", range(1, 12))
def test_fixed_analysis_and_composed_statement_have_limits(number):
    assert "LIMIT" in ANALYSIS_STATEMENTS[number - 1]
    statement, params = build_analysis_statement(number, "1000000")
    rendered = statement.as_string()
    assert rendered.startswith("SELECT")
    assert rendered.endswith("LIMIT %s")
    expected = 1 if number < 10 else (5 if number == 11 else 100)
    assert params == (expected,)


@pytest.mark.parametrize("number", [0, 12, "1; DROP TABLE applicants", 1.5])
def test_analysis_rejects_unapproved_query_selection(number):
    with pytest.raises(ValueError, match="Question number"):
        build_analysis_statement(number)


@pytest.mark.parametrize(
    "name,expected",
    [
        ("get_question_1", 1),
        ("get_question_2", 1),
        ("get_question_3", 1),
        ("get_question_4", 1),
        ("get_question_5", 1),
        ("get_question_6", 1),
        ("get_question_7", 1),
        ("get_question_8", 1),
        ("get_question_9", 1),
        ("get_original_question", 100),
        ("get_question_11", 5),
    ],
)
def test_every_orm_analysis_emits_a_limit(name, expected):
    session = Mock()
    getattr(orm_queries, name)(session)
    call = session.scalar.call_args or session.execute.call_args
    statement = call.args[0]
    compiled = statement.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    assert str(compiled).strip().endswith("LIMIT " + str(expected))


@pytest.mark.parametrize("requested,expected", [(1000000, 100), (2, 2), ("bad", 1)])
def test_real_grouped_reads_enforce_requested_limit(postgres_db, requested, expected):
    records = [
        {
            "url": "https://www.thegradcafe.com/result/" + str(990000 + index),
            "term": "Fall 2026",
            "US/International": "American" + " " * index,
            "GPA": "3.8",
        }
        for index in range(130)
    ]
    load_records(records)
    # The loader strips whitespace, so create distinct groups in the isolated test DB.
    with psycopg.connect(postgres_db) as connection:
        connection.execute(
            "UPDATE applicants SET us_or_international = " "'American' || repeat(' ', p_id)"
        )
        statement, params = build_analysis_statement(10, requested)
        rows = connection.execute(statement, params).fetchall()
        count_statement, count_params = build_analysis_statement(1)
        total = connection.execute(count_statement, count_params).fetchone()[0]
    assert len(rows) == expected
    assert total == 130
    assert all(row[1] == 1 for row in rows)
