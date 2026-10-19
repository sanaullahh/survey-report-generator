import pandas as pd
import numpy as np


def load_survey_file(file):
    name = getattr(file, "name", str(file))
    if name.lower().endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    df = df.dropna(how="all")
    return df


def detect_column_types(df):
    column_info = {}

    for col in df.columns:
        series = df[col]
        non_null = series.dropna()

        if len(non_null) == 0:
            column_info[col] = {"type": "empty"}
            continue

        if pd.api.types.is_datetime64_any_dtype(series):
            column_info[col] = {"type": "timestamp"}
            continue

        if not pd.api.types.is_numeric_dtype(non_null):
            parsed_dates = pd.to_datetime(non_null, errors="coerce", format="mixed")
            date_success_rate = parsed_dates.notna().mean()
            if date_success_rate > 0.8:
                column_info[col] = {"type": "timestamp"}
                continue

        numeric = pd.to_numeric(non_null, errors="coerce")
        numeric_rate = numeric.notna().mean()

        if numeric_rate > 0.95:
            numeric_clean = numeric.dropna()
            unique_vals = numeric_clean.nunique()

            if unique_vals <= 12 and (numeric_clean == numeric_clean.round()).all():
                best_scale = None
                for scale_max in (3, 5, 7, 10):
                    in_range = ((numeric_clean >= 1) & (numeric_clean <= scale_max)).mean()
                    if in_range >= 0.9:
                        best_scale = scale_max
                        break
                if best_scale:
                    column_info[col] = {
                        "type": "rating",
                        "expected_min": 1,
                        "expected_max": best_scale
                    }
                    continue

            column_info[col] = {"type": "numeric"}
            continue

        unique_count = non_null.nunique()
        unique_ratio = unique_count / len(non_null)
        avg_length = non_null.astype(str).str.len().mean()

        if unique_count <= 20 and unique_ratio < 0.5 and avg_length < 40:
            column_info[col] = {"type": "categorical"}
        else:
            column_info[col] = {"type": "open_text"}

    return column_info


def compute_data_quality(df, column_info):
    total_rows = len(df)
    issues = []
    blank_counts = {}

    for col, info in column_info.items():
        blanks = df[col].isna().sum()
        blank_counts[col] = int(blanks)

        if info["type"] == "rating":
            numeric = pd.to_numeric(df[col], errors="coerce")
            out_of_range = numeric[
                numeric.notna()
                & ((numeric < info["expected_min"]) | (numeric > info["expected_max"]))
            ]
            if len(out_of_range) > 0:
                issues.append({
                    "column": col,
                    "issue": f"{len(out_of_range)} value(s) outside expected {info['expected_min']}-{info['expected_max']} scale",
                    "rows": out_of_range.index.tolist()[:10],
                    "values": out_of_range.tolist()[:10]
                })

    return {"total_rows": total_rows, "blank_counts": blank_counts, "issues": issues}


def compute_summary(df, column_info):
    summary = {"total_responses": len(df), "date_range": None}

    for col, info in column_info.items():
        if info["type"] == "timestamp":
            parsed = pd.to_datetime(df[col], errors="coerce", format="mixed")
            valid = parsed.dropna()
            if len(valid) > 0:
                summary["date_range"] = (valid.min(), valid.max())
            break

    return summary


def compute_categorical_stats(df, col):
    counts = df[col].value_counts(dropna=True)
    total = counts.sum()
    percentages = (counts / total * 100).round(1)
    return pd.DataFrame({"Response": counts.index, "Count": counts.values, "Percent": percentages.values})


def compute_rating_stats(df, col, expected_min, expected_max):
    numeric = pd.to_numeric(df[col], errors="coerce")
    valid = numeric[(numeric >= expected_min) & (numeric <= expected_max)]
    distribution = valid.value_counts().sort_index()
    full_range = pd.Series(0, index=range(expected_min, expected_max + 1))
    full_range.update(distribution)
    return {
        "average": round(valid.mean(), 2) if len(valid) > 0 else None,
        "count": len(valid),
        "distribution": full_range
    }


STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "was", "were", "it", "to", "of", "in",
    "for", "on", "with", "this", "that", "my", "i", "have", "had", "has", "very", "so",
    "be", "at", "as", "when", "if", "there", "would", "could", "you", "your", "we", "our",
    "how", "did", "what", "which", "who", "just", "get", "got", "not", "no", "yes", "all",
    "are", "been", "being", "am", "do", "does", "than", "then", "them", "they", "their",
    "from", "by", "will", "can", "some", "into", "out", "up", "down", "about"
}


def compute_open_text_stats(df, col):
    non_null = df[col].dropna().astype(str)
    word_counts = {}
    for text in non_null:
        words = "".join(c.lower() if c.isalnum() else " " for c in text).split()
        for w in words:
            if len(w) > 2 and w not in STOPWORDS:
                word_counts[w] = word_counts.get(w, 0) + 1

    top_words = sorted(word_counts.items(), key=lambda x: -x[1])[:10]
    return {
        "response_count": len(non_null),
        "blank_count": df[col].isna().sum(),
        "top_words": top_words,
        "sample_responses": non_null.sample(min(5, len(non_null)), random_state=1).tolist() if len(non_null) > 0 else []
    }
