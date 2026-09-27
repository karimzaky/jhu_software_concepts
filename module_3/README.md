# Module 3: Database Queries, SQLAlchemy, and Dynamic Webpages

This project loads cleaned GradCafe applicant data into PostgreSQL, analyzes the data using raw SQL and SQLAlchemy ORM, generates a PDF report, and displays the results through a dynamic Flask webpage.

The Flask application can also run the Module 2 scraper in the background, add newly collected records to PostgreSQL, and refresh the analysis without restarting the server.

## Project Files

- `applicant_data.json`: Cleaned and LLM-enriched GradCafe dataset.
- `load_data.py`: Creates the PostgreSQL table and loads new applicant records.
- `query_data.py`: Answers Questions 1-11 using raw SQL.
- `models.py`: Defines the SQLAlchemy `Applicant` model, engine, and session.
- `orm_queries.py`: Performs the analysis using SQLAlchemy ORM.
- `generate_query_results.py`: Generates and validates the SQL analysis PDF.
- `query_results.pdf`: SQL questions, queries, results, and explanations.
- `app.py`: Defines the Flask routes and prepares results for the webpage.
- `scrape_manager.py`: Runs scraping in a background thread and prevents concurrent pulls.
- `scrape.py`: Captures and parses public GradCafe survey pages.
- `clean.py`: Contains Module 2 data-cleaning functions.
- `templates/analysis.html`: Displays the dynamic analysis and application controls.
- `static/style.css`: Styles the Flask analysis page.
- `limitations.pdf`: Discusses important dataset and analysis limitations.
- `screenshots/`: Contains evidence of raw SQL, ORM, and Flask execution.
- `requirements.txt`: Lists the required Python packages.
- `.env.example`: Provides an example database configuration without credentials.
- `github.txt`: Contains the project repository URL.

## Environment Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Database Configuration

PostgreSQL must be installed and running.

Create the project database:

```bash
createdb gradcafe_module3
```

Create a local `.env` file based on `.env.example`:

```text
DB_NAME=gradcafe_module3
DB_USER=your_postgresql_username
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
```

`DB_PASSWORD` may remain blank when the local PostgreSQL configuration does not require a password.

The `.env` file is ignored by Git and must not be committed.

## Load the Data

Run:

```bash
python load_data.py
```

The loader:

- Creates the `applicants` table if it does not exist.
- Converts dates and numeric scores into database-compatible types.
- Converts missing or invalid values to SQL `NULL`.
- Uses each GradCafe URL as a unique record identifier.
- Uses `ON CONFLICT DO NOTHING` to prevent duplicate records.

## Run the Raw SQL Analysis

Run:

```bash
python query_data.py
```

This executes Questions 1-9 and the two original questions using raw SQL through Psycopg.

## Run the SQLAlchemy ORM Analysis

Run:

```bash
python orm_queries.py
```

This repeats Questions 1, 4, 5, 8, 9, and Original Question 1 using SQLAlchemy ORM. The Flask application also uses ORM functions to retrieve all analysis results dynamically.

The ORM analysis does not use raw SQL strings, SQLAlchemy `text()`, or Psycopg cursors.

## Generate the SQL Analysis PDF

Run:

```bash
python generate_query_results.py
```

This creates `query_results.pdf` and validates its page count and required text.

## Run the Flask Application

Start the Flask development server:

```bash
python app.py
```

Open the following address in a web browser:

```text
http://127.0.0.1:5000
```

The page retrieves its current results from PostgreSQL through SQLAlchemy. The displayed values are not hard-coded into the HTML template.

Press `Control+C` in the terminal to stop the development server.

## Pull New Data

The Flask page contains two controls:

- **Pull Data** starts one background scraping operation.
- **Update Analysis** re-queries PostgreSQL and displays the latest completed results.

The Pull Data workflow:

1. Determines the current number of JSON records.
2. Requests one additional GradCafe result page.
3. Uses the Module 2 scraper to capture and parse the page.
4. Saves the new unique records to `applicant_data.json`.
5. Loads the new records into PostgreSQL.
6. Prevents another scrape from starting while one is already running.
7. Displays the completion time and number of inserted records.

Google Chrome must be open because the scraper uses AppleScript to capture rendered GradCafe HTML. Chrome must also have **Allow JavaScript from Apple Events** enabled.

When testing locally, the Flask page may be opened in Safari while Chrome remains available for GradCafe navigation. This prevents the scraper from replacing the Flask browser tab.

Newly scraped records may have `NULL` values in the LLM-generated columns because the web scraper does not run the separate Module 2 LLM enrichment process.

## Update the Analysis

Clicking **Update Analysis** does not start the scraper. It refreshes the page and executes the ORM analysis against the latest completed PostgreSQL data.

If a data pull is still running, the page reports that the displayed results reflect the latest completed database update.

## Raw SQL and SQLAlchemy Comparison

The following example answers Question 4: What is the average GPA of American applicants who applied for Fall 2026?

### Raw SQL

```sql
SELECT AVG(gpa)
FROM applicants
WHERE LOWER(TRIM(term)) = 'fall 2026'
  AND LOWER(TRIM(us_or_international)) = 'american'
  AND gpa IS NOT NULL;
```

### SQLAlchemy ORM

```python
statement = (
    select(func.avg(Applicant.gpa))
    .where(
        func.lower(func.trim(Applicant.term)) == "fall 2026",
        func.lower(
            func.trim(Applicant.us_or_international)
        ) == "american",
        Applicant.gpa.is_not(None),
    )
)

average_gpa = session.scalar(statement)
```

Raw SQL is concise and gives the developer direct control over the exact database query, which can make database-specific behavior easier to inspect and debug. SQLAlchemy expresses the same analysis through the `Applicant` model, reducing reliance on string-based table and column names and making the query easier to reuse in the Flask application. The ORM can improve portability and make refactoring safer when the Python application grows. Raw SQL remains useful when precise control, database-specific features, or direct query optimization are more important than abstraction.

## Data Limitations

GradCafe entries are anonymous and self-reported. They do not represent all applicants or official university admission statistics. Missing values, inconsistent text, reporting bias, unusual numeric values, and differences between raw and LLM-generated fields can affect the analysis.

See `limitations.pdf` for the full limitations discussion.