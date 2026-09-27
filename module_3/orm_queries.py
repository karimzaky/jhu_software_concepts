"""Repeat selected Module 3 analyses using SQLAlchemy ORM."""

from sqlalchemy import func, or_, select

from models import Applicant, SessionLocal


def get_question_1(session):
    """
    Return the number of Fall 2026 entries.

    SQLAlchemy builds the SQL statement from the Applicant model.
    """
    statement = (
        select(func.count(Applicant.p_id))
        .where(
            func.lower(func.trim(Applicant.term)) == "fall 2026"
        )
    )

    return session.scalar(statement)


def get_question_4(session):
    """
    Return the average GPA of American Fall 2026 applicants.

    SQL AVG automatically ignores NULL GPA values.
    """
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

    return session.scalar(statement)


def get_question_5(session):
    """
    Return the percentage of Fall 2025 entries that are acceptances.

    The main WHERE condition defines the denominator as all Fall 2025
    entries. The filtered count defines the acceptance numerator.
    """
    accepted_condition = func.lower(
        func.trim(Applicant.status)
    ).like("accepted%")

    accepted_count = func.count(Applicant.p_id).filter(
        accepted_condition
    )

    total_count = func.count(Applicant.p_id)

    percentage_expression = (
        100.0
        * accepted_count
        / func.nullif(total_count, 0)
    )

    statement = (
        select(percentage_expression)
        .where(
            func.lower(func.trim(Applicant.term)) == "fall 2025"
        )
    )

    return session.scalar(statement)


def original_university_conditions():
    """
    Return the university conditions used with the original program field.

    The regular-expression operator recognizes MIT as a standalone
    abbreviation. This remains an SQLAlchemy expression and does not use
    handwritten SQL through text().
    """
    return or_(
        Applicant.program.ilike("%Georgetown University%"),
        Applicant.program.ilike(
            "%Massachusetts Institute of Technology%"
        ),
        Applicant.program.op("~*")(
            r"(^|[^[:alnum:]])MIT([^[:alnum:]]|$)"
        ),
        Applicant.program.ilike("%Stanford University%"),
        Applicant.program.ilike("%Carnegie Mellon University%"),
    )


def llm_university_conditions():
    """
    Return university conditions for the LLM-generated university field.

    Both Georgetown and the observed George Town variation are included.
    """
    return or_(
        Applicant.llm_generated_university.ilike(
            "%Georgetown University%"
        ),
        Applicant.llm_generated_university.ilike(
            "%George Town University%"
        ),
        Applicant.llm_generated_university.ilike(
            "%Massachusetts Institute of Technology%"
        ),
        Applicant.llm_generated_university.op("~*")(
            r"(^|[^[:alnum:]])MIT([^[:alnum:]]|$)"
        ),
        Applicant.llm_generated_university.ilike(
            "%Stanford University%"
        ),
        Applicant.llm_generated_university.ilike(
            "%Carnegie Mellon University%"
        ),
    )


def get_question_8(session):
    """
    Return the Question 8 count using the original program field.

    Every expression passed to where() must be true for a record to
    contribute to the count.
    """
    statement = (
        select(func.count(Applicant.p_id))
        .where(
            func.lower(func.trim(Applicant.term)) == "fall 2026",
            func.lower(
                func.trim(Applicant.status)
            ).like("accepted%"),
            func.lower(func.trim(Applicant.degree)) == "phd",
            Applicant.program.ilike("%Computer Science%"),
            original_university_conditions(),
        )
    )

    return session.scalar(statement)


def get_question_9(session):
    """
    Return the Question 9 count using the LLM-generated fields.

    Term, status, and degree remain based on the original downloaded
    fields, as required by the assignment.
    """
    statement = (
        select(func.count(Applicant.p_id))
        .where(
            func.lower(func.trim(Applicant.term)) == "fall 2026",
            func.lower(
                func.trim(Applicant.status)
            ).like("accepted%"),
            func.lower(func.trim(Applicant.degree)) == "phd",
            Applicant.llm_generated_program.ilike(
                "%Computer Science%"
            ),
            llm_university_conditions(),
        )
    )

    return session.scalar(statement)


def get_original_question(session):
    """
    Compare Fall 2026 acceptance percentages for American and
    international applicants.

    GROUP BY returns one result row for each nationality group.
    """
    accepted_condition = func.lower(
        func.trim(Applicant.status)
    ).like("accepted%")

    accepted_count = func.count(Applicant.p_id).filter(
        accepted_condition
    )

    total_count = func.count(Applicant.p_id)

    acceptance_percentage = (
        100.0
        * accepted_count
        / func.nullif(total_count, 0)
    ).label("acceptance_percentage")

    statement = (
        select(
            Applicant.us_or_international.label(
                "applicant_group"
            ),
            total_count.label("total_entries"),
            accepted_count.label("accepted_entries"),
            acceptance_percentage,
        )
        .where(
            func.lower(
                func.trim(Applicant.term)
            ) == "fall 2026",
            func.lower(
                func.trim(Applicant.us_or_international)
            ).in_(["american", "international"]),
        )
        .group_by(Applicant.us_or_international)
        .order_by(Applicant.us_or_international)
    )

    return session.execute(statement).all()


def collect_orm_results():
    """
    Execute all required ORM analyses and return their results.

    Keeping the query logic in reusable functions allows the Flask
    application to import these functions later.
    """
    with SessionLocal() as session:
        question_1 = get_question_1(session)
        question_4 = get_question_4(session)
        question_5 = get_question_5(session)
        question_8 = get_question_8(session)
        question_9 = get_question_9(session)
        original_question = get_original_question(session)

    return {
        "question_1": question_1,
        "question_4": question_4,
        "question_5": question_5,
        "question_8": question_8,
        "question_9": question_9,
        "original_question": original_question,
    }


def print_orm_results(results):
    """Print the ORM results using the assignment's required formats."""
    print("Question 1")
    print(
        "Fall 2026 applicant count: "
        f"{results['question_1']:,}"
    )

    print("\nQuestion 4")
    print(
        "Average GPA of American Fall 2026 applicants: "
        f"{results['question_4']:.2f}"
    )

    print("\nQuestion 5")
    print(
        "Fall 2025 acceptance percentage: "
        f"{results['question_5']:.2f}%"
    )

    print("\nQuestion 8")
    print(
        "Original-field count: "
        f"{results['question_8']:,}"
    )

    difference = (
        results["question_9"] - results["question_8"]
    )

    print("\nQuestion 9")
    print(
        "Original-field count: "
        f"{results['question_8']:,}"
    )
    print(
        "LLM-field count: "
        f"{results['question_9']:,}"
    )
    print(f"Difference: {difference:+,}")

    print("\nOriginal Question")
    print(
        "How do Fall 2026 acceptance percentages compare "
        "between American and international applicants?"
    )

    for row in results["original_question"]:
        print(
            f"{row.applicant_group}: "
            f"{row.accepted_entries:,} accepted out of "
            f"{row.total_entries:,} entries "
            f"({row.acceptance_percentage:.2f}%)"
        )


def main():
    """Collect and display the required SQLAlchemy ORM analyses."""
    results = collect_orm_results()
    print_orm_results(results)


# Run the ORM analysis only when this file is executed directly.
if __name__ == "__main__":
    main()