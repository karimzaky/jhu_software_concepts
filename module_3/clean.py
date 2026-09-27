"""Clean and validate structured GradCafe applicant data."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from scrape import load_data, save_data


DEFAULT_INPUT = Path(__file__).with_name("applicant_data.json")

EXPECTED_FIELDS = (
    "program",
    "program_name",
    "university",
    "comments",
    "date_added",
    "url",
    "status",
    "acceptance_date",
    "rejection_date",
    "waitlist_date",
    "interview_date",
    "term",
    "US/International",
    "GRE",
    "GRE V",
    "GPA",
    "GRE AW",
    "Degree",
)

# These raw source values must not be standardized or overwritten here.
TRACEABILITY_FIELDS = {
    "program",
    "program_name",
    "university",
}


def _clean_text(value: Any) -> Any:
    """Decode HTML entities and collapse unnecessary whitespace."""
    if not isinstance(value, str):
        return value

    cleaned_value = html.unescape(value)
    cleaned_value = re.sub(r"\s+", " ", cleaned_value).strip()

    return cleaned_value or None


def _validate_result_url(url: Any) -> None:
    """Require a public GradCafe applicant-result URL."""
    if not isinstance(url, str):
        raise ValueError("Each record must contain a URL string.")

    parsed_url = urlparse(url)

    if (
        parsed_url.scheme != "https"
        or parsed_url.netloc != "www.thegradcafe.com"
        or re.fullmatch(r"/result/\d+", parsed_url.path) is None
    ):
        raise ValueError(f"Unexpected applicant URL: {url}")


def _clean_record(record: dict[str, Any]) -> dict[str, Any]:
    """Clean one record without altering its traceability fields."""
    cleaned_record = dict(record)

    for field in EXPECTED_FIELDS:
        cleaned_record.setdefault(field, None)

    for field, value in cleaned_record.items():
        if field not in TRACEABILITY_FIELDS:
            cleaned_record[field] = _clean_text(value)

    _validate_result_url(cleaned_record["url"])
    return cleaned_record


def clean_data(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Clean records and remove duplicate applicant URLs."""
    cleaned_by_url: dict[str, dict[str, Any]] = {}

    for record_number, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(
                f"Record {record_number} is not a JSON object."
            )

        cleaned_record = _clean_record(record)
        cleaned_by_url[cleaned_record["url"]] = cleaned_record

    return list(cleaned_by_url.values())


def main() -> None:
    """Load, clean, validate, and save applicant records."""
    parser = argparse.ArgumentParser(
        description="Clean structured GradCafe applicant data."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Input JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_INPUT,
        help="Output JSON file. Defaults to applicant_data.json.",
    )
    arguments = parser.parse_args()

    original_records = load_data(arguments.input)
    cleaned_records = clean_data(original_records)
    save_data(cleaned_records, arguments.output)

    print(f"Input records: {len(original_records)}")
    print(f"Cleaned records: {len(cleaned_records)}")
    print(
        "Duplicates removed: "
        f"{len(original_records) - len(cleaned_records)}"
    )
    print(f"Saved cleaned data: {arguments.output}")


if __name__ == "__main__":
    main()