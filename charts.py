import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

ACCENT = "#4F46E5"
ACCENT_LIGHT = "#818CF8"
INK = "#1A1A2E"
MUTED = "#6B7280"
GRID = "#E5E7EB"

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.edgecolor"] = GRID
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["text.color"] = INK
plt.rcParams["axes.labelcolor"] = INK
plt.rcParams["xtick.color"] = MUTED
plt.rcParams["ytick.color"] = MUTED


def _fig_to_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf


def make_categorical_chart(stats_df, title):
    fig, ax = plt.subplots(figsize=(7, max(2.5, 0.5 * len(stats_df))))
    stats_df_sorted = stats_df.sort_values("Count", ascending=True)
    bars = ax.barh(stats_df_sorted["Response"].astype(str), stats_df_sorted["Count"], color=ACCENT)
    ax.set_xlabel("Responses")
    ax.set_title(title, fontsize=12, fontweight="bold", loc="left", pad=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar, pct in zip(bars, stats_df_sorted["Percent"]):
        ax.text(
            bar.get_width() + max(stats_df_sorted["Count"]) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{pct}%",
            va="center", fontsize=9, color=MUTED
        )
    fig.tight_layout()
    return _fig_to_bytes(fig)


def make_rating_chart(distribution, title, average):
    fig, ax = plt.subplots(figsize=(6, 3.2))
    colors = [ACCENT_LIGHT] * len(distribution)
    bars = ax.bar(distribution.index.astype(str), distribution.values, color=colors)
    ax.set_xlabel("Rating")
    ax.set_ylabel("Responses")
    ax.set_title(f"{title}  (avg: {average})", fontsize=12, fontweight="bold", loc="left", pad=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, height + max(distribution.values) * 0.02,
                     str(int(height)), ha="center", fontsize=9, color=MUTED)
    fig.tight_layout()
    return _fig_to_bytes(fig)


def make_word_frequency_chart(top_words, title):
    if not top_words:
        return None
    fig, ax = plt.subplots(figsize=(6, max(2.5, 0.4 * len(top_words))))
    words = [w[0] for w in top_words][::-1]
    counts = [w[1] for w in top_words][::-1]
    ax.barh(words, counts, color=ACCENT)
    ax.set_xlabel("Mentions")
    ax.set_title(title, fontsize=12, fontweight="bold", loc="left", pad=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _fig_to_bytes(fig)
