"""AI adoption analysis for the Stack Overflow Developer Survey, 2023-2025.

Scope
-----
This module answers: how did AI adoption in the developer community evolve
across 2023, 2024 and 2025, overall and broken down by professional seniority
("vetek") and by age?

It works directly from the annual raw survey files (``results_<year>.csv``)
because the AI questions are not identical across years. We therefore map each
year's own raw column names explicitly and NEVER assume the columns match.

Two AI variables (per the project's harmonized schema):
  * AI_Usage_Status  <- raw ``AISelect``            (present 2023, 2024, 2025)
  * AI_Tool_Usage    <- raw ``AIToolCurrently Using`` (present 2023, 2024 only)

Important year differences that this code handles explicitly:
  * ``AISelect`` answer wording changed in 2025. 2023/2024 use a single
    "Yes"; 2025 splits it into "Yes, I use AI tools daily / weekly /
    monthly...". Adoption is therefore harmonized as: the answer starts with
    "Yes".
  * ``AIToolCurrently Using`` was restructured in 2025 (task-level
    "partially/mostly AI" columns) and has NO directly comparable column, so
    AI_Tool_Usage is treated as absent in 2025.
  * Professional experience is ``YearsCodePro`` in 2023/2024 (real), but 2025
    publishes only ``YearsCode`` (total coding years) which is used as an
    explicitly tagged proxy (experience_is_proxy=True), matching the repo's
    harmonization decision.

Outputs (written under outputs/):
  * outputs/ai/ai_adoption_summary.md   - human-readable tables
  * outputs/ai/ai_adoption_metrics.csv  - tidy metrics for every cell + CI
  * outputs/figures/ai_adoption_by_seniority.png
  * outputs/figures/ai_adoption_by_age.png
  * outputs/figures/ai_status_composition.png
"""

from __future__ import annotations

from pathlib import Path
import math

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

# Each year maps its OWN raw column names. Do not assume columns are shared.
YEAR_CONFIG: dict[int, dict] = {
    2023: {
        "ai_status": "AISelect",
        "ai_tool": "AIToolCurrently Using",
        "experience": "YearsCodePro",
        "age": "Age",
        "experience_is_proxy": False,
    },
    2024: {
        "ai_status": "AISelect",
        "ai_tool": "AIToolCurrently Using",
        "experience": "YearsCodePro",
        "age": "Age",
        "experience_is_proxy": False,
    },
    2025: {
        "ai_status": "AISelect",
        "ai_tool": None,  # restructured in 2025 -> no comparable column
        "experience": "YearsCode",  # proxy: YearsCodePro not published in 2025
        "age": "Age",
        "experience_is_proxy": True,
    },
}

COHORT_ORDER = ["Junior (<=3 yrs)", "Mid (4-7 yrs)", "Senior (>=8 yrs)"]
AGE_ORDER = [
    "Under 18 years old",
    "18-24 years old",
    "25-34 years old",
    "35-44 years old",
    "45-54 years old",
    "55-64 years old",
    "65 years or older",
]


# --------------------------------------------------------------------------
# Small statistical / parsing helpers
# --------------------------------------------------------------------------

