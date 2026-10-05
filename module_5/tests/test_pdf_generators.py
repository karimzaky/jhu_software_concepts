"""Verify inherited PDF generators using isolated data and temporary output."""

import runpy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import pypdf
import reportlab.platypus

import generate_limitations
import generate_query_results
import load_data

pytestmark = pytest.mark.db


@pytest.fixture
def report_data(orm_query):
    """Supply complete analysis data for both reports."""
    base = {
        "program": "Computer Science, Columbia University",
        "status": "Accepted",
        "term": "Fall 2026",
        "US/International": "American",
        "Degree": "Masters",
        "GPA": "3.8",
        "GRE": "160",
        "GRE V": "155",
        "GRE AW": "4",
        "llm-generated-program": "Computer Science",
        "llm-generated-university": "Columbia University",
    }
    first = dict(base, url="https://www.thegradcafe.com/result/970001")
    second = dict(base, url="https://www.thegradcafe.com/result/970002")
    second["US/International"] = "International"
    second["status"] = "Rejected"
    third = dict(
        base,
        url="https://www.thegradcafe.com/result/970003",
        term="Fall 2025",
    )
    load_data.load_records(records=[first, second, third])


@pytest.mark.parametrize("module", [
    generate_query_results, generate_limitations,
])
@pytest.mark.parametrize("entrypoint", ["function", "script"])
def test_reports_generate_and_validate(
    report_data, tmp_path, monkeypatch, capsys, module, entrypoint
):
    """Redirect both PDF writing and reading to the temporary folder."""
    original_document = reportlab.platypus.SimpleDocTemplate
    original_reader = pypdf.PdfReader

    def temporary_document(filename, *args, **kwargs):
        destination = tmp_path / Path(filename).name
        return original_document(str(destination), *args, **kwargs)

    def temporary_reader(filename, *args, **kwargs):
        destination = tmp_path / Path(filename).name
        return original_reader(str(destination), *args, **kwargs)

    # Existing module references are used by main().
    monkeypatch.setattr(module, "SimpleDocTemplate", temporary_document)
    monkeypatch.setattr(module, "PdfReader", temporary_reader)

    # Fresh imports are used when runpy executes the script entry point.
    monkeypatch.setattr(
        reportlab.platypus, "SimpleDocTemplate", temporary_document
    )
    monkeypatch.setattr(pypdf, "PdfReader", temporary_reader)

    if entrypoint == "function":
        module.main()
    else:
        runpy.run_path(module.__file__, run_name="__main__")

    output = tmp_path / module.OUTPUT_FILE.name
    assert output.exists()
    assert output.stat().st_size > 0

    reader = original_reader(str(output))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert reader.pages
    assert "Page 1" in text

    if module is generate_query_results:
        assert "Question 1" in text
        assert "Question 11" in text
        assert "Fall 2026 applicant count: 2" in text
        assert "Columbia University" in text
    else:
        assert "Data and Analysis Limitations" in text
        assert "Self-Reporting and Selection Bias" in text
        assert "Missing Values and Field Reliability" in text

    assert "PDF text validation passed" in capsys.readouterr().out


@pytest.mark.parametrize("module", [
    generate_query_results, generate_limitations,
])
@pytest.mark.parametrize("extracted_text", [None, "Incomplete report"])
def test_incomplete_reports_are_rejected(monkeypatch, module, extracted_text):
    page = SimpleNamespace(extract_text=lambda: extracted_text)
    reader = Mock(return_value=SimpleNamespace(pages=[page]))
    monkeypatch.setattr(module, "PdfReader", reader)

    with pytest.raises(ValueError, match="Missing text"):
        module.validate_pdf()


def test_query_report_collects_real_database_results(report_data):
    results = generate_query_results.collect_results()
    assert set(results) == {f"q{number}" for number in range(1, 12)}
    assert results["q1"] == 2
    assert float(results["q2"]) == pytest.approx(100 / 3)
    assert results["q11"] == [("Columbia University", 1)]


def test_limitations_report_counts_real_database_values(report_data):
    assert generate_limitations.get_database_count() == 3
    assert generate_limitations.get_missing_value_counts() == (0, 0, 0, 0)


def test_report_text_escapes_markup():
    assert generate_query_results.paragraph_text(
        "A & B\n<example>"
    ) == "A &amp; B<br/>&lt;example&gt;"
    assert generate_query_results.format_sql(
        "  SELECT 1;\n"
    ) == "SELECT 1;"
