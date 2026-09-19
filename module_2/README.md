# Module 2 – Web Scraping Assignment

## Student and Module Information

- Name: Karim Zaky
- JHED ID: kzaky1
- Course: Modern Software Concepts in Python
- Module: Module 2
- Assignment: Web Scraping Assignment
- Due Date: September 13, 2026

## Approach

The project collects publicly available graduate-admissions results from GradCafe and stores them as structured JSON.

Direct urllib/urllib3 requests returned HTTP 403, while Selenium was affected by Cloudflare verification. Following the instructor's updated guidance, the scraper uses a normal Google Chrome session. The user completes any legitimate Cloudflare verification manually, and Python uses macOS AppleScript to capture the HTML already displayed in Chrome. The program does not solve or bypass CAPTCHAs, authentication, rate limits, or access controls.

`urllib.parse` constructs and validates GradCafe URLs. BeautifulSoup, regex, and Python string methods parse the captured HTML. Each applicant record includes the original program and university values, comments, date added, result URL, status, decision date, term, residency classification, degree, GPA, and GRE information when available.

GradCafe uses cursor-based pagination. The scraper extracts each Next URL without modifying its opaque cursor. It waits for the result table to change before capturing the next page, uses a four-second delay, deduplicates records by applicant URL, and saves both the JSON data and next-page state after every page. This allows an interrupted run to resume without starting over.

The final `applicant_data.json` contains 30,000 valid records with 30,000 unique applicant URLs.

`clean.py` decodes HTML entities, normalizes comment whitespace, validates result URLs, ensures expected keys exist, and removes duplicate URLs. It preserves the original `program`, `program_name`, and `university` fields for traceability. Cleaning retained all 30,000 records and changed only whitespace in 938 comments.

The instructor-provided TinyLlama package adds:

- `llm-generated-program`
- `llm-generated-university`

The final `llm_extend_applicant_data.json` contains 30,000 records, preserves all original program values, and contains both LLM-generated fields for every record.

## Robots.txt Compliance

GradCafe's `robots.txt` was checked before scraping. For `User-agent: *`, it disallowed account-related paths including `/signin`, `/register`, password-reset paths, `/verify-email`, and `/profile`. The public `/survey` and `/result/` pages were not disallowed.

The scraper accesses only public survey pages, uses polite delays, and stops if verification, blocking, or an unexpected page occurs. Evidence is included in `screenshot.jpg`.

## Setup and Run Instructions

Python 3.10 or later is required. This project was developed with Python 3.13.15 on macOS using Google Chrome.

```bash
cd module_2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

In Chrome, enable:

`View → Developer → Allow JavaScript from Apple Events`

Open `https://www.thegradcafe.com/survey`, complete any normal verification manually, and run:

```bash
python scrape.py --target-records 30000
python clean.py
```

Run the local LLM:

```bash
cd llm_hosting
python app.py --file ../applicant_data.json --stdout > ../llm_extend_applicant_data.jsonl
cd ..
```

Convert JSON Lines into the required JSON array:

```bash
python - <<'PY'
import json
from pathlib import Path

source = Path("llm_extend_applicant_data.jsonl")
records = [
    json.loads(line)
    for line in source.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

Path("llm_extend_applicant_data.json").write_text(
    json.dumps(records, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
PY
```

## Known Limitations

Three of the 30,000 records produced `"Unknown"` for `llm-generated-university`. A future improvement would add those university variants to the canonical list or apply a documented fallback to the preserved raw `university` field.

Because GradCafe is a live website, future HTML changes may require selector updates. Cloudflare verification must always be completed manually; the program intentionally does not bypass it.
