"""Run the required GradCafe analyses using raw SQL."""

from psycopg import sql

from load_data import get_connection
from sql_safety import clamp_limit

# Question 1:
# Count records whose term is Fall 2026.
QUESTION_1_SQL = """
SELECT COUNT(*)
FROM applicants
WHERE LOWER(TRIM(term)) = 'fall 2026'
LIMIT 1;
"""


# Question 2:
# Calculate the percentage of applicants classified as International.
QUESTION_2_SQL = """
SELECT
    100.0
    * COUNT(*) FILTER (
        WHERE LOWER(TRIM(us_or_international)) = 'international'
    )
    / NULLIF(
        COUNT(*) FILTER (
            WHERE us_or_international IS NOT NULL
              AND TRIM(us_or_international) <> ''
        ),
        0
    )
FROM applicants
LIMIT 1;
"""


# Question 3:
# Calculate the four averages separately.
QUESTION_3_SQL = """
SELECT
    AVG(gpa),
    AVG(gre),
    AVG(gre_v),
    AVG(gre_aw)
FROM applicants
LIMIT 1;
"""
# Question 4:
# Calculate the average GPA of American applicants for Fall 2026.
QUESTION_4_SQL = """
SELECT AVG(gpa)
FROM applicants
WHERE LOWER(TRIM(term)) = 'fall 2026'
  AND LOWER(TRIM(us_or_international)) = 'american'
  AND gpa IS NOT NULL
LIMIT 1;
"""


# Question 5:
# Calculate the percentage of Fall 2025 entries that are acceptances.
QUESTION_5_SQL = """
SELECT
    100.0
    * COUNT(*) FILTER (
        WHERE LOWER(TRIM(status)) LIKE 'accepted%'
    )
    / NULLIF(COUNT(*), 0)
FROM applicants
WHERE LOWER(TRIM(term)) = 'fall 2025'
LIMIT 1;
"""


# Question 6:
# Calculate the average GPA of accepted Fall 2026 applicants.
QUESTION_6_SQL = """
SELECT AVG(gpa)
FROM applicants
WHERE LOWER(TRIM(term)) = 'fall 2026'
  AND LOWER(TRIM(status)) LIKE 'accepted%'
  AND gpa IS NOT NULL
LIMIT 1;
"""
# Question 7:
# Count applicants who applied to Johns Hopkins University for a
# master's degree in Computer Science.
QUESTION_7_SQL = """
SELECT COUNT(*)
FROM applicants
WHERE (
        program ILIKE '%Johns Hopkins University%'
        OR program ~* '(^|[^[:alnum:]])JHU([^[:alnum:]]|$)'
      )
  AND program ILIKE '%Computer Science%'
  AND LOWER(TRIM(degree)) = 'masters'
LIMIT 1;
"""


# Question 8:
# Count accepted Fall 2026 Computer Science PhD entries from one of
# the four specified universities using the original program field.
QUESTION_8_SQL = """
SELECT COUNT(*)
FROM applicants
WHERE LOWER(TRIM(term)) = 'fall 2026'
  AND LOWER(TRIM(status)) LIKE 'accepted%'
  AND LOWER(TRIM(degree)) = 'phd'
  AND program ILIKE '%Computer Science%'
  AND (
        program ILIKE '%Georgetown University%'
        OR program ILIKE '%Massachusetts Institute of Technology%'
        OR program ~* '(^|[^[:alnum:]])MIT([^[:alnum:]]|$)'
        OR program ILIKE '%Stanford University%'
        OR program ILIKE '%Carnegie Mellon University%'
      )
LIMIT 1;
"""


