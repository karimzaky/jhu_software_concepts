# Module 4 — GradCafe Testing and Documentation

Karim Zaky — JHU Modern Software Concepts in Python

This project extends the Module 3 GradCafe application with automated
tests, configurable Flask services, PostgreSQL integration tests,
continuous integration, and published Sphinx documentation.

## Documentation

https://karim-zaky-module-4-gradcafe.readthedocs.io/en/latest/

The documentation includes developer setup, architecture, an autodoc
API reference, and a testing guide.

## Setup

Use Python 3.13 and a running PostgreSQL server.
Run all commands below from the repository root.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r module_4/requirements.txt
```

An existing compatible virtual environment can also be used.

## PostgreSQL configuration

Create an application database:

```bash
createdb gradcafe_module4
```

Create `module_4/.env` and configure the connection:

```text
DATABASE_URL=postgresql:///gradcafe_module4
```

This local URL uses the current operating-system user. Adjust it for
your database host and credentials. DATABASE_URL takes precedence over
the legacy DB_* settings shown in `.env.example`.

The `.env` file is excluded from version control.

Place `applicant_data.json` in `module_4/`, then load it:

```bash
PYTHONPATH=module_4/src python module_4/src/load_data.py
```

The loader creates the applicants table if needed. Its unique URL
constraint prevents duplicate records. The dataset, captured pages,
and scraping state are excluded from the public repository.

## Run the application

```bash
PYTHONPATH=module_4/src python module_4/src/app.py
```

Open http://127.0.0.1:5000/analysis.

- GET `/` and `/analysis` render applicant analysis.
- POST `/pull-data` starts a background pull and returns JSON.
- POST `/update-analysis` executes the analysis queries and returns JSON.
- Both POST routes return HTTP 409 with a busy response while a pull runs.

The browser handles button responses and reloads the analysis page
after a successful request. Live scraping uses the retained macOS
Chrome/AppleScript workflow; automated tests mock browser operations.

## Run tests

Create a separate, disposable test database:

```bash
createdb gradcafe_module4_test
```

Run the required marked suite:

```bash
TEST_DATABASE_URL=postgresql:///gradcafe_module4_test python -m pytest -c module_4/pytest.ini module_4/tests -m "web or buttons or analysis or db or integration"
```

Fixtures reset the test table and require a database name ending in
`_test`. Never use an application database containing data you want
to retain.

Registered markers are `web`, `buttons`, `analysis`, `db`, and
`integration`. Every test must carry an allowed marker.

The suite verifies page content, button responses, busy behavior,
analysis formatting, database inserts, duplicates, rollback,
integration flows, and utility behavior without live scraping.

`pytest.ini` enforces 100% statement coverage of `module_4/src`.
The recorded verification run passed 116 tests with 100% coverage.
Statement coverage does not establish exhaustive input or branch coverage.

Evidence:
- `coverage_summary.txt`: saved test and coverage output.
- `actions_success.png`: successful GitHub Actions screenshot.
- `.github/workflows/tests.yml` at repository root: PostgreSQL CI workflow.

## Build and view documentation locally

```bash
python -m sphinx -E -W --keep-going -b html module_4/docs/source module_4/docs/build/html
```

Open `module_4/docs/build/html/index.html`.
Documentation sources are in `module_4/docs/source/`.
Generated HTML is included under `module_4/docs/build/html/`.

The root `.readthedocs.yaml` configures the published build.

## Repository

GitHub: https://github.com/karimzaky/jhu_software_concepts

SSH URL: `git@github.com:karimzaky/jhu_software_concepts.git`
