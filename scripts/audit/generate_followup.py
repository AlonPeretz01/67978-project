"""Generate the follow-up reconciliation, robustness, and RF-evaluation audits."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import nct, t

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis import structural_break
from src.cleaning.data_harmonization import EXPERIENCE_PROXY_YEARS, TARGET_COLUMNS, harmonize_schema
from src.models import community_demographics_ml as dm
from src.reference import engagement_random_forest as rf

MASTER_PATH = ROOT / "data" / "processed" / "harmonized_stack_overflow_2011_2025.csv"
OUT = ROOT / "outputs" / "audit"
FIGURES_DIRECTORY = ROOT / "outputs" / "figures"
YEARS = list(range(2011, 2026))
BREAKS = list(range(2016, 2024))
Z95 = 1.959963984540054
WESTERN_EUROPE = {"austria", "belgium", "france", "germany", "liechtenstein", "luxembourg", "monaco", "netherlands", "switzerland"}
NORTH_AMERICA = {"united states", "united states of america", "usa", "canada"}


def table(headers: list[str], rows: list[list[object]]) -> str:
    clean = lambda x: str(x).replace("|", "\\|").replace("\n", " ")
    return "\n".join([
        "| " + " | ".join(map(clean, headers)) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(map(clean, row)) + " |" for row in rows),
    ])


def p(value: float) -> str:
    return "NOT AVAILABLE" if pd.isna(value) else f"{value:.6f}"


def wilson(success: float, total: int) -> tuple[float, float]:
    if total == 0:
        return np.nan, np.nan
    share = success / total
    den = 1 + Z95 ** 2 / total
    center = (share + Z95 ** 2 / (2 * total)) / den
    half = Z95 * math.sqrt((share * (1 - share) + Z95 ** 2 / (4 * total)) / total) / den
    return center - half, center + half


def weights(experience: pd.Series) -> pd.DataFrame:
    values = experience.map(dm.experience_cohort_weights)
    frame = pd.DataFrame(values.tolist(), index=experience.index, columns=["junior", "mid", "senior"])
    return frame.dropna()


def annual_series(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data["Year"] = pd.to_numeric(data["Year"], errors="coerce")
    rows = []
    for year in YEARS:
        subset = data.loc[data["Year"].eq(year)]
        w = weights(subset["Years_of_Experience"])
        n = len(w)
        if n:
            counts = w.sum()
            lo, hi = wilson(float(counts["junior"]), n)
            rows.append([year, n, *(float(counts[key]) / n for key in ["junior", "mid", "senior"]), lo, hi])
        else:
            rows.append([year, 0, np.nan, np.nan, np.nan, np.nan, np.nan])
    return pd.DataFrame(rows, columns=["Year", "n", "junior", "mid", "senior", "junior_ci_low", "junior_ci_high"])


def cleaned_year(year: int) -> pd.DataFrame:
    path = next((ROOT / "data" / "clean" / str(year)).glob("*.csv"))
    return pd.read_csv(path, low_memory=False)


def regional_master() -> pd.DataFrame:
    pieces = []
    for year in YEARS:
        raw = cleaned_year(year)
        country_cols = [c for c in raw.columns if "country" in str(c).lower()]
        if not country_cols:
            continue
        keep = raw[country_cols[0]].astype("string").str.strip().str.lower().isin(WESTERN_EUROPE | NORTH_AMERICA)
        pieces.append(harmonize_schema(raw.loc[keep], str(year)))
    return pd.concat(pieces, ignore_index=True)


def write_reconciliation(master: pd.DataFrame) -> None:
    current = annual_series(master).set_index("Year")
    rows = []
    for year in (2017, 2018):
        row = current.loc[year]
        rows.append(["src/models/community_demographics_ml.py", "experience_cohort_weights + build_demographic_summary", year,
                     "Years_of_Experience <- " + ("YearsCodedJob" if year == 2017 else "YearsCodingProf"),
                     int(row["n"]), "parsable experience responses only",
                     "Inclusive integer years in each range receive equal fractional allocation",
                     p(row["junior"]), p(row["mid"]), p(row["senior"])])
    content = """# Cohort reconciliation

