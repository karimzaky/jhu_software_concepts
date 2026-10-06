"""Compose allowlisted applicant SQL and bound read-result limits."""

from psycopg import sql

MAX_QUERY_LIMIT = 100
APPLICANT_COLUMNS = (
    "program",
    "comments",
    "date_added",
    "url",
    "status",
    "term",
    "us_or_international",
    "gpa",
    "gre",
    "gre_v",
    "gre_aw",
    "degree",
    "llm_generated_program",
    "llm_generated_university",
)


def clamp_limit(value=MAX_QUERY_LIMIT):
    """Clamp integer limits to 1–100; malformed values get the smallest limit."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return 1
    try:
        requested = int(value)
    except ValueError:
        return 1
    return max(1, min(requested, MAX_QUERY_LIMIT))


def build_insert_statement(table="applicants", columns=APPLICANT_COLUMNS):
    """Compose an insert using approved identifiers and value placeholders."""
    if table != "applicants" or tuple(columns) != APPLICANT_COLUMNS:
        raise ValueError("Only the approved applicant table and columns are allowed.")
    return sql.SQL(
        "INSERT INTO {table} ({columns}) VALUES ({values}) ON CONFLICT ({url}) DO NOTHING"
    ).format(
        table=sql.Identifier(table),
        columns=sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        values=sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        url=sql.Identifier("url"),
    )


def build_count_statement(limit=1):
    """Build a bounded count query separately from its execution parameters."""
    statement = sql.SQL("SELECT COUNT(*) FROM {table} LIMIT {limit}").format(
        table=sql.Identifier("applicants"),
        limit=sql.Placeholder(),
    )
    return statement, (clamp_limit(limit),)
