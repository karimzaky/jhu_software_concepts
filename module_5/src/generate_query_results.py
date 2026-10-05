"""Generate and validate query_results.pdf for Module 3."""

from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from load_data import get_connection
from query_data import (
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


# Store the PDF in the same module_3 folder as this script.
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "query_results.pdf"


def collect_results():
    """
    Execute all 11 SQL queries and return their results.

    Questions 1-9 return one row each.
    Questions 10 and 11 return multiple rows, so they use fetchall().
    """
    results = {}

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(QUESTION_1_SQL)
            results["q1"] = cursor.fetchone()[0]

            cursor.execute(QUESTION_2_SQL)
            results["q2"] = cursor.fetchone()[0]

            cursor.execute(QUESTION_3_SQL)
            results["q3"] = cursor.fetchone()

            cursor.execute(QUESTION_4_SQL)
            results["q4"] = cursor.fetchone()[0]

            cursor.execute(QUESTION_5_SQL)
            results["q5"] = cursor.fetchone()[0]

            cursor.execute(QUESTION_6_SQL)
            results["q6"] = cursor.fetchone()[0]

            cursor.execute(QUESTION_7_SQL)
            results["q7"] = cursor.fetchone()[0]

            cursor.execute(QUESTION_8_SQL)
            results["q8"] = cursor.fetchone()[0]

            cursor.execute(QUESTION_9_SQL)
            results["q9"] = cursor.fetchone()[0]

            cursor.execute(QUESTION_10_SQL)
            results["q10"] = cursor.fetchall()

            cursor.execute(QUESTION_11_SQL)
            results["q11"] = cursor.fetchall()

    return results


def create_styles():
    """Create the text styles used throughout the PDF."""
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="DocumentTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#17365D"),
            spaceAfter=16,
        )
    )

    styles.add(
        ParagraphStyle(
            name="DocumentSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#444444"),
            spaceAfter=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="QuestionHeading",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#17365D"),
            spaceAfter=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionLabel",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#2F5597"),
            spaceBefore=7,
            spaceAfter=5,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyTextCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResultText",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1F1F1F"),
            backColor=colors.HexColor("#EAF2F8"),
            borderColor=colors.HexColor("#9FBAD0"),
            borderWidth=0.6,
            borderPadding=7,
            spaceAfter=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SQLText",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=7.3,
            leading=9.2,
            leftIndent=5,
            rightIndent=5,
            backColor=colors.HexColor("#F4F4F4"),
            borderColor=colors.HexColor("#BBBBBB"),
            borderWidth=0.5,
            borderPadding=7,
            spaceAfter=10,
        )
    )

    return styles


def paragraph_text(text):
    """
    Escape characters that ReportLab treats as markup and preserve
    line breaks using HTML break tags.
    """
    return escape(str(text)).replace("\n", "<br/>")


def format_sql(sql):
    """Prepare a multiline SQL statement for safe PDF display."""
    return paragraph_text(sql.strip())


def format_question_10(rows):
    """Format the grouped nationality comparison for the PDF."""
    lines = []

    for group, total, accepted, percentage in rows:
        lines.append(
            f"{group}: {accepted:,} accepted out of "
            f"{total:,} entries ({percentage:.2f}%)"
        )

    return "\n".join(lines)


def format_question_11(rows):
    """Format the five university rows for the PDF."""
    return "\n".join(
        f"{university}: {accepted_entries:,}"
        for university, accepted_entries in rows
    )


