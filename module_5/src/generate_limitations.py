"""Generate and validate the Module 3 data-limitations PDF."""

from pathlib import Path

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from pdf_support import build_report, add_body_style, add_title_style, validate_report
from sql_safety import fetch_applicant_count

from load_data import get_connection
from orm_queries import collect_all_analysis_results

# Store the PDF beside this generator script.
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "limitations.pdf"


# Define a small, consistent color palette for the report.
NAVY = colors.HexColor("#16324F")
BLUE = colors.HexColor("#2563EB")
LIGHT_BLUE = colors.HexColor("#EFF6FF")
SLATE = colors.HexColor("#475569")
LIGHT_GRAY = colors.HexColor("#E2E8F0")
WHITE = colors.white


def get_database_count():
    """Return the bounded aggregate applicant count."""
    return fetch_applicant_count(get_connection)


def get_missing_value_counts():
    """Return missing-value counts for selected numeric fields."""
    query = """
        SELECT
            COUNT(*) FILTER (WHERE gpa IS NULL),
            COUNT(*) FILTER (WHERE gre IS NULL),
            COUNT(*) FILTER (WHERE gre_v IS NULL),
            COUNT(*) FILTER (WHERE gre_aw IS NULL)
        FROM applicants
        LIMIT 1;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()


def add_page_number(canvas, document):
    """Draw a simple footer and page number on every PDF page."""
    canvas.saveState()
    canvas.setStrokeColor(LIGHT_GRAY)
    canvas.line(
        0.7 * inch,
        0.55 * inch,
        LETTER[0] - 0.7 * inch,
        0.55 * inch,
    )

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(SLATE)
    canvas.drawString(
        0.7 * inch,
        0.35 * inch,
        "JHU Modern Software Concepts - Module 3",
    )
    canvas.drawRightString(
        LETTER[0] - 0.7 * inch,
        0.35 * inch,
        f"Page {document.page}",
    )
    canvas.restoreState()


def build_styles():
    """Create the paragraph styles used throughout the PDF."""
    styles = getSampleStyleSheet()

    add_title_style(styles, "ReportTitle", textColor=NAVY, spaceAfter=8)

    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            alignment=TA_CENTER,
            textColor=SLATE,
            spaceAfter=20,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=NAVY,
            spaceAfter=8,
        )
    )

    add_body_style(
        styles, fontSize=10.5, leading=16, textColor=colors.HexColor("#1E293B"), spaceAfter=12
    )

    styles.add(
        ParagraphStyle(
            name="MetricLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=SLATE,
        )
    )

    styles.add(
        ParagraphStyle(
            name="MetricValue",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            alignment=TA_CENTER,
            textColor=BLUE,
        )
    )

    return styles


def create_metric_table(
    styles,
    database_count,
    percent_international,
    american_acceptance,
    international_acceptance,
):
    """Create a compact table connecting limitations to key results."""
    data = [
        [
            Paragraph(
                f"{database_count:,}",
                styles["MetricValue"],
            ),
            Paragraph(
                f"{percent_international:.2f}%",
                styles["MetricValue"],
            ),
            Paragraph(
                f"{american_acceptance:.2f}%",
                styles["MetricValue"],
            ),
            Paragraph(
                f"{international_acceptance:.2f}%",
                styles["MetricValue"],
            ),
        ],
        [
            Paragraph(
                "DATABASE ROWS",
                styles["MetricLabel"],
            ),
            Paragraph(
                "INTERNATIONAL ENTRIES",
                styles["MetricLabel"],
            ),
            Paragraph(
                "AMERICAN ACCEPTANCE",
                styles["MetricLabel"],
            ),
            Paragraph(
                "INTERNATIONAL ACCEPTANCE",
                styles["MetricLabel"],
            ),
        ],
    ]

    table = Table(
        data,
        colWidths=[1.55 * inch] * 4,
        rowHeights=[0.38 * inch, 0.38 * inch],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.75, LIGHT_GRAY),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    return table


def generate_pdf():
    """Query current results and create the limitations report."""
    analysis = collect_all_analysis_results()

    missing_gpa, missing_gre, missing_gre_v, missing_gre_aw = get_missing_value_counts()

    percent_international = analysis["question_2"]

    acceptance_by_group = {
        row.applicant_group.lower(): float(row.acceptance_percentage)
        for row in analysis["original_question"]
    }

    american_acceptance = acceptance_by_group["american"]
    international_acceptance = acceptance_by_group["international"]

    original_field_count = analysis["question_8"]

    styles = build_styles()

    document = SimpleDocTemplate(
        str(OUTPUT_FILE),
        pagesize=LETTER,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.75 * inch,
        title="Module 3 Data and Analysis Limitations",
        author="Karim Zaky",
    )

    story = [
        Paragraph(
            "Data and Analysis Limitations",
            styles["ReportTitle"],
        ),
        Paragraph(
            "GradCafe Applicant Analysis | Module 3",
            styles["ReportSubtitle"],
        ),
        create_metric_table(
            styles,
            get_database_count(),
            percent_international,
            american_acceptance,
            international_acceptance,
        ),
        Spacer(1, 0.25 * inch),
    ]

    first_paragraph = (
        "The GradCafe dataset is a large collection of anonymous, "
        "self-reported entries rather than a random or complete sample "
        "of graduate-school applicants. People choose whether to report "
        "their results, and reporting behavior may differ by university, "
        "program, nationality, decision outcome, and application year. "
        f"For example, international entries represent "
        f"{percent_international:.2f}% of records with a reported "
        "applicant group, while the calculated Fall 2026 acceptance "
        f"percentages are {american_acceptance:.2f}% for American "
        f"entries and {international_acceptance:.2f}% for international "
        "entries. These percentages describe only the submitted "
        "GradCafe records and cannot establish the official acceptance "
        "rates of either population. Duplicate prevention by URL improves "
        "internal consistency, but it cannot correct selection bias, "
        "misreporting, or applicants who never submitted a result."
    )

    second_paragraph = (
        "Missing, inconsistent, and transformed values also limit the "
        "precision of the analysis. PostgreSQL currently contains "
        f"{missing_gpa:,} rows without a usable GPA, {missing_gre:,} "
        f"without a valid GRE Quantitative score, {missing_gre_v:,} "
        f"without a valid GRE Verbal score, and {missing_gre_aw:,} "
        "without a valid Analytical Writing score. Out-of-range values "
        "were stored as SQL NULL rather than included in averages, which "
        "avoids obviously invalid calculations but reduces the available "
        "sample and may introduce additional bias if missingness is not "
        "random. The LLM-generated program and university fields improve "
        "search consistency but may contain normalization errors, and new "
        "records collected by the scraper remain NULL in those fields "
        "until a separate enrichment process is performed. The original "
        f"and LLM fields both produced {original_field_count:,} matching "
        "records for the selected Computer Science PhD comparison, but "
        "agreement on that query does not prove that every generated value "
        "is accurate. Results should therefore be interpreted as "
        "descriptive patterns in the collected dataset, not authoritative "
        "admissions statistics."
    )

    story.extend(
        [
            KeepTogether(
                [
                    Paragraph(
                        "1. Self-Reporting and Selection Bias",
                        styles["SectionHeading"],
                    ),
                    Paragraph(
                        first_paragraph,
                        styles["BodyTextCustom"],
                    ),
                ]
            ),
            Spacer(1, 0.08 * inch),
            KeepTogether(
                [
                    Paragraph(
                        "2. Missing Values and Field Reliability",
                        styles["SectionHeading"],
                    ),
                    Paragraph(
                        second_paragraph,
                        styles["BodyTextCustom"],
                    ),
                ]
            ),
        ]
    )

    build_report(document, story, add_page_number)


def validate_pdf():
    """Verify this report using the shared content validator."""
    required_text = [
        "Data and Analysis Limitations",
        "Self-Reporting and Selection Bias",
        "Missing Values and Field Reliability",
        "descriptive patterns",
    ]
    validate_report(OUTPUT_FILE, PdfReader(str(OUTPUT_FILE)), required_text)


def main():
    """Generate the PDF and validate its extracted text."""
    generate_pdf()
    validate_pdf()


if __name__ == "__main__":
    main()
