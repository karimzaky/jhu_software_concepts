"""Shared test fixtures."""

import pytest
from app import create_app


@pytest.fixture
def application():
    """Create an app with fake analysis data and no database calls."""
    results = {
        "question_1": 10,
        "question_2": 33.333,
        "question_3": (3.5, 160.0, 155.0, 4.0),
        "question_4": 3.6,
        "question_5": 25.0,
        "question_6": 3.7,
        "question_7": 2,
        "question_8": 3,
        "question_9": 4,
        "original_question": [],
        "question_11": [],
    }
    status = {
        "running": False,
        "message": "Idle",
        "last_added": None,
        "last_finished": None,
        "error": None,
    }
    return create_app({
        "TESTING": True,
        "QUERY_RESULTS_FN": lambda: results,
        "GET_STATUS_FN": lambda: status,
    })




@pytest.fixture
def postgres_db(monkeypatch):
    """Prepare an isolated PostgreSQL database for each database test."""
    import os

    import psycopg

    from load_data import CREATE_TABLE_SQL

    database_url = os.environ["TEST_DATABASE_URL"]
    with psycopg.connect(database_url) as connection:
        name = connection.execute("SELECT current_database()").fetchone()[0]
        if not name.endswith("_test"):
            raise RuntimeError("Database tests require a database ending in _test")
        connection.execute(CREATE_TABLE_SQL)
        connection.execute("TRUNCATE applicants RESTART IDENTITY")

    monkeypatch.setenv("DATABASE_URL", database_url)
    return database_url


@pytest.fixture
def orm_query(postgres_db, monkeypatch):
    """Bind the real query service to the isolated test database."""
    import orm_queries
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url
    from sqlalchemy.orm import sessionmaker

    url = make_url(postgres_db).set(drivername="postgresql+psycopg")
    test_engine = create_engine(url)
    test_sessions = sessionmaker(bind=test_engine, expire_on_commit=False)
    monkeypatch.setattr(orm_queries, "SessionLocal", test_sessions)

    try:
        yield orm_queries.collect_all_analysis_results
    finally:
        test_engine.dispose()
