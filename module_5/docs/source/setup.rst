Developer setup
===============

Environment
-----------

Use Python 3.13 and a running PostgreSQL server. Run commands from
the repository root.

Create and activate a virtual environment, then install dependencies::

    python3.13 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r module_4/requirements.txt

Database configuration
----------------------

Create a database for the application::

    createdb gradcafe_module4

Configure DATABASE_URL in module_4/.env::

    DATABASE_URL=postgresql:///gradcafe_module4

This local connection uses the current operating-system user.
Adjust the URL for your PostgreSQL credentials and host.
Keep .env out of version control.

Load applicant records
----------------------

Place applicant_data.json in module_4/, then run::

    PYTHONPATH=module_4/src python module_4/src/load_data.py

The loader creates the applicants table if needed and inserts usable
records. Duplicate URLs do not create additional rows.
The dataset is excluded from the public repository.

Run the application
-------------------

Start the Flask development server::

    PYTHONPATH=module_4/src python module_4/src/app.py

Open http://127.0.0.1:5000/analysis in a browser.
Use this server for local development.

Run automated tests
-------------------

Create a separate test database::

    createdb gradcafe_module4_test

Run the marked suite with coverage::

    TEST_DATABASE_URL=postgresql:///gradcafe_module4_test python -m pytest -c module_4/pytest.ini module_4/tests -m "web or buttons or analysis or db or integration"

Database fixtures reset test data. Use a dedicated database whose
name ends in _test. Never point TEST_DATABASE_URL at application data.

Build documentation
-------------------

Generate HTML with warnings treated as errors::

    python -m sphinx -W --keep-going -b html module_4/docs/source module_4/docs/build/html

Open module_4/docs/build/html/index.html to view the documentation.
