# Module 5 — Secure GradCafe Development

Karim Zaky — JHU Modern Software Concepts in Python

This module extends the GradCafe application with SQL composition,
parameter binding, bounded reads, least-privilege database access,
static analysis, dependency visualization, and reproducible installation.

## Fresh Install

Use Python 3.13 and run these commands from `module_5/`.
PostgreSQL and Graphviz are external tools, installed separately.
On macOS, use Postgres.app and `brew install graphviz`.
Live scraping also requires macOS and Google Chrome.

### pip + venv

```bash
python3.13 -m venv .venv-pip
.venv-pip/bin/python -m pip install --upgrade pip
.venv-pip/bin/python -m pip install -r requirements.txt
.venv-pip/bin/python -m pip install --no-deps -e .
.venv-pip/bin/python -m pip check
```

### uv

```bash
uv venv --python python3.13 .venv-uv
uv pip install --python .venv-uv/bin/python -r requirements.txt
uv pip install --python .venv-uv/bin/python --no-deps -e .
uv pip check --python .venv-uv/bin/python
```

Both methods install the source in editable mode. This keeps Flask templates,
static files, and local data paths beside the source while making the modules
importable without manually setting PYTHONPATH. These instructions target
editable development installs; standalone wheel deployment is not verified.
Requirements specify compatible version ranges, rather than an exact lockfile.
For an exact uv sync, first compile a complete lockfile:

```bash
uv pip compile --python .venv-uv/bin/python requirements.txt -o requirements.lock
uv pip sync --python .venv-uv/bin/python requirements.lock
uv pip install --python .venv-uv/bin/python --no-deps -e .
```

## Database Configuration

Copy `.env.example` to `.env` and enter your local database credentials.
Do not commit `.env`. DATABASE_URL, when set, overrides the DB_* settings.
The application database is `gradcafe_module5`, and its application role is
`gradcafe_module5_app`. The role has CONNECT, schema USAGE, table SELECT and
INSERT, and sequence USAGE. It does not own the table and cannot create,
alter, drop, update, or delete application tables or records.
INSERT is necessary because Pull Data saves newly scraped records.
Verification evidence is recorded in `database_privileges.txt`.

For a new database, an administrator must create the schema explicitly:

```bash
DATABASE_URL=postgresql:///gradcafe_module5 .venv-pip/bin/python src/setup_database.py
```

Grant the application permissions separately as an administrator. Then load
`applicant_data.json` using the configured application role:

```bash
.venv-pip/bin/python src/load_data.py
```

The regular loader does not create tables. URL uniqueness prevents duplicate
inserts. Datasets and browser captures are excluded from version control.

## Run the Application

```bash
.venv-pip/bin/gradcafe-module5
```

For uv, use `.venv-uv/bin/gradcafe-module5` instead.
Open http://127.0.0.1:5000/analysis. Stop the server with Control+C.
GET `/` and `/analysis` display database analysis. POST `/pull-data` starts
collection; POST `/update-analysis` refreshes analysis. Busy requests receive
HTTP 409. Browser operations are mocked during automated tests.

## Tests and Pylint

Create a separate disposable test database, if it does not already exist:

```bash
createdb gradcafe_module5_test
```

```bash
TEST_DATABASE_URL=postgresql:///gradcafe_module5_test .venv-pip/bin/python -m pytest
.venv-pip/bin/python -m pylint src --fail-under=10
```

Use the corresponding `.venv-uv/bin/python` to verify the alternate environment.
Fixtures reset the test table and require a database name ending in `_test`.
The test suite uses web, buttons, analysis, db, and integration markers.
`pytest.ini` requires 100% statement coverage of src. The latest verified
pre-packaging run passed 167 tests with 100% coverage and Pylint 10.00/10.
Statement coverage does not establish exhaustive branch or input coverage.

## SQL Safety

Dynamic identifiers use psycopg Identifier, and values use placeholders with
separate execution parameters. Application read statements contain LIMIT;
requested limits are clamped to 1–100 and further restricted where appropriate.
DDL and INSERT statements do not use a SELECT-style LIMIT clause.
Tests exercise malicious input, identifier allowlists, and bounded SQL/ORM reads.

## Dependency Graph

```bash
PYTHONPATH=src .venv-pip/bin/python -m pydeps src/app.py --noshow -T svg -o dependency.svg
```

The graph starts at app.py and follows application imports; it does not include
all standalone report or setup entry points. Flask supports the web interface,
orm_queries and models support SQLAlchemy analysis, scrape_manager coordinates
scrape and load_data, and sql_safety centralizes shared query safety helpers.

## Documentation and Remaining Evidence

The existing published Module 4 documentation remains available at
https://karim-zaky-module-4-gradcafe.readthedocs.io/en/latest/.
Module 5 documentation and final scan/CI evidence are still being completed.

```bash
.venv-pip/bin/python -m sphinx -E -W --keep-going -b html docs/source docs/build/html
```

The final report will cover installation, packaging, dependency relationships,
SQL defenses, permissions, and CI. Snyk scan results and workflow evidence will
be added after verification.

## Repository

GitHub: https://github.com/karimzaky/jhu_software_concepts

SSH URL: `git@github.com:karimzaky/jhu_software_concepts.git`
