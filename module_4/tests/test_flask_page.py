"""Verify the app factory and Analysis page."""

import pytest
from bs4 import BeautifulSoup

from app import create_app

pytestmark = pytest.mark.web


def test_factory_config_and_routes(application):
    assert application.config["TESTING"] is True

    routes = {rule.rule for rule in application.url_map.iter_rules()}
    assert {"/", "/analysis", "/pull-data", "/update-analysis"} <= routes


@pytest.mark.parametrize("route", ["/", "/analysis"])
def test_analysis_page_content(application, route):
    response = application.test_client().get(route)

    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    text = soup.get_text(" ", strip=True)
    assert "Analysis" in text
    assert "Answer:" in text
    assert "Pull Data" in text
    assert "Update Analysis" in text


def test_stable_button_selectors(application):
    response = application.test_client().get("/analysis")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")

    pull = soup.select_one('button[data-testid="pull-data-btn"]')
    update = soup.select_one('button[data-testid="update-analysis-btn"]')
    assert pull is not None
    assert update is not None
    assert pull.get_text(strip=True) == "Pull Data"
    assert update.get_text(strip=True) == "Update Analysis"
