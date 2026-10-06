Developer setup
===============

Run all commands from module_5 using Python 3.13. PostgreSQL must be
running. Graphviz is an external tool; on macOS install it with
``brew install graphviz``. Live scraping requires macOS and Chrome.

Fresh pip installation
----------------------

::

    python3.13 -m venv .venv-pip
    .venv-pip/bin/python -m pip install -r requirements.txt
    .venv-pip/bin/python -m pip install --no-deps -e .
    .venv-pip/bin/python -m pip check

Fresh uv installation
---------------------

::

    uv venv --python python3.13 .venv-uv
    uv pip install --python .venv-uv/bin/python -r requirements.txt
    uv pip install --python .venv-uv/bin/python --no-deps -e .
    uv pip check --python .venv-uv/bin/python

Both paths use editable installs. Requirements use compatible version
ranges rather than an exact dependency lock.

Database configuration
----------------------

Copy .env.example to .env and set DB_NAME, DB_USER, DB_PASSWORD, DB_HOST,
and DB_PORT. DATABASE_URL overrides the separate settings when supplied.
Do not commit .env. Use gradcafe_module5 and the restricted role
gradcafe_module5_app.

For a new database, an administrator creates the database and schema::

    createdb gradcafe_module5
    DATABASE_URL=postgresql:///gradcafe_module5 .venv-pip/bin/python src/setup_database.py

The administrator separately creates the application role and grants
CONNECT, schema USAGE, table SELECT and INSERT, and sequence USAGE.
The SQL and rationale are recorded in module_5_report.pdf. The normal
loader does not create tables. Place applicant_data.json in module_5,
then load records using the configured application role::

    .venv-pip/bin/python src/load_data.py

Duplicate URLs do not create additional rows. Datasets are excluded
from version control.

Run the application
-------------------

::

    .venv-pip/bin/gradcafe-module5

For uv use .venv-uv/bin/gradcafe-module5. Open
http://127.0.0.1:5000/analysis and stop the server with Control+C.

Build documentation
-------------------

::

    .venv-pip/bin/python -m sphinx -E -W --keep-going -b html docs/source docs/build/html

Open docs/build/html/index.html. The repository-root Read the Docs
configuration continues to publish the existing Module 4 documentation.
