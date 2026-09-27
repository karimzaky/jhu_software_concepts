"""Run the dynamic Flask analysis webpage for Module 3."""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    url_for,
)

from orm_queries import collect_all_analysis_results
from scrape_manager import get_scrape_status, start_data_pull


# Load local environment variables from the ignored .env file.
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# Create the Flask application.
app = Flask(__name__)


# Flask uses the secret key to protect session data and flash messages.
# A local fallback allows the coursework app to run even if the optional
# environment variable is not set.
app.config["SECRET_KEY"] = os.getenv(
    "FLASK_SECRET_KEY",
    "module-3-local-development-key",
)


def build_view_model(raw_results):
    """
    Convert raw SQLAlchemy values into display-ready strings.

    Formatting values here keeps presentation formatting out of the
    database queries and makes the HTML template easier to read.
    """
    average_gpa, average_gre, average_gre_v, average_gre_aw = (
        raw_results["question_3"]
    )

    original_count = raw_results["question_8"]
    llm_count = raw_results["question_9"]

    nationality_results = [
        {
            "group": row.applicant_group,
            "total": f"{row.total_entries:,}",
            "accepted": f"{row.accepted_entries:,}",
            "percentage": (
                f"{row.acceptance_percentage:.2f}%"
            ),
        }
        for row in raw_results["original_question"]
    ]

    top_universities = [
        {
            "university": row.university,
            "accepted_entries": (
                f"{row.accepted_entries:,}"
            ),
        }
        for row in raw_results["question_11"]
    ]

    return {
        "fall_2026_count": (
            f"{raw_results['question_1']:,}"
        ),
        "percent_international": (
            f"{raw_results['question_2']:.2f}%"
        ),
        "average_gpa": f"{average_gpa:.2f}",
        "average_gre": f"{average_gre:.2f}",
        "average_gre_v": f"{average_gre_v:.2f}",
        "average_gre_aw": f"{average_gre_aw:.2f}",
        "american_fall_2026_gpa": (
            f"{raw_results['question_4']:.2f}"
        ),
        "fall_2025_acceptance_percentage": (
            f"{raw_results['question_5']:.2f}%"
        ),
        "accepted_fall_2026_gpa": (
            f"{raw_results['question_6']:.2f}"
        ),
        "jhu_cs_masters_count": (
            f"{raw_results['question_7']:,}"
        ),
        "original_field_count": f"{original_count:,}",
        "llm_field_count": f"{llm_count:,}",
        "field_count_difference": (
            f"{llm_count - original_count:+,}"
        ),
        "nationality_results": nationality_results,
        "top_universities": top_universities,
    }


@app.get("/")
def analysis():
    """
    Query PostgreSQL through SQLAlchemy and display the analysis page.

    Every page request retrieves the current database results rather
    than displaying hard-coded values.
    """
    try:
        raw_results = collect_all_analysis_results()
        results = build_view_model(raw_results)

        updated_at = datetime.now().strftime(
            "%B %d, %Y at %I:%M:%S %p"
        )

        return render_template(
            "analysis.html",
            results=results,
            updated_at=updated_at,
            scrape_status=get_scrape_status(),
        )

    except Exception:
        # Record the full error in the Flask terminal for debugging,
        # while showing the user a concise message.
        app.logger.exception(
            "Unable to retrieve the database analysis."
        )

        return render_template(
            "analysis.html",
            results=None,
            updated_at=None,
            scrape_status=get_scrape_status(),
        ), 500


@app.post("/pull-data")
def pull_data():
    """
    Start one background scrape without blocking the Flask webpage.

    start_data_pull prevents another scraping process from starting
    while the current background worker still owns the scrape lock.
    """
    scrape_started = start_data_pull()

    if scrape_started:
        flash(
            "Data pull started. Keep Google Chrome open, then use "
            "Update Analysis after the pull finishes.",
            "success",
        )
    else:
        flash(
            "A data pull is already running. Please wait for it to finish.",
            "warning",
        )

    return redirect(url_for("analysis"))

@app.post("/update-analysis")
def update_analysis():
    """
    Re-query PostgreSQL unless a background data pull is still running.

    The route does not start the scraper. It refreshes the analysis
    after newly scraped records have been stored in PostgreSQL.
    """
    scrape_status = get_scrape_status()

    if scrape_status["running"]:
        flash(
            "The data pull is still running. The analysis currently "
            "shows the latest completed database update.",
            "warning",
        )
    elif scrape_status["error"]:
        flash(
            f"The most recent data pull failed: "
            f"{scrape_status['error']}",
            "error",
        )
    else:
        flash(
            "Analysis refreshed using the latest database records.",
            "success",
        )

    return redirect(url_for("analysis"))


def main():
    """Start the local Flask development server."""
    debug_enabled = (
        os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=debug_enabled,
    )


# Start Flask only when app.py is executed directly.
if __name__ == "__main__":
    main()