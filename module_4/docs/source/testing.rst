Testing guide
=============

Run the suite
-------------

Run from the repository root with the virtual environment active
and PostgreSQL running::

    TEST_DATABASE_URL=postgresql:///gradcafe_module4_test python -m pytest -c module_4/pytest.ini module_4/tests -m "web or buttons or analysis or db or integration"

pytest.ini enables coverage of module_4/src, reports missing statements,
and requires 100 percent statement coverage.

Test markers
------------

Every test carries at least one registered assignment marker:

* web: Flask page responses and rendered HTML.
* buttons: button routes, busy responses, and pull coordination.
* analysis: analysis labels, values, and formatting.
* db: PostgreSQL persistence and database behavior.
* integration: behavior across application layers.

The collection hook rejects tests without an allowed marker.
Strict marker checking also rejects unregistered marker names.

Stable selectors
----------------

Page tests locate the buttons using these HTML attributes:

* data-testid="pull-data-btn"
* data-testid="update-analysis-btn"

BeautifulSoup inspects rendered HTML. Flask's test client sends
requests without starting a development server.

Fixtures and test doubles
-------------------------

Shared fixtures live in tests/conftest.py.

Application tests inject controlled query, status, and pull services
through create_app configuration:

* QUERY_RESULTS_FN supplies analysis results.
* GET_STATUS_FN supplies idle or busy status.
* START_PULL_FN controls pull startup.

Scraper tests mock browser operations and use controlled HTML,
saved state, and temporary files. Tests do not scrape the live website.

PostgreSQL isolation
--------------------

TEST_DATABASE_URL identifies the dedicated test database.
Database fixtures check that its name ends in _test before resetting
the applicants table.

Database tests verify inserts, duplicate prevention, and rollback.
Integration tests exercise pull, query refresh, and rendered output
using real PostgreSQL queries.

Use a disposable test database. Do not configure these tests against
an application database containing data you want to retain.

Coverage evidence and CI
------------------------

coverage_summary.txt stores terminal verification output.
Statement coverage confirms that executable statements were exercised;
it does not prove every possible input or branch is correct.

The root .github/workflows/tests.yml workflow installs dependencies,
starts PostgreSQL, and runs the marked suite with the coverage gate.

actions_success.png records a successful GitHub Actions run.
