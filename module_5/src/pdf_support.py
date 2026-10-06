"""Shared typography and content validation for generated PDF reports."""

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle


def add_title_style(styles, name, **overrides):
    """Add the reports' common title typography with report-specific settings."""
    styles.add(
        ParagraphStyle(
            name=name,
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            alignment=TA_CENTER,
            **overrides,
        )
    )


def add_body_style(styles, **overrides):
    """Add the common body style with report-specific spacing and colors."""
    styles.add(
        ParagraphStyle(
            name="BodyTextCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            **overrides,
        )
    )


def validate_report(output_file, reader, required_text):
    """Reject incomplete reports and describe successfully validated output."""
    extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    missing_text = [value for value in required_text if value not in extracted_text]
    if missing_text:
        raise ValueError(f"PDF validation failed. Missing text: {missing_text}")
    print(f"PDF created: {output_file.name}")
    print(f"PDF pages: {len(reader.pages)}")
    print("PDF text validation passed")


def build_report(document, story, page_number):
    """Build a report with the same page numbering on every page."""
    document.build(story, onFirstPage=page_number, onLaterPages=page_number)
