"""Scrape publicly available GradCafe admissions results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin, urlparse
import subprocess
import re
from bs4 import BeautifulSoup
import time

BASE_URL = "https://www.thegradcafe.com"
SURVEY_PATH = "/survey"
OUTPUT_FILE = Path(__file__).with_name("applicant_data.json")
CAPTURE_DIRECTORY = Path(__file__).with_name("captured_pages")

DISALLOWED_PATHS = {
    "/signin",
    "/register",
    "/forgot-password",
    "/reset-password",
    "/confirm-password",
    "/verify-email",
    "/profile",
}


def build_survey_url(cursor: str | None = None) -> str:
    """Construct a GradCafe survey URL with an optional pagination cursor."""
    url = f"{BASE_URL}{SURVEY_PATH}"

    if cursor:
        url = f"{url}?{urlencode({'cursor': cursor})}"

    _validate_public_url(url)
    return url


def _validate_public_url(url: str) -> None:
    """Reject URLs outside the permitted public GradCafe survey pages."""
    parsed_url = urlparse(url)

    if parsed_url.scheme != "https":
        raise ValueError("Only HTTPS URLs are permitted.")

    if parsed_url.netloc != "www.thegradcafe.com":
        raise ValueError("The URL must belong to www.thegradcafe.com.")

    if parsed_url.path in DISALLOWED_PATHS:
        raise ValueError(f"robots.txt disallows this path: {parsed_url.path}")

    if parsed_url.path != SURVEY_PATH:
        raise ValueError(f"Unexpected GradCafe path: {parsed_url.path}")

def _navigate_chrome(url: str) -> None:
    """Navigate the active Chrome tab to a validated GradCafe survey URL."""
    _validate_public_url(url)

    apple_script = """
    on run arguments
        set targetURL to item 1 of arguments
        tell application "Google Chrome"
            if (count of windows) is 0 then
                error "Google Chrome has no open windows."
            end if
            set URL of active tab of window 1 to targetURL
        end tell
    end run
    """

    result = subprocess.run(
        ["osascript", "-e", apple_script, url],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Chrome navigation failed.\n"
            f"{result.stderr.strip()}"
        )


def _wait_for_survey_page(
    expected_url: str,
    previous_first_result: str | None = None,
    timeout_seconds: float = 45.0,
) -> None:
    """Wait until Chrome renders a new applicant-results table."""
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        current_url, current_html = _get_active_chrome_page()
        lowercase_html = current_html.lower()

        verification_phrases = (
            "verify you are human",
            "checking your browser",
            "performing security verification",
        )

        if any(
            phrase in lowercase_html
            for phrase in verification_phrases
        ):
            raise RuntimeError(
                "GradCafe displayed a verification page. "
                "Complete it manually and rerun the program."
            )

        first_result_match = re.search(
            r'href=["\'](/result/\d+)["\']',
            current_html,
        )
        current_first_result = (
            first_result_match.group(1)
            if first_result_match
            else None
        )

        result_changed = (
            previous_first_result is None
            or current_first_result != previous_first_result
        )

        page_is_ready = (
            current_url == expected_url
            and current_first_result is not None
            and result_changed
        )

        if page_is_ready:
            return

        time.sleep(1.0)

    raise TimeoutError(
        "GradCafe did not render a new results table within "
        f"{timeout_seconds} seconds: {expected_url}"
    )
    

def _get_active_chrome_page() -> tuple[str, str]:
    """Return the URL and rendered HTML from the active Chrome tab."""
    apple_script = """
    tell application "Google Chrome"
        if (count of windows) is 0 then
            error "Google Chrome has no open windows."
        end if
        set pageURL to URL of active tab of window 1
        set pageHTML to execute active tab of window 1 javascript "document.documentElement.outerHTML"
        return pageURL & "<<<GRADCAFE_SPLIT>>>" & pageHTML
    end tell
    """

    result = subprocess.run(
        ["osascript", "-e", apple_script],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Chrome capture failed. Confirm that Chrome is open and "
            "'Allow JavaScript from Apple Events' is enabled.\n"
            f"{result.stderr.strip()}"
        )

    page_url, separator, page_html = result.stdout.partition(
        "<<<GRADCAFE_SPLIT>>>"
    )

    if not separator or not page_html.strip():
        raise RuntimeError("Chrome did not return usable page HTML.")

    return page_url.strip(), page_html.strip()


def capture_current_page(page_number: int) -> Path:
    """Capture and save the currently displayed public GradCafe survey page."""
    page_url, page_html = _get_active_chrome_page()
    _validate_public_url(page_url)

    verification_phrases = (
        "verify you are human",
        "checking your browser",
        "performing security verification",
    )
    lowercase_html = page_html.lower()

    if any(phrase in lowercase_html for phrase in verification_phrases):
        raise RuntimeError(
            "The active page is a verification page. Complete verification "
            "manually in Chrome before capturing."
        )

    CAPTURE_DIRECTORY.mkdir(exist_ok=True)
    output_file = CAPTURE_DIRECTORY / f"page_{page_number:05d}.html"
    output_file.write_text(page_html, encoding="utf-8")

    print(f"Captured: {page_url}")
    print(f"Saved HTML: {output_file}")

    return output_file

def _is_applicant_row(row: Any) -> bool:
    """Return True when a table row begins a new applicant record."""
    cells = row.find_all("td", recursive=False)
    result_link = row.find("a", href=re.compile(r"^/result/\d+$"))
    return len(cells) >= 5 and result_link is not None


def _add_status_date(record: dict[str, Any]) -> None:
    """Extract the decision date from a status such as 'Accepted on May 04'."""
    match = re.fullmatch(
        r"(Accepted|Rejected|Wait listed|Interview) on (.+)",
        record["status"],
        flags=re.IGNORECASE,
    )

    if not match:
        return

    status_type = match.group(1).lower()
    status_date = match.group(2).strip()

    date_fields = {
        "accepted": "acceptance_date",
        "rejected": "rejection_date",
        "wait listed": "waitlist_date",
        "interview": "interview_date",
    }
    record[date_fields[status_type]] = status_date


def _add_badge_value(record: dict[str, Any], badge_text: str) -> None:
    """Place a metadata badge into the appropriate applicant field."""
    badge_text = badge_text.strip()

    if badge_text == record["status"]:
        return

    if re.fullmatch(
        r"(Fall|Spring|Summer|Winter)\s+\d{4}",
        badge_text,
        flags=re.IGNORECASE,
    ):
        record["term"] = badge_text
    elif badge_text in {"American", "International"}:
        record["US/International"] = badge_text
    elif badge_text.startswith("GRE AW "):
        record["GRE AW"] = badge_text
    elif badge_text.startswith("GRE V "):
        record["GRE V"] = badge_text
    elif badge_text.startswith("GRE "):
        record["GRE"] = badge_text
    elif badge_text.startswith("GPA "):
        record["GPA"] = badge_text


def _parse_applicant_row(row: Any) -> dict[str, Any]:
    """Parse the main table row for one applicant."""
    cells = row.find_all("td", recursive=False)
    result_link = row.find("a", href=re.compile(r"^/result/\d+$"))

    university = cells[0].get_text(" ", strip=True)
    program_parts = cells[1].find_all("span")
    program_name = program_parts[0].get_text(" ", strip=True)
    degree = (
        program_parts[-1].get_text(" ", strip=True)
        if len(program_parts) > 1
        else None
    )
    date_added = cells[2].get_text(" ", strip=True)
    status = cells[3].get_text(" ", strip=True)

    record = {
        # Combined value required by the supplied LLM package:
        "program": f"{program_name}, {university}",
        # Separate raw values preserved for traceability:
        "program_name": program_name,
        "university": university,
        "comments": None,
        "date_added": f"Added on {date_added}",
        "url": urljoin(BASE_URL, result_link["href"]),
        "status": status,
        "acceptance_date": None,
        "rejection_date": None,
        "waitlist_date": None,
        "interview_date": None,
        "term": None,
        "US/International": None,
        "GRE": None,
        "GRE V": None,
        "GPA": None,
        "GRE AW": None,
        "Degree": degree,
    }

    _add_status_date(record)
    return record


def parse_captured_page(
    input_file: Path,
) -> tuple[list[dict[str, Any]], str | None]:
    """Parse applicant records and the next cursor URL from captured HTML."""
    html = input_file.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    table_body = soup.select_one("table tbody")

    if table_body is None:
        raise ValueError("No applicant results table was found.")

    rows = table_body.find_all("tr", recursive=False)
    records: list[dict[str, Any]] = []
    row_index = 0

    while row_index < len(rows):
        current_row = rows[row_index]

        if not _is_applicant_row(current_row):
            row_index += 1
            continue

        record = _parse_applicant_row(current_row)
        row_index += 1

        # Metadata and comments appear after the main applicant row.
        while (
            row_index < len(rows)
            and not _is_applicant_row(rows[row_index])
        ):
            supplementary_row = rows[row_index]

            for badge in supplementary_row.select("td > div > div"):
                _add_badge_value(
                    record,
                    badge.get_text(" ", strip=True),
                )

            comment = supplementary_row.find("p")
            if comment is not None:
                record["comments"] = comment.get_text(" ", strip=True)

            row_index += 1

        records.append(record)

    next_url = None

    for link in soup.find_all("a", href=True):
        if link.get_text(" ", strip=True) == "Next":
            next_url = urljoin(BASE_URL, link["href"])
            _validate_public_url(next_url)
            break

    return records, next_url

def save_data(
    records: list[dict[str, Any]],
    output_file: Path = OUTPUT_FILE,
) -> None:
    """Save records atomically so an interruption does not corrupt the JSON."""
    temporary_file = output_file.with_suffix(".tmp")
    temporary_file.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_file.replace(output_file)


def load_data(input_file: Path = OUTPUT_FILE) -> list[dict[str, Any]]:
    """Load previously saved records so scraping can resume."""
    if not input_file.exists():
        return []

    records = json.loads(input_file.read_text(encoding="utf-8"))

    if not isinstance(records, list):
        raise ValueError("The applicant data file must contain a JSON list.")

    return records


if __name__ == "__main__":
    first_file = CAPTURE_DIRECTORY / "page_00001.html"
    first_records, second_page_url = parse_captured_page(first_file)

    if second_page_url is None:
        raise RuntimeError("The first page did not contain a Next link.")

    print(f"Navigating to: {second_page_url}")
    _navigate_chrome(second_page_url)

    previous_first_result = urlparse(first_records[0]["url"]).path

    _wait_for_survey_page(
        second_page_url,
        previous_first_result=previous_first_result,
    )

    second_file = capture_current_page(page_number=2)
    second_records, third_page_url = parse_captured_page(second_file)

    print(f"Parsed page 2 records: {len(second_records)}")
    print(f"Next page: {third_page_url}")