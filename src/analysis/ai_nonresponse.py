"""Non-response bias check for the AI usage question (AISelect), 2023-2025.

Motivation
----------
AISelect response coverage fell from ~99% (2023) to ~68% (2025). If the people
who skipped the AI question differ systematically from those who answered
(e.g. skew older / more senior, who adopt AI less), then the adoption rate
computed among answerers is biased upward.

This script:
  1. Computes the AISelect response rate by age band and by seniority cohort,
     for each year, to see WHO is missing.
  2. Reports Manski-style worst/best-case bounds on overall adoption:
       - lower bound: assume every non-responder is a non-adopter
       - upper bound: assume every non-responder is an adopter
     The width of this band shows how much the missingness could move the
     headline number.

Outputs:
  outputs/ai/ai_nonresponse_2023_2025.md
  outputs/figures/ai_response_rate_by_age.png
  outputs/figures/ai_response_rate_by_seniority.png
"""

from __future__ import annotations

from pathlib import Path
import math

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analysis.ai_adoption import (
    YEAR_CONFIG,
    AGE_ORDER,
    COHORT_ORDER,
    parse_experience_years,
    experience_to_cohort,
    is_adopter,
)


def load_year_full(raw_dir: Path, year: int) -> pd.DataFrame:
    cfg = YEAR_CONFIG[year]
    path = raw_dir / f"results_{year}.csv"
    cols = pd.read_csv(path, nrows=0).columns.tolist()
    use = [c for c in (cfg["ai_status"], cfg["experience"], cfg["age"]) if c in cols]
    raw = pd.read_csv(path, usecols=use, low_memory=False)
    out = pd.DataFrame(index=raw.index)
    out["Year"] = year
    out["answered"] = raw[cfg["ai_status"]].notna()
    out["is_adopter"] = raw[cfg["ai_status"]].map(is_adopter)
    out["Age"] = raw[cfg["age"]]
    out["Seniority"] = raw[cfg["experience"]].map(parse_experience_years).map(experience_to_cohort)
    return out


def response_rate_by(df: pd.DataFrame, col: str, order: list[str]) -> pd.DataFrame:
    rows = []
    for year, g in df.groupby("Year"):
        for cat in order:
            sub = g[g[col] == cat]
            n = len(sub)
            answered = int(sub["answered"].sum())
            rows.append(dict(Year=year, category=cat,
                             n=n, answered=answered,
                             response_rate=(answered / n if n else math.nan)))
    return pd.DataFrame(rows)


def manski_bounds(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, g in df.groupby("Year"):
        n_total = len(g)
        answered = g[g["answered"]]
        n_ans = len(answered)
        adopters = int((answered["is_adopter"] == True).sum())  # noqa: E712
        missing = n_total - n_ans
        observed = adopters / n_ans if n_ans else math.nan
        lower = adopters / n_total                    # all missing = non-adopter
        upper = (adopters + missing) / n_total        # all missing = adopter
        rows.append(dict(Year=year, n_total=n_total, answered=n_ans,
                         missing=missing, coverage=n_ans / n_total,
                         observed_adoption=observed,
                         lower_bound=lower, upper_bound=upper,
                         bound_width=upper - lower))
    return pd.DataFrame(rows)


def plot_response_rate(rr: pd.DataFrame, order: list[str], title: str, path: Path) -> None:
    years = sorted(rr["Year"].unique())
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for year in years:
        g = rr[rr["Year"] == year].set_index("category").reindex(order)
        ax.plot(order, g["response_rate"].values * 100, marker="o", label=str(year))
    ax.set_ylabel("AISelect response rate (%)")
    ax.set_ylim(0, 105)
    ax.set_title(title, fontsize=11)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(order, rotation=30, ha="right")
    ax.legend(title="Survey year")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _pct(x): return "n/a" if (x is None or (isinstance(x, float) and math.isnan(x))) else f"{x*100:.1f}%"


def run(raw_dir: Path, out_dir: Path, fig_dir: Path) -> dict:
    df = pd.concat([load_year_full(raw_dir, y) for y in YEAR_CONFIG], ignore_index=True)
    by_age = response_rate_by(df, "Age", AGE_ORDER)
    by_sen = response_rate_by(df, "Seniority", COHORT_ORDER)
    bounds = manski_bounds(df)

    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    plot_response_rate(by_age, AGE_ORDER, "Who answered the AI question? Response rate by age", fig_dir / "ai_response_rate_by_age.png")
    plot_response_rate(by_sen, COHORT_ORDER, "Who answered the AI question? Response rate by seniority", fig_dir / "ai_response_rate_by_seniority.png")

    lines = ["# AI question non-response bias, 2023-2025", ""]
    lines.append("## Manski bounds on overall adoption\n")
    lines.append("`observed` = adoption among answerers. `lower` assumes every "
                 "non-responder is a non-adopter; `upper` assumes every "
                 "non-responder is an adopter. The true value must lie in "
                 "[lower, upper]; a wide band = missingness matters a lot.\n")
    lines.append("| Year | n | answered | coverage | observed | lower | upper | band width |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for _, r in bounds.iterrows():
        lines.append(f"| {int(r.Year)} | {int(r.n_total):,} | {int(r.answered):,} | "
                     f"{_pct(r.coverage)} | {_pct(r.observed_adoption)} | {_pct(r.lower_bound)} | "
                     f"{_pct(r.upper_bound)} | {_pct(r.bound_width)} |")
    lines.append("")
    lines.append("## Response rate by seniority\n")
    lines.append("| Year | " + " | ".join(COHORT_ORDER) + " |")
    lines.append("|---|" + "---|" * len(COHORT_ORDER))
    for year in sorted(df["Year"].unique()):
        g = by_sen[by_sen["Year"] == year].set_index("category").reindex(COHORT_ORDER)
        lines.append(f"| {int(year)} | " + " | ".join(_pct(v) for v in g["response_rate"].values) + " |")
    lines.append("")
    lines.append("## Response rate by age\n")
    lines.append("| Year | " + " | ".join(AGE_ORDER) + " |")
    lines.append("|---|" + "---|" * len(AGE_ORDER))
    for year in sorted(df["Year"].unique()):
        g = by_age[by_age["Year"] == year].set_index("category").reindex(AGE_ORDER)
        lines.append(f"| {int(year)} | " + " | ".join(_pct(v) for v in g["response_rate"].values) + " |")
    (out_dir / "ai_nonresponse_2023_2025.md").write_text("\n".join(lines), encoding="utf-8")

    return {"by_age": by_age, "by_sen": by_sen, "bounds": bounds}


def main() -> int:
    here = Path(__file__).resolve()
    project_root = here.parents[2]
    candidates = [project_root / "data" / "raw", project_root.parent / "data" / "raw"]
    raw_dir = next((c for c in candidates if (c / "results_2023.csv").is_file()), candidates[0])
    res = run(raw_dir, project_root / "outputs" / "ai", project_root / "outputs" / "figures")
    print(res["bounds"].to_string(index=False))
    print("\nResponse rate by seniority:")
    print(res["by_sen"].pivot(index="Year", columns="category", values="response_rate").reindex(columns=COHORT_ORDER).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