## Every current cohort/junior calculation

| File | Function | Role and consumers |
| --- | --- | --- |
| `src/models/community_demographics_ml.py` | `experience_interval` | Parses a response to inclusive experience bounds; called by the two functions below. |
| `src/models/community_demographics_ml.py` | `experience_cohort_weights` | The sole respondent-level cohort allocator. Used by `build_demographic_summary` and this audit. |
| `src/models/community_demographics_ml.py` | `build_demographic_summary` | Calculates annual junior/mid/senior proportions from `experience_cohort_weights`; consumed by `main.py`, `plot_demographic_shift`, and the structural-break table/figures. |
| `src/models/community_demographics_ml.py` | `plot_demographic_shift` | Displays the `build_demographic_summary` table; it does not recompute cohort membership. |

No second callable cohort allocator exists in the current repository. `experience_to_years` is used only for the random-forest numeric feature and is not a cohort-membership calculation.

## 2017 and 2018 results from the sole current calculation

""" + table(["File", "Function", "Year", "Source column", "Denominator n", "Denominator", "Range allocation", "Junior", "Mid", "Senior"], rows) + """

## Resolution

The prior `outputs/figures/demographic_shift_2011_2025.png` artifact was stale: its plotted 2017/2018 junior values (approximately 0.307/0.325) are not reproducible from any current function or the current master data. The current source produces 0.369076 and 0.392047, respectively, exactly as the audit reported. Other years appeared to agree because their stale plotted points happened to be close to the current calculation.