def add_page_number(canvas, document):
    """Add a page number to the bottom-right corner of every page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawRightString(
        letter[0] - 0.55 * inch,
        0.35 * inch,
        f"Page {document.page}",
    )
    canvas.restoreState()


def add_question(
    story,
    styles,
    number,
    question,
    result,
    sql,
    explanation,
    add_page_break=True,
):
    """Add one complete question section to the PDF."""
    story.append(
        Paragraph(
            f"Question {number}",
            styles["QuestionHeading"],
        )
    )

    story.append(Paragraph("Question", styles["SectionLabel"]))
    story.append(
        Paragraph(
            paragraph_text(question),
            styles["BodyTextCustom"],
        )
    )

    story.append(Paragraph("Final Result", styles["SectionLabel"]))
    story.append(
        Paragraph(
            paragraph_text(result),
            styles["ResultText"],
        )
    )

    story.append(Paragraph("SQL Query", styles["SectionLabel"]))
    story.append(
        Paragraph(
            format_sql(sql),
            styles["SQLText"],
        )
    )

    story.append(Paragraph("Explanation", styles["SectionLabel"]))
    story.append(
        Paragraph(
            paragraph_text(explanation),
            styles["BodyTextCustom"],
        )
    )

    if add_page_break:
        story.append(PageBreak())


def build_pdf(results):
    """Build query_results.pdf with all questions and explanations."""
    styles = create_styles()

    document = SimpleDocTemplate(
        str(OUTPUT_FILE),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="Module 3 SQL Query Analysis",
        author="Karim Zaky",
    )

    story = []

    # Title page content.
    story.append(
        Paragraph(
            "Module 3 SQL Query Analysis",
            styles["DocumentTitle"],
        )
    )
    story.append(
        Paragraph(
            "Modern Software Concepts in Python",
            styles["DocumentSubtitle"],
        )
    )
    story.append(
        Paragraph(
            "Karim Zaky",
            styles["DocumentSubtitle"],
        )
    )
    story.append(Spacer(1, 0.3 * inch))
    story.append(
        Paragraph(
            "This report presents the results, raw SQL queries, and "
            "brief explanations for the nine required analyses and "
            "two original database questions.",
            styles["BodyTextCustom"],
        )
    )
    story.append(PageBreak())

    average_gpa, average_gre, average_gre_v, average_gre_aw = (
        results["q3"]
    )

    original_count = results["q8"]
    llm_count = results["q9"]
    difference = llm_count - original_count

    add_question(
        story,
        styles,
        1,
        "How many entries are from applicants who applied for Fall 2026?",
        f"Fall 2026 applicant count: {results['q1']:,}",
        QUESTION_1_SQL,
        "The query standardizes the term with LOWER and TRIM, filters "
        "the table to Fall 2026, and counts every matching row.",
    )

    add_question(
        story,
        styles,
        2,
        "Among entries that provide a nationality classification, what "
        "percentage are international students?",
        f"Percent international: {results['q2']:.2f}%",
        QUESTION_2_SQL,
        "The numerator counts entries classified as International. "
        "The denominator includes every nonblank nationality "
        "classification, including American and Other, while excluding "
        "missing values. NULLIF prevents division by zero.",
    )

    add_question(
        story,
        styles,
        3,
        "What are the average GPA, GRE Quantitative, GRE Verbal, and "
        "GRE Analytical Writing scores of applicants who provide each metric?",
        (
            f"Average GPA: {average_gpa:.2f}\n"
            f"Average GRE Quantitative: {average_gre:.2f}\n"
            f"Average GRE Verbal: {average_gre_v:.2f}\n"
            f"Average GRE Analytical Writing: {average_gre_aw:.2f}"
        ),
        QUESTION_3_SQL,
        "Each AVG calculation operates independently. PostgreSQL ignores "
        "NULL values, so an applicant contributes to any average for "
        "which that applicant supplied a usable value.",
    )

    add_question(
        story,
        styles,
        4,
        "What is the average GPA of American applicants who applied for "
        "Fall 2026?",
        (
            "Average GPA of American Fall 2026 applicants: "
            f"{results['q4']:.2f}"
        ),
        QUESTION_4_SQL,
        "The query simultaneously restricts records to Fall 2026, "
        "American applicants, and records with a usable GPA. AVG then "
        "calculates the mean of those matching GPA values.",
    )

    add_question(
        story,
        styles,
        5,
        "What percentage of Fall 2025 entries are acceptances?",
        f"Fall 2025 acceptance percentage: {results['q5']:.2f}%",
        QUESTION_5_SQL,
        "The main WHERE clause defines all Fall 2025 entries as the "
        "denominator. The filtered count includes statuses beginning "
        "with Accepted as the numerator.",
    )

    add_question(
        story,
        styles,
        6,
        "What is the average GPA of accepted applicants who applied for "
        "Fall 2026?",
        (
            "Average GPA of accepted Fall 2026 applicants: "
            f"{results['q6']:.2f}"
        ),
        QUESTION_6_SQL,
        "The query requires Fall 2026, an acceptance status, and a "
        "nonmissing GPA before calculating the average.",
    )

    add_question(
        story,
        styles,
        7,
        "How many entries are from applicants who applied to Johns "
        "Hopkins University for a master's degree in Computer Science?",
        (
            "Johns Hopkins Computer Science master's count: "
            f"{results['q7']:,}"
        ),
        QUESTION_7_SQL,
        "The query uses the original program and degree fields. It "
        "recognizes both Johns Hopkins University and the standalone "
        "abbreviation JHU, requires Computer Science, and restricts the "
        "degree to Masters.",
    )

    add_question(
        story,
        styles,
        8,
        "How many Fall 2026 entries are acceptances from applicants "
        "applying for a Computer Science PhD at Georgetown, MIT, "
        "Stanford, or Carnegie Mellon using the original fields?",
        f"Original-field count: {original_count:,}",
        QUESTION_8_SQL,
        "The query requires all five conditions at the same time: Fall "
        "2026, acceptance, PhD, Computer Science, and one of the four "
        "listed universities. University and program matching use the "
        "original combined program field.",
    )

    add_question(
        story,
        styles,
        9,
        "Repeat Question 8 using the LLM-generated program and university "
        "fields, and compare the results.",
        (
            f"Original-field count: {original_count:,}\n"
            f"LLM-field count: {llm_count:,}\n"
            f"Difference: {difference:+,}"
        ),
        QUESTION_9_SQL,
        "This query keeps the original term, status, and degree fields "
        "but identifies the program and university through the "
        "LLM-generated fields. The counts are equal, suggesting that "
        "the LLM normalization did not change the qualifying set for "
        "this specific analysis. Individual labels can still contain "
        "normalization errors even when the final count is unchanged.",
    )

    add_question(
        story,
        styles,
        10,
        "How do Fall 2026 acceptance percentages compare between "
        "American and international applicants?",
        format_question_10(results["q10"]),
        QUESTION_10_SQL,
        "The query groups Fall 2026 records by nationality classification. "
        "For each group, it counts all entries and accepted entries, then "
        "calculates the acceptance percentage. These self-reported "
        "percentages describe the GradCafe data and should not be treated "
        "as official population acceptance rates.",
    )

    add_question(
        story,
        styles,
        11,
        "Which five universities have the most reported Fall 2026 "
        "acceptances?",
        format_question_11(results["q11"]),
        QUESTION_11_SQL,
        "The query groups accepted Fall 2026 records by the normalized "
        "university field, orders the groups by their reported acceptance "
        "counts, and returns the five largest groups. The results measure "
        "reporting frequency in this dataset rather than official "
        "university acceptance totals.",
        add_page_break=False,
    )

    document.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )


def validate_pdf():
    """Reopen the PDF and verify its basic content."""
    reader = PdfReader(str(OUTPUT_FILE))
    extracted_text = "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )

    required_text = [
        "Question 1",
        "Question 11",
        "Fall 2026 applicant count",
        "Original-field count",
        "Columbia University",
    ]

    missing_text = [
        text
        for text in required_text
        if text not in extracted_text
    ]

    if missing_text:
        raise ValueError(
            f"PDF validation failed. Missing text: {missing_text}"
        )

    print(f"PDF created: {OUTPUT_FILE.name}")
    print(f"PDF pages: {len(reader.pages)}")
    print("PDF text validation passed")


def main():
    """Collect query results, build the PDF, and validate it."""
    results = collect_results()
    build_pdf(results)
    validate_pdf()


if __name__ == "__main__":
    main()