def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95% confidence interval for a proportion."""
    if n == 0:
        return (math.nan, math.nan)
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, center - half), min(1.0, center + half))


def parse_experience_years(value: object) -> float:
    """Parse a survey experience answer into a float number of years."""
    if pd.isna(value):
        return math.nan
    text = str(value).strip().lower()
    if text == "" or text == "nan":
        return math.nan
    if text.startswith("less than 1"):
        return 0.5
    if text.startswith("more than 50"):
        return 51.0
    try:
        return float(text)
    except ValueError:
        return math.nan


def experience_to_cohort(years: float) -> object:
    """Map professional experience in years to a seniority cohort."""
    if pd.isna(years):
        return pd.NA
    if years <= 3:
        return COHORT_ORDER[0]
    if years <= 7:
        return COHORT_ORDER[1]
    return COHORT_ORDER[2]


def is_adopter(status: object) -> object:
    """AI adopter = AISelect answer that starts with 'Yes' (any year wording)."""
    if pd.isna(status):
        return pd.NA
    return str(status).strip().lower().startswith("yes")


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def load_year(raw_dir: Path, year: int) -> pd.DataFrame:
    """Load only the relevant columns for one survey year into a tidy frame."""
    cfg = YEAR_CONFIG[year]
    path = raw_dir / f"results_{year}.csv"
    available = pd.read_csv(path, nrows=0).columns.tolist()

    usecols = [cfg["ai_status"], cfg["experience"], cfg["age"]]
    if cfg["ai_tool"] and cfg["ai_tool"] in available:
        usecols.append(cfg["ai_tool"])
    usecols = [c for c in usecols if c in available]

    raw = pd.read_csv(path, usecols=usecols, low_memory=False)

    out = pd.DataFrame(index=raw.index)
    out["Year"] = year
    out["AI_Usage_Status"] = raw[cfg["ai_status"]]
    out["AI_Tool_Usage"] = (
        raw[cfg["ai_tool"]] if (cfg["ai_tool"] and cfg["ai_tool"] in raw.columns) else pd.NA
    )
    out["Age"] = raw[cfg["age"]]
    out["experience_years"] = raw[cfg["experience"]].map(parse_experience_years)
    out["experience_is_proxy"] = cfg["experience_is_proxy"]
    out["Seniority"] = out["experience_years"].map(experience_to_cohort)
    out["is_adopter"] = out["AI_Usage_Status"].map(is_adopter)
    return out


# --------------------------------------------------------------------------
# Metric builders
# --------------------------------------------------------------------------

def _rate_row(label_fields: dict, mask_adopt: pd.Series) -> dict:
    """Build one metric row (count, n, rate, Wilson CI) from a boolean series."""
    valid = mask_adopt.dropna()
    n = int(valid.shape[0])
    k = int(valid.sum())
    lo, hi = wilson_ci(k, n)
    row = dict(label_fields)
    row.update(
        n_valid=n,
        adopters=k,
        adoption_rate=(k / n if n else math.nan),
        ci_low=lo,
        ci_high=hi,
    )
    return row


def per_year_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Coverage + overall adoption for both AI variables, per year."""
    rows = []
    for year, g in df.groupby("Year"):
        cfg = YEAR_CONFIG[year]
        n_total = len(g)
        status_nonnull = int(g["AI_Usage_Status"].notna().sum())
        tool_nonnull = int(g["AI_Tool_Usage"].notna().sum())
        adopt = g["is_adopter"].dropna()
        k = int(adopt.sum())
        lo, hi = wilson_ci(k, len(adopt))
        # overlap between the two AI variables
        both = int((g["AI_Usage_Status"].notna() & g["AI_Tool_Usage"].notna()).sum())
        rows.append(
            dict(
                Year=year,
                n_total=n_total,
                status_source=cfg["ai_status"],
                status_nonnull=status_nonnull,
                status_coverage=status_nonnull / n_total,
                tool_source=cfg["ai_tool"] or "(absent this year)",
                tool_nonnull=tool_nonnull,
                tool_coverage=tool_nonnull / n_total,
                overlap_status_and_tool=both,
                adopters_yes=k,
                adoption_rate=k / len(adopt) if len(adopt) else math.nan,
                adoption_ci_low=lo,
                adoption_ci_high=hi,
                experience_source=cfg["experience"],
                experience_is_proxy=cfg["experience_is_proxy"],
            )
        )
    return pd.DataFrame(rows).sort_values("Year").reset_index(drop=True)


def status_composition(df: pd.DataFrame) -> pd.DataFrame:
    """Harmonized AISelect composition per year: Uses AI / Plans to / Won't."""
    def bucket(s: object) -> object:
        if pd.isna(s):
            return pd.NA
        t = str(s).strip().lower()
        if t.startswith("yes"):
            return "Uses AI"
        if t.startswith("no, but"):
            return "Plans to adopt"
        if t.startswith("no, and"):
            return "No plans"
        return "Other"

    tmp = df.copy()
    tmp["bucket"] = tmp["AI_Usage_Status"].map(bucket)
    tab = (
        tmp.dropna(subset=["bucket"])
        .groupby(["Year", "bucket"]).size()
        .unstack(fill_value=0)
    )
    return tab.div(tab.sum(axis=1), axis=0)  # proportions


