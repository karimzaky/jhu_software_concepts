Testing and security verification
=================================

Run from module_5 with PostgreSQL running. Create a separate disposable
test database if it does not already exist::

    createdb gradcafe_module5_test
    TEST_DATABASE_URL=postgresql:///gradcafe_module5_test .venv-pip/bin/python -m pytest

Use the corresponding .venv-uv/bin/python for the alternate environment.
Fixtures reject database names that do not end in _test and reset the
test table. Do not use the application database for tests.

pytest.ini enables strict markers and requires 100 percent statement
coverage of src. Every test carries a web, buttons, analysis, db, or
integration marker. Tests inject services and mock browser operations;
database integration tests execute real SQL against the test database.

SQL safety tests exercise malicious values, identifier allowlists,
parameter binding, malformed limits, and bounded raw SQL and ORM reads.
Schema setup tests verify that creation is an explicit administrative
operation rather than part of ordinary data loading.

Local verification
------------------

Both fresh pip and uv environments passed 167 tests, reached 100 percent
statement coverage, and achieved Pylint 10.00/10::

    .venv-pip/bin/python -m pylint src --fail-under=10

Statement coverage does not establish exhaustive branch or input coverage.
Narrow source-level lint exceptions explain intentional framework and
error-boundary patterns.

Dependency graph
----------------

::

    PYTHONPATH=src .venv-pip/bin/python -m pydeps src/app.py --noshow -T svg -o dependency.svg

Graphviz must be on PATH. The graph follows imports from the application
entry point and does not include every standalone utility.

Snyk and CI evidence
--------------------

::

    snyk test --file=requirements.txt --command=.venv-pip/bin/python

The successful CI scan tested 53 dependencies and reported zero issues.
The screenshot is snyk-analysis.png. Local scan attempts previously
failed in service processing and did not produce vulnerability results.

The root .github/workflows/ci.yml checks Pylint, graph generation and
validation, Snyk, and pytest. It uses a PostgreSQL 18 test service and
SNYK_TOKEN from repository Actions secrets. actions_success.png records
the successful run. CI uploads pylint_ci.txt, dependency.svg,
snyk_ci.txt, and coverage_summary.txt as verification artifacts.
