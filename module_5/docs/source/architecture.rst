Architecture
============

Web and ETL
-----------

app.py provides the Flask factory and routes. GET / and /analysis render
current query results. POST /pull-data starts a background worker and
POST /update-analysis refreshes queries. Busy requests receive HTTP 409.
analysis.js handles JSON responses and reloads the page after success.

scrape_manager coordinates scrape and load_data using a lock to prevent
concurrent pulls. Worker status records completion or failure, and the
lock is released after work. Scraping uses the retained Chrome workflow.
clean.py handles cleaning and deduplication; load_data prepares records
and inserts them transactionally. URL uniqueness prevents duplicates.

Database and security
---------------------

models defines SQLAlchemy models and environment configuration.
orm_queries supplies web analysis, while query_data provides raw SQL
analysis. sql_safety centralizes allowlisted identifiers, composed SQL,
parameter placeholders, and limit validation. Application read results
are bounded to at most 100 rows, with smaller caps for scalar and top-five
queries. Aggregates still examine the underlying relevant records.

setup_database is an explicit administrative schema entry point. The
normal application role has SELECT and INSERT with sequence access;
it cannot create, alter, or drop tables or update or delete records.
Credentials come from environment variables or an ignored .env file.

Packaging and verification
--------------------------

setup.py supports editable installation and a console entry point.
Tests inject services and mock live browser operations. Database tests
use an isolated disposable PostgreSQL database. CI checks lint, the
dependency graph, open-source dependencies, and tests on pushes and PRs.
