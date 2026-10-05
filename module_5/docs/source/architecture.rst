Architecture
============

Web layer
---------

app.py provides the Flask application factory and HTTP routes.
The analysis page renders query results through a Jinja template.
analysis.js submits button requests and handles JSON responses.

GET / and GET /analysis display the analysis page.
POST /pull-data starts a background data pull.
POST /update-analysis executes the analysis queries.

Both POST routes return HTTP 409 when a pull is running.
The application factory accepts injected services so tests can
control queries, pull startup, and busy status.

ETL layer
---------

scrape.py collects applicant records and manages saved scraping state.
clean.py validates and deduplicates records in the cleaning workflow.
load_data.py prepares records for PostgreSQL and inserts them within
a transaction.

scrape_manager.py coordinates background scraping and loading.
A lock prevents concurrent pulls. Worker status records completion
or failure, and the lock is released when work finishes.

Database layer
--------------

PostgreSQL stores applicant records in the applicants table.
The unique URL constraint prevents duplicate inserts.

models.py defines the SQLAlchemy model and connection configuration.
orm_queries.py supplies the analysis results used by the Flask page.
query_data.py provides the retained raw SQL analysis utilities.

Data flow
---------

A pull request starts the worker, which calls the scraper and loader.
Loaded records become available to subsequent analysis queries.

An update request executes the analysis queries. After a successful
response, the browser navigates to the analysis page, which queries
and renders the current database results.

Test boundaries
---------------

Unit tests inject controlled services and mock browser operations.
Database and integration tests use an isolated PostgreSQL database.
This verifies application behavior without live scraping.