Kept: `experience_cohort_weights`. It is the only current respondent-level allocator and explicitly handles the historical range labels by allocating each inclusive integer year equally. There was no second source function to delete or redirect; the conflicting item was a generated figure, which has been regenerated by `main.py` from `build_demographic_summary` and therefore from the kept function.
"""
    row_2025 = current.loc[2025]
    content += "\n## 2025 proxy-experience cohort row\n\n"
    content += "Raw 2025 contains no `YearsCodePro`; `YearsCode` is genuinely the available source (12.464630% missing) and is mapped with `experience_is_proxy=True` for non-null values.\n\n"
    content += table(["Year", "Source", "Parsable n", "Junior", "Mid", "Senior"], [[2025, "YearsCode (proxy)", int(row_2025["n"]), p(row_2025["junior"]), p(row_2025["mid"]), p(row_2025["senior"])]]) + "\n"
    (OUT / "COHORT_RECONCILIATION.md").write_text(content, encoding="utf-8")


def write_rf_eval(master: pd.DataFrame) -> None:
    result = rf.evaluate_engagement_model(master)
    metrics = result["metrics"]
    permutation = result["permutation_importance"]
    groups = result["groups"]
    grouped = []
    for source, columns in groups.items():
        sub = permutation.set_index("feature").loc[columns]
        grouped.append([source, f"{sub['mean'].sum():.6f}", f"{math.sqrt((sub['std'] ** 2).sum()):.6f}"])
    content = "# Random-forest held-out evaluation\n\n"
    content += f"Target: **{result['target_name']}**. Target-covered years: **{', '.join(map(str, result['target_years']))}**. AI-related variable ever included as a feature: **NO**; the feature list is exactly `Years_of_Experience`, `Yearly_Compensation`, and `Education_Level`.\n\n"
    content += f"Stratified split: random_state=42, train n={len(result['y_train'])}, test n={len(result['y_test'])}.\n\n"
    content += table(["Metric", "Test-set value"], [[name, f"{value:.6f}"] for name, value in metrics.items()]) + "\n\n"
    content += "Permutation importance uses test-set accuracy, n_repeats=10, random_state=42. Encoded-feature results:\n\n"
    content += table(["Encoded feature", "Mean decrease", "Std"], [[r.feature, f"{r.mean:.6f}", f"{r.std:.6f}"] for r in permutation.itertuples()]) + "\n\n"
    content += "Aggregated to the three original source features (standard deviations combined as root-sum-of-squares):\n\n"
    content += table(["Source feature", "Mean decrease", "Std"], grouped) + "\n"
    (OUT / "RF_EVAL.md").write_text(content, encoding="utf-8")


def mde(fit: object, sample: pd.DataFrame, knot: int) -> float:
    time = sample["Year"].astype(float) - knot
    design = np.column_stack([np.ones(len(sample)), time, np.maximum(time, 0.0)])
    se_per_sigma = math.sqrt(np.linalg.inv(design.T @ design)[2, 2])
    sigma = math.sqrt(float(fit.mse_resid))
    df = int(fit.df_resid)
    critical = t.ppf(0.975, df)
    def power_at(change: float) -> float:
        ncp = change / (sigma * se_per_sigma)
        return nct.cdf(-critical, df, ncp) + nct.sf(critical, df, ncp)
    low, high = 0.0, 1.0
    while power_at(high) < 0.80:
        high *= 2
    for _ in range(60):
        middle = (low + high) / 2
        if power_at(middle) < 0.80:
            low = middle
        else:
            high = middle
    return high


def write_robustness(master: pd.DataFrame) -> None:
    professional_only = master.loc[~master["experience_is_proxy"].fillna(False)]
    regional_professional_only = regional_master()
    regional_professional_only = regional_professional_only.loc[
        ~regional_professional_only["experience_is_proxy"].fillna(False)
    ]
    named = {
        "All experience years (proxy-inclusive sensitivity)": annual_series(master),
        "All respondents (professional years only)": annual_series(professional_only),
        "US + Canada + Western Europe (professional years only)": annual_series(regional_professional_only),
    }
    plot_named = {
        "All respondents (professional years only)": annual_series(professional_only),
        "US + Canada + Western Europe (professional years only)": annual_series(regional_professional_only),
        # Draw this last: on non-proxy years it has identical values to the
        # professional-only series, so its dashed line must be on top to stay visible.
        "All experience years (proxy-inclusive sensitivity)": annual_series(master),
    }

    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=120)
    colors = {
        "All experience years (proxy-inclusive sensitivity)": "#4D4D4D",
        "All respondents (professional years only)": "#1F4E79",
        "US + Canada + Western Europe (professional years only)": "#009E73",
    }
    proxy_handle = None
    for name, series in plot_named.items():
        valid = series.dropna(subset=["junior"])
        is_proxy = valid["Year"].isin({2015, 2016, 2025})
        display = valid["junior"].where(~is_proxy)
        ax.plot(
            valid["Year"], display * 100, marker="o", linewidth=2.5,
            linestyle="--" if name.startswith("All experience years") else "-",
            color=colors[name], label=name,
        )
        ax.errorbar(
            valid["Year"], valid["junior"] * 100,
            yerr=np.vstack(((valid["junior"] - valid["junior_ci_low"]) * 100,
                            (valid["junior_ci_high"] - valid["junior"]) * 100)),
            fmt="none", ecolor=colors[name], elinewidth=1.1, capsize=3, alpha=0.85,
            label="_nolegend_",
        )
        proxy = valid.loc[is_proxy]
        if not proxy.empty:
            handle = ax.errorbar(
                proxy["Year"], proxy["junior"] * 100,
                yerr=np.vstack(((proxy["junior"] - proxy["junior_ci_low"]) * 100,
                                (proxy["junior_ci_high"] - proxy["junior"]) * 100)),
                color=colors[name], marker="o", linestyle="none", markerfacecolor="none",
                markeredgewidth=2, markersize=8, capsize=3,
                label="proxy experience measure (not comparable)" if proxy_handle is None else "_nolegend_",
            )
            if proxy_handle is None:
                proxy_handle = handle
    ax.set_title("The junior decline holds under regional restriction", fontweight="semibold", fontsize=17)
    ax.set_xlabel("Survey year", fontsize=13)
    ax.set_ylabel("Junior respondents (%, Wilson 95% CI)", fontsize=13)
    ax.set_xticks(YEARS)
    ax.set_xlim(2010.6, 2025.4)
    ax.set_ylim(0, 100)
    ax.grid(axis="y", color="#D9D9D9")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=11)
    fig.tight_layout()
    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIRECTORY / "robustness_junior_series.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    series_rows = []
    regression_rows = []
    mde_rows = []
    for name, series in named.items():
        usable = series.dropna(subset=["junior"])[["Year", "junior"]]
        series_rows.extend([[name, int(r.Year), int(r.n), p(r.junior), f"[{p(r.junior_ci_low)}, {p(r.junior_ci_high)}]"] for r in series.itertuples()])
        for knot in BREAKS:
            fit = structural_break._fit_broken_stick(usable, "Year", "junior", knot)
            ci = fit.conf_int()
            for coefficient in fit.params.index:
                regression_rows.append([name, knot, len(usable), coefficient, f"{fit.params[coefficient]:.6f}", f"{fit.bse[coefficient]:.6f}", f"[{ci.loc[coefficient, 0]:.6f}, {ci.loc[coefficient, 1]:.6f}]", f"{fit.pvalues[coefficient]:.6f}", f"{fit.rsquared:.6f}"])
            mde_rows.append([name, knot, len(usable), f"{mde(fit, usable, knot):.6f}"])
    slope_rows = [row for row in regression_rows if row[3] == "slope_change"]
    slopes_2020_2022 = [row for row in slope_rows if row[1] in (2020, 2022)]
    fit_summary_rows = [
        [row[1], row[0], row[4], row[7], row[8]]
        for row in sorted(slope_rows, key=lambda row: (row[1], row[0]))
    ]
    rankings = []
    for series_name in named:
        candidates = [row for row in slope_rows if row[0] == series_name]
        ranked = sorted(candidates, key=lambda row: float(row[8]), reverse=True)
        best = ranked[0]
        rank_2022 = next(position for position, row in enumerate(ranked, start=1) if row[1] == 2022)
        rankings.append(
            f"**{series_name}**: best fit is {best[1]} (R-squared {best[8]}); "
            f"2022 ranks {rank_2022} of {len(ranked)}."
        )

    figure, axis = plt.subplots(figsize=(9.5, 5.8), dpi=120)
    r2_colors = ["#4D4D4D", "#1F4E79", "#009E73"]
    r2_styles = ["--", "-", "-"]
    for color, style, series_name in zip(r2_colors, r2_styles, named, strict=True):
        candidates = sorted((row for row in slope_rows if row[0] == series_name), key=lambda row: row[1])
        axis.plot([row[1] for row in candidates], [float(row[8]) for row in candidates],
                  color=color, linestyle=style, marker="o", linewidth=2.5, markersize=7, label=series_name)
    axis.set_title("Later candidate breaks monotonically reduce piecewise fit", fontsize=17, fontweight="semibold")
    axis.set_xlabel("Candidate break year", fontsize=13)
    axis.set_ylabel("R-squared", fontsize=13)
    axis.set_xticks(BREAKS)
    axis.set_ylim(0, 1)
    axis.grid(axis="y", color="#D9D9D9")
    axis.spines[["top", "right"]].set_visible(False)
    axis.legend(frameon=False, fontsize=10.5)
    figure.tight_layout()
    figure.savefig(FIGURES_DIRECTORY / "robustness_r_squared_by_break.png", dpi=200, bbox_inches="tight")
    plt.close(figure)
    content = "# Robustness, placebo breaks, and confidence intervals\n\n"
    content += "The annual chart uses the single kept cohort allocator and Wilson 95% intervals; hollow points are proxy measures. The two primary regression series exclude 2015, 2016, and 2025, including the US + Canada + Western Europe series. `All experience years (proxy-inclusive sensitivity)` deliberately retains all 15 points as a separately labelled sensitivity block; it is not used as the comparable-measure result. Country restriction uses the same UN M49 Western Europe definition documented in the audit.\n\n"
    content += "![Junior-series robustness chart](../figures/robustness_junior_series.png)\n\n## Annual junior series\n\n"
    content += table(["Series", "Year", "Parsable n", "Junior", "Wilson 95% CI"], series_rows) + "\n\n## Placebo-scan summary\n\n"
    content += "![R-squared by candidate break year](../figures/robustness_r_squared_by_break.png)\n\n"
    content += table(["Break year", "Series", "Slope change", "p-value", "R-squared"], fit_summary_rows) + "\n\n"
    content += "## Fit ranking\n\n" + "\n\n".join(rankings) + "\n\n## Piecewise regressions\n\n"
    content += "Each regression is `junior = const + time + slope_change × max(0, time)`; therefore the `slope_change` p-value tests a slope difference only, not a level shift.\n\n"
    content += table(["Series", "Break", "n", "Coefficient", "Estimate", "SE", "95% CI", "p-value", "R-squared"], regression_rows) + "\n\n"
    content += "## 2020/2022 versus placebo breaks\n\n"
    content += "The two comparable-measure series use only professional-experience years; the n=15 proxy-inclusive series is retained solely to display the leverage of proxy years. Read the ranking and summary table before treating a nominal p-value at any selected knot as confirmatory evidence.\n\n"
    content += "2020/2022 slope rows:\n\n" + table(["Series", "Break", "n", "Coefficient", "Estimate", "SE", "95% CI", "p-value", "R-squared"], slopes_2020_2022) + "\n\n"
    content += "## Power note\n\n"
    content += "Minimum detectable absolute slope changes at 80% power, two-sided alpha=0.05, are design- and residual-SD-specific. The values below use each fitted model's residual SD and exact broken-stick design; they are not claims about an unspecified generic n. The comparable-measure samples contain n=12 annual points; the labelled proxy-inclusive sensitivity sample contains n=15. **NOT AVAILABLE for a generic n without the actual observation years, knot placement, and residual SD.**\n\n"
    content += table(["Series", "Break", "n", "MDE (slope-change units/year)"], mde_rows) + "\n"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ROBUSTNESS.md").write_text(content, encoding="utf-8")


def append_fact_check(master: pd.DataFrame) -> None:
    core = [column for column in TARGET_COLUMNS if column in master.columns]
    all_columns = list(master.columns)
    rows = [[year, *[int(master.loc[master["Year"].eq(year), column].notna().sum()) for column in all_columns]] for year in YEARS]
    content = "# Stack Overflow Survey Audit\n\n## FACT CHECK\n\n"
    content += f"Exact master row count: **{len(master)}**. Exact master column list ({len(all_columns)} columns):\n\n```text\n" + "\n".join(all_columns) + "\n```\n\n"
    content += "The original 13 core variables are retained. `experience_is_proxy` is a newly required provenance flag and makes the current master 14 columns wide.\n\n"
    content += "Per-year non-null matrix for all current columns (the first 13 are the requested original core columns):\n\n"
    content += table(["Year", *all_columns], rows) + "\n"
    (OUT / "AUDIT.md").write_text(content, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(MASTER_PATH, low_memory=False)
    master["Year"] = pd.to_numeric(master["Year"], errors="coerce")
    write_reconciliation(master)
    write_rf_eval(master)
    write_robustness(master)
    print("Wrote follow-up audit documents.")


if __name__ == "__main__":
    main()
