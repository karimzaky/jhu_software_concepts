"""Load the cleaned GradCafe applicant data into PostgreSQL."""

import json
import os
import re
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "applicant_data.json"
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS applicants (
    p_id SERIAL PRIMARY KEY,
    program TEXT,
    comments TEXT,
    date_added DATE,
    url TEXT UNIQUE NOT NULL,
    status TEXT,
    term TEXT,
    us_or_international TEXT,
    gpa FLOAT,
    gre FLOAT,
    gre_v FLOAT,
    gre_aw FLOAT,
    degree TEXT,
    llm_generated_program TEXT,
    llm_generated_university TEXT
);
"""


INSERT_SQL = """
INSERT INTO applicants (
    program,
    comments,
    date_added,
    url,
    status,
    term,
    us_or_international,
    gpa,
    gre,
    gre_v,
    gre_aw,
    degree,
    llm_generated_program,
    llm_generated_university
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (url) DO NOTHING;
"""


def get_connection():
    """Create a PostgreSQL connection using environment variables."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg.connect(database_url)

    connection_settings = {
        "dbname": os.getenv("DB_NAME", "gradcafe_module3"),
        "user": os.getenv("DB_USER", "karimzaky"),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
    }

    password = os.getenv("DB_PASSWORD")
    if password:
        connection_settings["password"] = password

    return psycopg.connect(**connection_settings)


def clean_text(value):
    """Convert blank text values to None for SQL NULL storage."""
    if value is None:
        return None

    cleaned_value = str(value).strip()
    return cleaned_value if cleaned_value else None


def parse_number(value):
    """Extract a floating-point number from a labeled score string."""
    cleaned_value = clean_text(value)

    if cleaned_value is None:
        return None

    match = re.search(r"-?\d+(?:\.\d+)?", cleaned_value)
    return float(match.group()) if match else None

def parse_bounded_number(value, minimum, maximum):
    """
    Extract a number and return it only when it falls within an
    accepted range.

    Values outside the range are treated as missing because they
    cannot reliably represent the metric assigned to the column.
    """
    number = parse_number(value)

    if number is None:
        return None

    if minimum <= number <= maximum:
        return number

    return None

def parse_date(value):
    """Convert a GradCafe date string into a Python date."""
    cleaned_value = clean_text(value)

    if cleaned_value is None:
        return None

    cleaned_value = cleaned_value.removeprefix("Added on ").strip()

    try:
        return datetime.strptime(cleaned_value, "%b %d, %Y").date()
    except ValueError:
        return None


def prepare_record(record):
    """Convert one JSON record into the database column format."""
    return (
        clean_text(record.get("program")),
        clean_text(record.get("comments")),
        parse_date(record.get("date_added")),
        clean_text(record.get("url")),
        clean_text(record.get("status")),
        clean_text(record.get("term")),
        clean_text(record.get("US/International")),
        # GPA values above 4.33 are treated as invalid.
        parse_bounded_number(record.get("GPA"), 0, 4.33),

        # Current GRE Quantitative and Verbal scores range from 130 to 170.
        # Combined totals such as 328 cannot be treated as Quantitative scores.
        parse_bounded_number(record.get("GRE"), 130, 170),
        parse_bounded_number(record.get("GRE V"), 130, 170),

        # GRE Analytical Writing scores range from 0 to 6.
        parse_bounded_number(record.get("GRE AW"), 0, 6),
        clean_text(record.get("Degree")),
        clean_text(record.get("llm-generated-program")),
        clean_text(record.get("llm-generated-university")),
    )


def load_records(records=None):
    """Insert supplied records, or read records from the local JSON file.

    Return the number of newly inserted rows. Database errors propagate
    to the caller, and the connection context rolls back failed inserts.
    """
    if records is None:
        with DATA_FILE.open(encoding="utf-8") as file:
            records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Applicant data must be a list of records.")

    prepared_records = [
        prepare_record(record)
        for record in records
        if clean_text(record.get("url")) is not None
    ]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_TABLE_SQL)
            cursor.execute("SELECT COUNT(*) FROM applicants")
            count_before = cursor.fetchone()[0]

            cursor.executemany(INSERT_SQL, prepared_records)

            cursor.execute("SELECT COUNT(*) FROM applicants")
            count_after = cursor.fetchone()[0]

    inserted_count = count_after - count_before
    print(f"JSON records read: {len(records):,}")
    print(f"Usable records prepared: {len(prepared_records):,}")
    print(f"New records inserted: {inserted_count:,}")
    print(f"Total database records: {count_after:,}")
    return inserted_count


if __name__ == "__main__":
    load_records()
