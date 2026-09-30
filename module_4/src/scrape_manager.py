"""Manage background scraping for the Module 3 Flask application."""

import json
import threading
from datetime import datetime
from pathlib import Path

from load_data import get_connection, load_records
from scrape import scrape_data


# Locate the JSON file relative to this Python file.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "applicant_data.json"


# Only one scraping thread can hold this lock at a time.
# A second Pull Data request will therefore be rejected while the
# current scrape is still running.
SCRAPE_LOCK = threading.Lock()


# Protect status information because Flask requests and the background
# scraping thread can access it at the same time.
STATUS_LOCK = threading.Lock()


# Store the current scraping state for display on the webpage.
_scrape_status = {
    "running": False,
    "message": "No data pull is currently running.",
    "last_added": None,
    "last_finished": None,
    "error": None,
}


def _set_status(**changes):
    """Safely update one or more scraping-status values."""
    with STATUS_LOCK:
        _scrape_status.update(changes)


def get_scrape_status():
    """Return a safe copy of the current scraping status."""
    with STATUS_LOCK:
        return dict(_scrape_status)


def _json_record_count():
    """Return the number of applicant records currently in JSON."""
    with DATA_FILE.open(encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError(
            "applicant_data.json must contain a JSON list."
        )

    return len(records)


def _database_record_count():
    """Return the number of applicant rows currently in PostgreSQL."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM applicants;")
            return cursor.fetchone()[0]


def _pull_data_worker():
    """
    Scrape one GradCafe page and load its new records into PostgreSQL.

    This function runs in a background thread so Flask can continue
    responding while Chrome captures the page.
    """
    try:
        starting_json_count = _json_record_count()
        starting_database_count = _database_record_count()

        # GradCafe normally returns 20 records per page. Setting the
        # target 20 records above the current count requests one page.
        target_record_count = starting_json_count + 20

        _set_status(
            running=True,
            message=(
                "Pulling one new GradCafe page. Keep Google Chrome "
                "open while the scrape runs."
            ),
            last_added=None,
            error=None,
        )

        # Reuse the Module 2 scraper and limit this request to one page.
        scraped_records = scrape_data(
            target_records=target_record_count,
            max_pages=1,
        )

        scraped_count = len(scraped_records) - starting_json_count

        # Insert only new URLs; load_records uses ON CONFLICT DO NOTHING.
        load_records()

        ending_database_count = _database_record_count()
        inserted_count = (
            ending_database_count - starting_database_count
        )

        # Detect a partial failure where JSON received new records but
        # PostgreSQL did not receive all of them.
        if inserted_count < scraped_count:
            raise RuntimeError(
                f"The scraper collected {scraped_count} new records, "
                f"but PostgreSQL inserted only {inserted_count}."
            )

        finished_time = datetime.now().strftime(
            "%B %d, %Y at %I:%M:%S %p"
        )

        _set_status(
            running=False,
            message=(
                f"Data pull completed successfully. "
                f"{inserted_count} new database records were added."
            ),
            last_added=inserted_count,
            last_finished=finished_time,
            error=None,
        )

    except Exception as error:
        finished_time = datetime.now().strftime(
            "%B %d, %Y at %I:%M:%S %p"
        )

        _set_status(
            running=False,
            message="The data pull did not complete successfully.",
            last_added=0,
            last_finished=finished_time,
            error=str(error),
        )

    finally:
        # Always release the lock, even when scraping or loading fails.
        SCRAPE_LOCK.release()


def start_data_pull():
    """
    Start one background data pull.

    Return False when another scrape already owns the lock, preventing
    simultaneous Chrome navigation and duplicate scraping processes.
    """
    lock_acquired = SCRAPE_LOCK.acquire(blocking=False)

    if not lock_acquired:
        return False

    _set_status(
        running=True,
        message="The data pull is starting.",
        last_added=None,
        error=None,
    )

    worker = threading.Thread(
        target=_pull_data_worker,
        name="gradcafe-data-pull",
        daemon=True,
    )
    worker.start()

    return True