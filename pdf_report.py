import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)

from analysis import (
    compute_categorical_stats, compute_rating_stats, compute_open_text_stats
)
from charts import make_categorical_chart, make_rating_chart, make_word_frequency_chart
from PIL import Image as PILImage


def _scaled_image(buf, target_width):
    buf.seek(0)
    pil_img = PILImage.open(buf)
    aspect = pil_img.height / pil_img.width
    buf.seek(0)
    return Image(buf, width=target_width, height=target_width * aspect)

ACCENT = colors.HexColor("#4F46E5")
INK = colors.HexColor("#1A1A2E")
MUTED = colors.HexColor("#6B7280")
LIGHT_BG = colors.HexColor("#F5F5F2")


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", fontSize=22, leading=26, textColor=INK,
        fontName="Helvetica-Bold", spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle", fontSize=11, textColor=MUTED, spaceAfter=20
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading", fontSize=15, textColor=INK,
        fontName="Helvetica-Bold", spaceBefore=18, spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name="QuestionHeading", fontSize=12, textColor=INK,
        fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="BodyMuted", fontSize=9.5, textColor=MUTED, leading=13
    ))
    styles.add(ParagraphStyle(
        name="BodyText2", fontSize=10, textColor=INK, leading=14
    ))
    return styles


def build_pdf_report(df, column_info, summary, quality, report_title, org_name):
    styles = build_styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch
    )
    story = []

    story.append(Paragraph(report_title or "Survey Report", styles["ReportTitle"]))
    subtitle_parts = []
    if org_name:
        subtitle_parts.append(org_name)
    subtitle_parts.append(f"Generated {datetime.now().strftime('%B %d, %Y')}")
    story.append(Paragraph(" · ".join(subtitle_parts), styles["ReportSubtitle"]))

    story.append(Paragraph("Summary", styles["SectionHeading"]))
    summary_rows = [["Total responses", str(summary["total_responses"])]]
    if summary.get("date_range"):
        start, end = summary["date_range"]
        summary_rows.append(["Response period", f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"])
    summary_table = Table(summary_rows, colWidths=[2.2 * inch, 3.5 * inch])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
    ]))
    story.append(summary_table)

    if quality["issues"] or any(quality["blank_counts"].values()):
        story.append(Paragraph("Data Quality Notes", styles["SectionHeading"]))
        story.append(Paragraph(
            "These items were flagged, not automatically changed. Review the original file "
            "for these rows before drawing conclusions.",
            styles["BodyMuted"]
        ))
        story.append(Spacer(1, 6))

        quality_rows = [["Column", "Note"]]
        for col, count in quality["blank_counts"].items():
            if count > 0:
                quality_rows.append([col, f"{count} blank response(s)"])
        for issue in quality["issues"]:
            quality_rows.append([issue["column"], issue["issue"]])

        quality_table = Table(quality_rows, colWidths=[2.2 * inch, 3.8 * inch])
        quality_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), INK),
            ("TEXTCOLOR", (0, 1), (-1, -1), MUTED),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ]))
        story.append(quality_table)

    story.append(PageBreak())
    story.append(Paragraph("Question Breakdown", styles["SectionHeading"]))

    for col, info in column_info.items():
        if info["type"] == "categorical":
            stats_df = compute_categorical_stats(df, col)
            chart_buf = make_categorical_chart(stats_df, col)
            story.append(Paragraph(col, styles["QuestionHeading"]))
            story.append(_scaled_image(chart_buf, 5.5 * inch))

        elif info["type"] == "rating":
            rstats = compute_rating_stats(df, col, info["expected_min"], info["expected_max"])
            chart_buf = make_rating_chart(rstats["distribution"], col, rstats["average"])
            story.append(Paragraph(col, styles["QuestionHeading"]))
            story.append(Paragraph(f"Average: {rstats['average']} out of {info['expected_max']} ({rstats['count']} valid responses)", styles["BodyText2"]))
            story.append(Spacer(1, 4))
            story.append(_scaled_image(chart_buf, 5 * inch))

        elif info["type"] == "open_text":
            tstats = compute_open_text_stats(df, col)
            story.append(Paragraph(col, styles["QuestionHeading"]))
            story.append(Paragraph(
                f"{tstats['response_count']} written responses ({tstats['blank_count']} left blank)",
                styles["BodyText2"]
            ))
            if tstats["top_words"]:
                story.append(Spacer(1, 4))
                word_chart = make_word_frequency_chart(tstats["top_words"], f"Common words — {col}")
                story.append(_scaled_image(word_chart, 5 * inch))
            if tstats["sample_responses"]:
                story.append(Spacer(1, 6))
                story.append(Paragraph("Sample responses:", styles["BodyText2"]))
                for r in tstats["sample_responses"][:5]:
                    story.append(Paragraph(f"&ldquo;{r}&rdquo;", styles["BodyMuted"]))

        story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer
