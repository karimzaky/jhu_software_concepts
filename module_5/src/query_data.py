"""Run the required GradCafe analyses using raw SQL."""


from load_data import get_connection


# Question 1:
# Count records whose term is Fall 2026.
QUESTION_1_SQL = """
SELECT COUNT(*)
FROM applicants
WHERE LOWER(TRIM(term)) = 'fall 2026';
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
FROM applicants;
"""


# Question 3:
# Calculate the four averages separately.
QUESTION_3_SQL = """
SELECT
    AVG(gpa),
    AVG(gre),
    AVG(gre_v),
    AVG(gre_aw)
FROM applicants;
"""
# Question 4:
# Calculate the average GPA of American applicants for Fall 2026.
QUESTION_4_SQL = """
SELECT AVG(gpa)
FROM applicants
WHERE LOWER(TRIM(term)) = 'fall 2026'
  AND LOWER(TRIM(us_or_international)) = 'american'
  AND gpa IS NOT NULL;
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
WHERE LOWER(TRIM(term)) = 'fall 2025';
"""


# Question 6:
# Calculate the average GPA of accepted Fall 2026 applicants.
QUESTION_6_SQL = """
SELECT AVG(gpa)
FROM applicants
WHERE LOWER(TRIM(term)) = 'fall 2026'
  AND LOWER(TRIM(status)) LIKE 'accepted%'
  AND gpa IS NOT NULL;
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
  AND LOWER(TRIM(degree)) = 'masters';
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
      );
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
      );
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
ORDER BY applicant_group;
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

def run_raw_sql_queries():
    """Execute the raw SQL queries and print their formatted results."""

    # Open a connection to the PostgreSQL database.
    # The connection settings come from the ignored .env file.
    with get_connection() as connection:

        # Create a cursor that can send SQL statements to PostgreSQL
        # and retrieve the resulting rows.
        with connection.cursor() as cursor:

            # Execute Question 1 and retrieve its single count.
            cursor.execute(QUESTION_1_SQL)
            fall_2026_count = cursor.fetchone()[0]

            # Execute Question 2 and retrieve its calculated percentage.
            cursor.execute(QUESTION_2_SQL)
            percent_international = cursor.fetchone()[0]

            # Execute Question 3.
            # The returned row contains four average values in the same
            # order in which they appear in the SELECT statement.
            cursor.execute(QUESTION_3_SQL)
            average_gpa, average_gre, average_gre_v, average_gre_aw = (
                cursor.fetchone()
            )
                        # Execute Question 4 and retrieve the average GPA for
            # American applicants who applied for Fall 2026.
            cursor.execute(QUESTION_4_SQL)
            average_american_gpa_fall_2026 = cursor.fetchone()[0]

            # Execute Question 5 and retrieve the Fall 2025
            # acceptance percentage.
            cursor.execute(QUESTION_5_SQL)
            fall_2025_acceptance_percentage = cursor.fetchone()[0]

            # Execute Question 6 and retrieve the average GPA for
            # accepted Fall 2026 applicants.
            cursor.execute(QUESTION_6_SQL)
            average_accepted_gpa_fall_2026 = cursor.fetchone()[0]

                        # Execute Question 7 and retrieve the Johns Hopkins
            # Computer Science master's applicant count.
            cursor.execute(QUESTION_7_SQL)
            jhu_cs_masters_count = cursor.fetchone()[0]

            # Execute Question 8 using the original program field.
            cursor.execute(QUESTION_8_SQL)
            original_field_count = cursor.fetchone()[0]

            # Execute Question 9 using the LLM-generated fields.
            cursor.execute(QUESTION_9_SQL)
            llm_field_count = cursor.fetchone()[0]

            # A positive value means the LLM fields found more records.
            # A negative value means they found fewer records.
            field_count_difference = (
                llm_field_count - original_field_count
            )

            # Execute Question 10.
            cursor.execute(QUESTION_10_SQL)
            acceptance_by_nationality = cursor.fetchall()

            # Execute Question 11.
            cursor.execute(QUESTION_11_SQL)
            top_accepted_universities = cursor.fetchall()


    # Display counts as whole numbers with comma separators.
    print("Question 1")
    print(f"Fall 2026 applicant count: {fall_2026_count:,}")

    # Display percentages with exactly two decimal places and a % sign.
    print("\nQuestion 2")
    print(f"Percent international: {percent_international:.2f}%")

    # Display each average with exactly two decimal places.
    print("\nQuestion 3")
    print(f"Average GPA: {average_gpa:.2f}")
    print(f"Average GRE Quantitative: {average_gre:.2f}")
    print(f"Average GRE Verbal: {average_gre_v:.2f}")
    print(f"Average GRE Analytical Writing: {average_gre_aw:.2f}")

        # Display the Question 4 average with two decimal places.
    print("\nQuestion 4")
    print(
        "Average GPA of American Fall 2026 applicants: "
        f"{average_american_gpa_fall_2026:.2f}"
    )

    # Display the Question 5 percentage with two decimal places.
    print("\nQuestion 5")
    print(
        "Fall 2025 acceptance percentage: "
        f"{fall_2025_acceptance_percentage:.2f}%"
    )

    # Display the Question 6 average with two decimal places.
    print("\nQuestion 6")
    print(
        "Average GPA of accepted Fall 2026 applicants: "
        f"{average_accepted_gpa_fall_2026:.2f}"
    )

        # Question 7 requires a whole-number count.
    print("\nQuestion 7")
    print(
        "Johns Hopkins Computer Science master's count: "
        f"{jhu_cs_masters_count:,}"
    )

    # Question 8 reports the count obtained from the original field.
    print("\nQuestion 8")
    print(f"Original-field count: {original_field_count:,}")

    # Question 9 reports both counts and their signed difference.
    # The + format displays positive values with a plus sign,
    # matching the assignment's example.
    print("\nQuestion 9")
    print(f"Original-field count: {original_field_count:,}")
    print(f"LLM-field count: {llm_field_count:,}")
    print(f"Difference: {field_count_difference:+,}")

        # Print each nationality group's Fall 2026 acceptance results.
    print("\nQuestion 10")
    print(
        "How do Fall 2026 acceptance percentages compare between "
        "American and international applicants?"
    )

    for (
        applicant_group,
        total_entries,
        accepted_entries,
        acceptance_percentage,
    ) in acceptance_by_nationality:
        print(
            f"{applicant_group}: "
            f"{accepted_entries:,} accepted out of "
            f"{total_entries:,} entries "
            f"({acceptance_percentage:.2f}%)"
        )

    # Print the five universities with the most reported
    # Fall 2026 acceptances.
    print("\nQuestion 11")
    print(
        "Which five universities have the most reported "
        "Fall 2026 acceptances?"
    )

    for university, accepted_entries in top_accepted_universities:
        print(f"{university}: {accepted_entries:,}")

if __name__ == "__main__":
    run_raw_sql_queries()
