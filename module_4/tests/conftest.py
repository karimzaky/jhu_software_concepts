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