def adoption_by_seniority(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, g in df.groupby("Year"):
        for cohort in COHORT_ORDER:
            sub = g[g["Seniority"] == cohort]
            rows.append(
                _rate_row(
                    {
                        "Year": year,
                        "Seniority": cohort,
                        "experience_is_proxy": YEAR_CONFIG[year]["experience_is_proxy"],
                    },
                    sub["is_adopter"],
                )
            )
    return pd.DataFrame(rows)


def adoption_by_age(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, g in df.groupby("Year"):
        for age in AGE_ORDER:
            sub = g[g["Age"] == age]
            rows.append(_rate_row({"Year": year, "Age": age}, sub["is_adopter"]))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------

def plot_by_seniority(sen: pd.DataFrame, path: Path) -> None:
    years = sorted(sen["Year"].unique())
    x = np.arange(len(COHORT_ORDER))
    width = 0.8 / len(years)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for i, year in enumerate(years):
        g = sen[sen["Year"] == year].set_index("Seniority").reindex(COHORT_ORDER)
        rates = g["adoption_rate"].values * 100
        err = np.vstack([
            (g["adoption_rate"] - g["ci_low"]).values * 100,
            (g["ci_high"] - g["adoption_rate"]).values * 100,
        ])
        proxy = bool(g["experience_is_proxy"].iloc[0])
        label = f"{year}" + (" (experience=proxy)" if proxy else "")
        bars = ax.bar(x + i * width - 0.4 + width / 2, rates, width,
                      yerr=err, capsize=3, label=label,
                      hatch=("//" if proxy else None), edgecolor="white")
        for b, r in zip(bars, rates):
            if not math.isnan(r):
                ax.text(b.get_x() + b.get_width() / 2, r + 1, f"{r:.0f}",
                        ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(COHORT_ORDER)
    ax.set_ylabel("AI adoption rate (%)")
    ax.set_ylim(0, 100)
    ax.set_title("AI adoption by professional seniority, 2023-2025\n"
                 "(adopter = AISelect answer starts with 'Yes')", fontsize=11)
    ax.legend(title="Survey year")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_by_age(age_df: pd.DataFrame, path: Path) -> None:
    years = sorted(age_df["Year"].unique())
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for year in years:
        g = age_df[age_df["Year"] == year].set_index("Age").reindex(AGE_ORDER)
        ax.plot(AGE_ORDER, g["adoption_rate"].values * 100, marker="o", label=str(year))
        ax.fill_between(AGE_ORDER, g["ci_low"].values * 100, g["ci_high"].values * 100,
                        alpha=0.12)
    ax.set_ylabel("AI adoption rate (%)")
    ax.set_ylim(0, 100)
    ax.set_title("AI adoption by age band, 2023-2025", fontsize=11)
    ax.set_xticks(range(len(AGE_ORDER)))
    ax.set_xticklabels(AGE_ORDER, rotation=30, ha="right")
    ax.legend(title="Survey year")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_status_composition(comp: pd.DataFrame, path: Path) -> None:
    order = ["Uses AI", "Plans to adopt", "No plans"]
    comp = comp.reindex(columns=[c for c in order if c in comp.columns])
    fig, ax = plt.subplots(figsize=(8, 5))
    bottom = np.zeros(len(comp))
    colors = {"Uses AI": "#2c7fb8", "Plans to adopt": "#7fcdbb", "No plans": "#d95f0e"}
    for col in comp.columns:
        vals = comp[col].values * 100
        ax.bar(comp.index.astype(str), vals, bottom=bottom, label=col,
               color=colors.get(col))
        bottom += vals
    ax.set_ylabel("Share of respondents (%)")
    ax.set_title("AI usage status composition (AISelect), 2023-2025", fontsize=11)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def _fmt_pct(x: float) -> str:
    return "n/a" if (x is None or (isinstance(x, float) and math.isnan(x))) else f"{x*100:.1f}%"


def write_markdown(summary, sen, age_df, comp, overlap_note, out_path: Path) -> None:
    lines = ["# AI Adoption Analysis 2023-2025", ""]
    lines.append("Adopter = `AISelect` answer that starts with \"Yes\" "
                 "(harmonizes the 2025 daily/weekly/monthly split with the "
                 "2023-2024 single \"Yes\"). CIs are Wilson 95%.\n")

    lines.append("## Per-year coverage and overall adoption\n")
    lines.append("| Year | n | AI_Usage_Status src | non-null | AI_Tool_Usage src | non-null | Adoption (Yes) | 95% CI | exp. source | proxy |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for _, r in summary.iterrows():
        lines.append(
            f"| {int(r.Year)} | {int(r.n_total):,} | `{r.status_source}` | "
            f"{int(r.status_nonnull):,} | `{r.tool_source}` | {int(r.tool_nonnull):,} | "
            f"{_fmt_pct(r.adoption_rate)} | [{_fmt_pct(r.adoption_ci_low)}, {_fmt_pct(r.adoption_ci_high)}] | "
            f"`{r.experience_source}` | {'YES' if r.experience_is_proxy else 'no'} |"
        )
    lines.append("")
    lines.append(overlap_note)
    lines.append("")

    lines.append("## AISelect composition (share of non-null responses)\n")
    lines.append("| Year | " + " | ".join(comp.columns) + " |")
    lines.append("|---|" + "---|" * len(comp.columns))
    for year, row in comp.iterrows():
        lines.append(f"| {int(year)} | " + " | ".join(_fmt_pct(v) for v in row.values) + " |")
    lines.append("")

    lines.append("## Adoption by professional seniority\n")
    lines.append("| Year | Seniority | n | adopters | rate | 95% CI | proxy |")
    lines.append("|---|---|---|---|---|---|---|")
    for _, r in sen.iterrows():
        lines.append(
            f"| {int(r.Year)} | {r.Seniority} | {int(r.n_valid):,} | {int(r.adopters):,} | "
            f"{_fmt_pct(r.adoption_rate)} | [{_fmt_pct(r.ci_low)}, {_fmt_pct(r.ci_high)}] | "
            f"{'YES' if r.experience_is_proxy else 'no'} |"
        )
    lines.append("")

    lines.append("## Adoption by age band\n")
    lines.append("| Year | Age | n | adopters | rate | 95% CI |")
    lines.append("|---|---|---|---|---|---|")
    for _, r in age_df.iterrows():
        lines.append(
            f"| {int(r.Year)} | {r.Age} | {int(r.n_valid):,} | {int(r.adopters):,} | "
            f"{_fmt_pct(r.adoption_rate)} | [{_fmt_pct(r.ci_low)}, {_fmt_pct(r.ci_high)}] |"
        )
    out_path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def run(raw_dir: Path, out_dir: Path, fig_dir: Path) -> dict:
    frames = [load_year(raw_dir, y) for y in YEAR_CONFIG]
    df = pd.concat(frames, ignore_index=True)

    summary = per_year_summary(df)
    sen = adoption_by_seniority(df)
    age_df = adoption_by_age(df)
    comp = status_composition(df)

    # overlap narrative
    overlap_bits = []
    for _, r in summary.iterrows():
        overlap_bits.append(
            f"{int(r.Year)}: {int(r.overlap_status_and_tool):,} rows have BOTH "
            f"AI_Usage_Status and AI_Tool_Usage non-null"
            + ("" if r.tool_nonnull else " (AI_Tool_Usage absent this year)")
        )
    overlap_note = "**Overlap of the two AI variables (non-null rows):** " + "; ".join(overlap_bits) + "."

    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    # tidy metrics csv
    sen.assign(kind="by_seniority").to_csv(out_dir / "ai_adoption_metrics.csv", index=False)
    with open(out_dir / "ai_adoption_metrics.csv", "a", encoding="utf-8") as fh:
        age_df.assign(kind="by_age").to_csv(fh, index=False, header=False)

    summary.to_csv(out_dir / "ai_per_year_summary.csv", index=False)
    write_markdown(summary, sen, age_df, comp, overlap_note, out_dir / "ai_adoption_summary.md")

    plot_by_seniority(sen, fig_dir / "ai_adoption_by_seniority.png")
    plot_by_age(age_df, fig_dir / "ai_adoption_by_age.png")
    plot_status_composition(comp, fig_dir / "ai_status_composition.png")

    return {"summary": summary, "seniority": sen, "age": age_df, "composition": comp}


def main() -> int:
    here = Path(__file__).resolve()
    project_root = here.parents[2]
    # Default raw dir: sibling project data folder (../../.. /data/raw), else env.
    candidates = [
        project_root / "data" / "raw",
        project_root.parent / "data" / "raw",
    ]
    raw_dir = next((c for c in candidates if (c / "results_2023.csv").is_file()), candidates[0])
    out_dir = project_root / "outputs" / "ai"
    fig_dir = project_root / "outputs" / "figures"
    print(f"Reading raw survey files from: {raw_dir}")
    res = run(raw_dir, out_dir, fig_dir)
    print(res["summary"].to_string(index=False))
    print(f"\nWrote report to {out_dir/'ai_adoption_summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