# Question 9:
# Repeat Question 8 using the LLM-generated program and university
# fields instead of the original combined program field.
QUESTION_9_SQL = """
SELECT COUNT(*)
FROM applicants
WHERE LOWER(TRIM(term)) = 'fall 2026'
  AND LOWER(TRIM(status)) LIKE 'accepted%'
  AND LOWER(TRIM(degree)) = 'phd'
  AND llm_generated_program ILIKE '%Computer Science%'
  AND (
        llm_generated_university ILIKE '%Georgetown University%'
        OR llm_generated_university ILIKE '%George Town University%'
        OR llm_generated_university
            ILIKE '%Massachusetts Institute of Technology%'
        OR llm_generated_university
            ~* '(^|[^[:alnum:]])MIT([^[:alnum:]]|$)'
        OR llm_generated_university ILIKE '%Stanford University%'
        OR llm_generated_university ILIKE '%Carnegie Mellon University%'
      )
LIMIT 1;
"""

# Question 10
# How do Fall 2026 acceptance percentages compare between American
# and international applicants?
QUESTION_10_SQL = """
SELECT
    us_or_international AS applicant_group,
    COUNT(*) AS total_entries,
    COUNT(*) FILTER (
        WHERE LOWER(TRIM(status)) LIKE 'accepted%'
    ) AS accepted_entries,
    ROUND(
        100.0
        * COUNT(*) FILTER (
            WHERE LOWER(TRIM(status)) LIKE 'accepted%'
        )
        / NULLIF(COUNT(*), 0),
        2
    ) AS acceptance_percentage
FROM applicants
WHERE LOWER(TRIM(term)) = 'fall 2026'
  AND LOWER(TRIM(us_or_international))
      IN ('american', 'international')
GROUP BY us_or_international
ORDER BY applicant_group
LIMIT 100;
"""


# Question 11
# Which five universities have the most reported Fall 2026
# acceptances?

QUESTION_11_SQL = """
SELECT
    llm_generated_university AS university,
    COUNT(*) AS accepted_entries
FROM applicants
WHERE LOWER(TRIM(term)) = 'fall 2026'
  AND LOWER(TRIM(status)) LIKE 'accepted%'
  AND llm_generated_university IS NOT NULL
  AND TRIM(llm_generated_university) <> ''
GROUP BY llm_generated_university
ORDER BY accepted_entries DESC, university
LIMIT 5;
"""


ANALYSIS_STATEMENTS = (
    QUESTION_1_SQL,
    QUESTION_2_SQL,
    QUESTION_3_SQL,
    QUESTION_4_SQL,
    QUESTION_5_SQL,
    QUESTION_6_SQL,
    QUESTION_7_SQL,
    QUESTION_8_SQL,
    QUESTION_9_SQL,
    QUESTION_10_SQL,
    QUESTION_11_SQL,
)


def build_analysis_statement(question_number, limit=100):
    """Compose an approved analysis with a separately bound result limit."""
    if not isinstance(question_number, int) or not 1 <= question_number <= 11:
        raise ValueError("Question number must be an integer from 1 to 11.")
    # These templates are fixed source constants, never request-supplied SQL.
    template = ANALYSIS_STATEMENTS[question_number - 1].rsplit("LIMIT", 1)[0].strip()
    inherent_cap = 1 if question_number < 10 else (5 if question_number == 11 else 100)
    # Psycopg requires literal percent signs to be escaped when binding parameters.
    fixed_query = sql.SQL(template.replace("%", "%%"))
    statement = sql.SQL("{query} LIMIT {limit}").format(query=fixed_query, limit=sql.Placeholder())
    return statement, (min(clamp_limit(limit), inherent_cap),)


