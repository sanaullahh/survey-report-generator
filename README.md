# Survey Report Generator

Upload a survey export (.xlsx or .csv) and get summary stats, charts, and a downloadable PDF
report — automatically, in a couple of seconds. No manual counting, no copy-pasting into
PowerPoint.

A sample file (`sample_survey_responses.xlsx`) is included so you can try it immediately.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Upload `sample_survey_responses.xlsx` (included) to see it in action, or upload your own
survey export.

## What it does

- **Auto-detects question types** — multiple choice, rating scale (1-5, 1-10, etc.),
  open-ended text, and timestamps — from the raw column data, no manual setup
- **Flags data quality issues instead of guessing** — blank answers and out-of-range values
  (e.g. a "7" on a 1-5 scale) are shown clearly, never silently fixed or dropped
- **Generates real charts** for every question — bar charts for multiple choice, distribution
  charts for ratings, word-frequency charts for open text
- **Exports a branded PDF report** — add your organization name and a report title, and it
  produces a clean, presentable PDF with all the above
- Handles both `.xlsx` and `.csv` exports (Google Forms, Microsoft Forms, Typeform, etc. all
  export in one of these)

## How column types are detected

This is heuristic-based, same honest approach as a real data-cleaning tool:
- **Timestamp** — column parses as valid dates for 80%+ of values
- **Rating** — numeric, 12 or fewer unique values, and 90%+ fall within a common scale (1-3,
  1-5, 1-7, or 1-10)
- **Categorical (multiple choice)** — 20 or fewer unique values, low uniqueness ratio, short
  average answer length
- **Open text** — everything else (long or highly varied answers)

If a column doesn't clearly fit, it's left as open text rather than forced into the wrong
category.

## Project structure

```
survey-report-generator/
├── app.py                          (Streamlit UI)
├── analysis.py                     (column detection, stats — testable independent of UI)
├── charts.py                       (matplotlib chart generation)
├── pdf_report.py                   (PDF report assembly, via reportlab)
├── sample_survey_responses.xlsx    (included test file — 200 fake responses)
├── requirements.txt
└── README.md
```

## Testing notes

Before this was packaged, every piece was actually run and checked, not just written:
- All analysis logic tested against the real sample file
- Charts visually inspected for correct rendering
- A full PDF was generated and every page visually reviewed
- The Streamlit app itself was run through Streamlit's testing framework with a simulated
  file upload (both `.xlsx` and `.csv`), plus a corrupted file and an empty file, to confirm
  errors are shown clearly instead of crashing the app

## Possible next steps

- Compare two survey exports side by side (e.g. this month vs. last month)
- Let users filter/segment responses before generating the report
- Export to PowerPoint slides in addition to PDF
- Add a logo upload for the PDF header

## Author

**Sanaullah Khokhar**
[LinkedIn](https://linkedin.com/in/sanaullah-khokhar)
