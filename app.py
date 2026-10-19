import streamlit as st
import pandas as pd
from analysis import (
    detect_column_types, compute_data_quality, compute_summary,
    compute_categorical_stats, compute_rating_stats, compute_open_text_stats
)
from charts import make_categorical_chart, make_rating_chart, make_word_frequency_chart
from pdf_report import build_pdf_report

st.set_page_config(page_title="Survey Report Generator", page_icon="📋", layout="centered")

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root {
    --bg: #F5F5F2;
    --surface: #FFFFFF;
    --ink: #1A1A2E;
    --muted: #6B7280;
    --accent: #4F46E5;
    --accent-soft: #EEF2FF;
    --border: #E5E7EB;
    --success: #16A34A;
    --warning: #D97706;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: var(--bg);
}

h1, h2, h3 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: var(--ink) !important;
}

.eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.1em;
    color: var(--accent);
    text-transform: uppercase;
    font-weight: 600;
}

.hero-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 32px;
    font-weight: 800;
    color: var(--ink);
    margin: 4px 0 8px 0;
}

.hero-subtitle {
    color: var(--muted);
    font-size: 15px;
    margin-bottom: 24px;
}

.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
}

.metric-row {
    display: flex;
    gap: 16px;
    margin-bottom: 8px;
}

.metric-box {
    background: var(--accent-soft);
    border-radius: 12px;
    padding: 14px 18px;
    flex: 1;
}

.metric-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.metric-value {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: var(--ink);
    margin-top: 2px;
}

.quality-flag {
    background: #FFFBEB;
    border-left: 3px solid var(--warning);
    padding: 10px 14px;
    border-radius: 6px;
    margin-bottom: 8px;
    font-size: 13.5px;
    color: #92400E;
}

.quality-clean {
    background: #F0FDF4;
    border-left: 3px solid var(--success);
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 13.5px;
    color: #166534;
}

.question-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 16px;
    color: var(--ink);
    margin-top: 4px;
}

.stButton > button, .stDownloadButton > button {
    background: var(--accent) !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    border: none !important;
    padding: 10px 20px !important;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    background: #4338CA !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: var(--surface) !important;
    border: 1.5px dashed var(--accent) !important;
    border-radius: 14px !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown('<span class="eyebrow">SURVEY REPORT GENERATOR</span>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Turn raw survey data into a real report</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Upload a survey export (.xlsx or .csv) and get summary stats, '
    'charts, and a downloadable PDF report — nothing guessed, issues flagged for your review.</div>',
    unsafe_allow_html=True
)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        org_name = st.text_input("Organization / brand name (optional)", placeholder="e.g. Brewhouse Coffee Co.")
    with col2:
        report_title = st.text_input("Report title (optional)", placeholder="e.g. Q3 Customer Survey")

    uploaded_file = st.file_uploader("Upload survey responses", type=["xlsx", "csv"])
    st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        df = df.dropna(how="all")
    except Exception as e:
        st.error(f"Could not read this file: {e}")
        st.stop()

    if len(df) == 0:
        st.error("This file has no data rows.")
        st.stop()

    column_info = detect_column_types(df)
    summary = compute_summary(df, column_info)
    quality = compute_data_quality(df, column_info)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Summary")
    date_text = ""
    if summary["date_range"]:
        start, end = summary["date_range"]
        date_text = f'<div class="metric-box"><div class="metric-label">Period</div><div class="metric-value" style="font-size:15px">{start.strftime("%b %d")} – {end.strftime("%b %d, %Y")}</div></div>'
    st.markdown(
        f'<div class="metric-row">'
        f'<div class="metric-box"><div class="metric-label">Responses</div><div class="metric-value">{summary["total_responses"]}</div></div>'
        f'<div class="metric-box"><div class="metric-label">Questions</div><div class="metric-value">{len(column_info)}</div></div>'
        f'{date_text}'
        f'</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Data Quality")
    has_flags = bool(quality["issues"]) or any(v > 0 for v in quality["blank_counts"].values())
    if not has_flags:
        st.markdown('<div class="quality-clean">No blanks or out-of-range values detected.</div>', unsafe_allow_html=True)
    else:
        for col, count in quality["blank_counts"].items():
            if count > 0:
                st.markdown(f'<div class="quality-flag">📌 <b>{col}</b> — {count} blank response(s)</div>', unsafe_allow_html=True)
        for issue in quality["issues"]:
            st.markdown(f'<div class="quality-flag">⚠️ <b>{issue["column"]}</b> — {issue["issue"]}</div>', unsafe_allow_html=True)
        st.caption("These are flagged for your review — nothing was changed or guessed.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Question Breakdown")
    for col, info in column_info.items():
        if info["type"] == "timestamp":
            continue

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="question-title">{col}</div>', unsafe_allow_html=True)

        if info["type"] == "categorical":
            stats_df = compute_categorical_stats(df, col)
            chart_buf = make_categorical_chart(stats_df, col)
            st.image(chart_buf, width='stretch')

        elif info["type"] == "rating":
            rstats = compute_rating_stats(df, col, info["expected_min"], info["expected_max"])
            st.caption(f"Average: **{rstats['average']}** out of {info['expected_max']} ({rstats['count']} valid responses)")
            chart_buf = make_rating_chart(rstats["distribution"], col, rstats["average"])
            st.image(chart_buf, width='stretch')

        elif info["type"] == "open_text":
            tstats = compute_open_text_stats(df, col)
            st.caption(f"{tstats['response_count']} written responses ({tstats['blank_count']} left blank)")
            if tstats["top_words"]:
                chart_buf = make_word_frequency_chart(tstats["top_words"], "Common words")
                st.image(chart_buf, width='stretch')
            if tstats["sample_responses"]:
                with st.expander("Sample responses"):
                    for r in tstats["sample_responses"]:
                        st.write(f"— {r}")

        elif info["type"] == "empty":
            st.caption("No data in this column.")

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Export")
    pdf_buffer = build_pdf_report(
        df, column_info, summary, quality,
        report_title or "Survey Report",
        org_name
    )
    st.download_button(
        "Download PDF Report",
        data=pdf_buffer,
        file_name="survey_report.pdf",
        mime="application/pdf"
    )
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Upload a survey file to get started. A sample file (sample_survey_responses.xlsx) is included in this project folder if you want to try it first.")
