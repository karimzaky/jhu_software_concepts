"""Verify rendered analysis labels and percentage precision."""

import re
from types import SimpleNamespace

import pytest
from bs4 import BeautifulSoup

pytestmark = pytest.mark.analysis


def test_all_result_blocks_have_answer_labels(application):
    response = application.test_client().get("/analysis")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")

    values = soup.select(".metric-value, .analysis-value")
    assert values
    for value in values:
        assert value.get_text(" ", strip=True).startswith("Answer:")

    tables = soup.select(".table-wrapper")
    assert len(tables) == 2
    for table in tables:
        label = table.find_previous_sibling("p")
        assert label is not None
        assert label.get_text(strip=True) == "Answer:"


def test_percentage_precision_and_rounding(application):
    original_query = application.config["QUERY_RESULTS_FN"]
    results = dict(original_query())
    results["question_2"] = 33.333
    results["question_5"] = 25.0
    results["original_question"] = [
        SimpleNamespace(
            applicant_group="International",
            total_entries=3,
            accepted_entries=1,
            acceptance_percentage=33.333,
        ),
        SimpleNamespace(
            applicant_group="American",
            total_entries=1,
            accepted_entries=0,
            acceptance_percentage=0.0,
        ),
    ]
    application.config["QUERY_RESULTS_FN"] = lambda: results

    response = application.test_client().get("/analysis")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")

    percentages = re.findall(r"\S*%", soup.get_text(" ", strip=True))
    assert len(percentages) == 4
    assert all(
        re.fullmatch(r"\d+\.\d{2}%", value)
        for value in percentages
    )
    assert percentages.count("33.33%") == 2
    assert "25.00%" in percentages
    assert "0.00%" in percentages
