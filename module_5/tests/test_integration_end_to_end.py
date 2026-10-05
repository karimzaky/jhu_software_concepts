"""Verify complete pull, update, and render flows."""

import psycopg
import pytest
from bs4 import BeautifulSoup

from app import create_app
from load_data import load_records

pytestmark = pytest.mark.integration


@pytest.fixture
def integration_system(orm_query, postgres_db):
    first = {
        "url": "https://www.thegradcafe.com/result/910001",
        "program": "Computer Science, Johns Hopkins University",
        "term": "Fall 2026",
        "status": "Accepted",
        "US/International": "American",
        "Degree": "Masters",
        "GPA": "3.8",
        "GRE": "160",
        "GRE V": "155",
        "GRE AW": "4",
    }
    second = dict(
        first,
        url="https://www.thegradcafe.com/result/910002",
        status="Rejected",
    )
    second["US/International"] = "International"
    batches = [[first, second]]

    def fake_scraper():
        return batches.pop(0)

    def start_test_pull():
        load_records(records=fake_scraper())
        return True

    application = create_app({
        "TESTING": True,
        "QUERY_RESULTS_FN": orm_query,
        "START_PULL_FN": start_test_pull,
        "GET_STATUS_FN": lambda: {
            "running": False,
            "message": "Idle",
            "error": None,
            "last_added": None,
            "last_finished": None,
        },
    })
    return application.test_client(), batches, first, second, postgres_db


def test_pull_update_render(integration_system):
    client, _, _, _, database_url = integration_system

    assert client.post("/pull-data").status_code == 202

    with psycopg.connect(database_url) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM applicants"
        ).fetchone()[0] == 2

    assert client.post("/update-analysis").status_code == 200
    response = client.get("/analysis")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    values = soup.select(".metric-value")
    assert values[0].get_text(" ", strip=True) == "Answer: 2"
    assert values[1].get_text(" ", strip=True) == "Answer: 50.00%"


def test_overlapping_pulls_preserve_uniqueness(integration_system):
    client, batches, _, second, database_url = integration_system
    third = dict(
        second,
        url="https://www.thegradcafe.com/result/910003",
    )
    batches.append([second, third])

    for _ in range(2):
        assert client.post("/pull-data").status_code == 202

    with psycopg.connect(database_url) as connection:
        total, unique = connection.execute(
            "SELECT COUNT(*), COUNT(DISTINCT url) FROM applicants"
        ).fetchone()

    assert total == unique == 3


def test_empty_database_renders_analysis(integration_system):
    client, _, _, _, _ = integration_system

    response = client.get("/analysis")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    values = soup.select(".metric-value")
    assert values[0].get_text(" ", strip=True) == "Answer: 0"
    assert values[1].get_text(" ", strip=True) == "Answer: N/A"
