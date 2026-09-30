"""Run the dynamic Flask analysis webpage for Module 3."""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    current_app,
    jsonify,
    flash,
    redirect,
    render_template,
    url_for,
)

from orm_queries import collect_all_analysis_results
from scrape_manager import get_scrape_status, start_data_pull


# Load local environment variables from the ignored .env file.
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


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


def analysis():
    """
    Query PostgreSQL through SQLAlchemy and display the analysis page.

    Every page request retrieves the current database results rather
    than displaying hard-coded values.
    """
    try:
        raw_results = current_app.config.get("QUERY_RESULTS_FN", collect_all_analysis_results)()
        results = build_view_model(raw_results)

        updated_at = datetime.now().strftime(
            "%B %d, %Y at %I:%M:%S %p"
        )

        return render_template(
            "analysis.html",
            results=results,
            updated_at=updated_at,
            scrape_status=current_app.config.get("GET_STATUS_FN", get_scrape_status)(),
        )

    except Exception:
        # Record the full error in the Flask terminal for debugging,
        # while showing the user a concise message.
        current_app.logger.exception(
            "Unable to retrieve the database analysis."
        )

        return render_template(
            "analysis.html",
            results=None,
            updated_at=None,
            scrape_status=current_app.config.get("GET_STATUS_FN", get_scrape_status)(),
        ), 500


def pull_data():
    """Start a pull when idle and report its status as JSON."""
    status = current_app.config.get("GET_STATUS_FN", get_scrape_status)()
    if status["running"]:
        return jsonify(busy=True), 409

    start_pull = current_app.config.get("START_PULL_FN", start_data_pull)
    try:
        if not start_pull():
            return jsonify(busy=True), 409
    except Exception:
        current_app.logger.exception("Data pull failed to start.")
        return jsonify(ok=False), 500

    return jsonify(ok=True), 202


def update_analysis():
    """Refresh analysis only when no data pull is running."""
    status = current_app.config.get("GET_STATUS_FN", get_scrape_status)()
    if status["running"]:
        return jsonify(busy=True), 409

    query_results = current_app.config.get(
        "QUERY_RESULTS_FN", collect_all_analysis_results
    )
    try:
        query_results()
    except Exception:
        current_app.logger.exception("Unable to update analysis.")
        return jsonify(ok=False), 500

    return jsonify(ok=True), 200


def create_app(test_config=None):
    """Create a configurable Flask application."""
    flask_app = Flask(__name__)
    flask_app.config["SECRET_KEY"] = os.getenv(
        "FLASK_SECRET_KEY", "module-4-local-development-key"
    )
    if test_config:
        flask_app.config.update(test_config)

    flask_app.add_url_rule("/", endpoint="analysis", view_func=analysis)
    flask_app.add_url_rule("/analysis", endpoint="analysis_page", view_func=analysis)
    flask_app.add_url_rule(
        "/pull-data", endpoint="pull_data", view_func=pull_data, methods=["POST"]
    )
    flask_app.add_url_rule(
        "/update-analysis",
        endpoint="update_analysis",
        view_func=update_analysis,
        methods=["POST"],
    )
    return flask_app


app = create_app()


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