def collect_raw_sql_results():
    """Execute the analysis queries and return their results."""
    results = {}
    with get_connection() as connection:
        with connection.cursor() as cursor:
            statement, params = build_analysis_statement(1)
            cursor.execute(statement, params)
            results["fall_2026_count"] = cursor.fetchone()[0]
            statement, params = build_analysis_statement(2)
            cursor.execute(statement, params)
            results["percent_international"] = cursor.fetchone()[0]
            statement, params = build_analysis_statement(3)
            cursor.execute(statement, params)
            (
                results["average_gpa"],
                results["average_gre"],
                results["average_gre_v"],
                results["average_gre_aw"],
            ) = cursor.fetchone()
            statement, params = build_analysis_statement(4)
            cursor.execute(statement, params)
            results["average_american_gpa_fall_2026"] = cursor.fetchone()[0]
            statement, params = build_analysis_statement(5)
            cursor.execute(statement, params)
            results["fall_2025_acceptance_percentage"] = cursor.fetchone()[0]
            statement, params = build_analysis_statement(6)
            cursor.execute(statement, params)
            results["average_accepted_gpa_fall_2026"] = cursor.fetchone()[0]
            statement, params = build_analysis_statement(7)
            cursor.execute(statement, params)
            results["jhu_cs_masters_count"] = cursor.fetchone()[0]
            statement, params = build_analysis_statement(8)
            cursor.execute(statement, params)
            results["original_field_count"] = cursor.fetchone()[0]
            statement, params = build_analysis_statement(9)
            cursor.execute(statement, params)
            results["llm_field_count"] = cursor.fetchone()[0]
            results["field_count_difference"] = (
                results["llm_field_count"] - results["original_field_count"]
            )
            statement, params = build_analysis_statement(10)
            cursor.execute(statement, params)
            results["acceptance_by_nationality"] = cursor.fetchall()
            statement, params = build_analysis_statement(11)
            cursor.execute(statement, params)
            results["top_accepted_universities"] = cursor.fetchall()
    return results


def run_raw_sql_queries():
    """Collect SQL results and print their formatted values."""
    results = collect_raw_sql_results()
    print("Question 1")
    print(f"Fall 2026 applicant count: {results['fall_2026_count']:,}")
    print("\nQuestion 2")
    print(f"Percent international: {results['percent_international']:.2f}%")
    print("\nQuestion 3")
    print(f"Average GPA: {results['average_gpa']:.2f}")
    print(f"Average GRE Quantitative: {results['average_gre']:.2f}")
    print(f"Average GRE Verbal: {results['average_gre_v']:.2f}")
    print(f"Average GRE Analytical Writing: {results['average_gre_aw']:.2f}")
    print("\nQuestion 4")
    print(
        "Average GPA of American Fall 2026 applicants: "
        f"{results['average_american_gpa_fall_2026']:.2f}"
    )
    print("\nQuestion 5")
    print(f"Fall 2025 acceptance percentage: {results['fall_2025_acceptance_percentage']:.2f}%")
    print("\nQuestion 6")
    print(
        "Average GPA of accepted Fall 2026 applicants: "
        f"{results['average_accepted_gpa_fall_2026']:.2f}"
    )
    print("\nQuestion 7")
    print(f"Johns Hopkins Computer Science master's count: {results['jhu_cs_masters_count']:,}")
    print("\nQuestion 8")
    print(f"Original-field count: {results['original_field_count']:,}")
    print("\nQuestion 9")
    print(f"Original-field count: {results['original_field_count']:,}")
    print(f"LLM-field count: {results['llm_field_count']:,}")
    print(f"Difference: {results['field_count_difference']:+,}")
    print("\nQuestion 10")
    print(
        "How do Fall 2026 acceptance percentages compare "
        "between American and international applicants?"
    )
    for applicant_group, total_entries, accepted_entries, acceptance_percentage in results[
        "acceptance_by_nationality"
    ]:
        print(
            f"{applicant_group}: {accepted_entries:,} accepted out of "
            f"{total_entries:,} entries ({acceptance_percentage:.2f}%)"
        )
    print("\nQuestion 11")
    print("Which five universities have the most reported Fall 2026 acceptances?")
    for university, accepted_entries in results["top_accepted_universities"]:
        print(f"{university}: {accepted_entries:,}")


if __name__ == "__main__":
    run_raw_sql_queries()
