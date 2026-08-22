"""Interactive presentation of the project's committed audit findings.

Every number displayed here is read from the markdown tables under
``outputs/audit/``. The app never loads the harmonized master CSV and never
fits a model. The two-slope line on the second tab is drawn by evaluating the
regression coefficients the audit already reports, not by refitting anything.
Values derived arithmetically from audit numbers are labelled as such on
screen.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]

# Category colours are fixed here and reused across every tab. The cohort
# colours are colour-vision-safe and are never reassigned to another category.
COHORT_COLOURS = {
    "junior": "#0072B2",
    "mid": "#E69F00",
    "senior": "#009E73",
}
SERIES_COLOURS = {
    "All respondents (professional years only)": "#0072B2",
    "US + Canada + Western Europe (professional years only)": "#009E73",
    "All experience years (proxy-inclusive sensitivity)": "#767676",
}
BELONGING_COLOURS = {
    "yes/agree": "#0072B2",
    "no/disagree": "#D55E00",
    "excluded": "#767676",
}
PARTICIPATION_COLOUR = "#CC79A7"
NONRESPONSE_COLOUR = "#767676"
NEUTRAL_INK = "#333333"
MUTED_FILL = "#D6D6D6"
GRID_INK = "#E4E4E4"

PROXY_YEARS = (2015, 2016, 2025)
CANDIDATE_BREAKS = list(range(2016, 2024))
SERIES_ORDER = [
    "All respondents (professional years only)",
    "US + Canada + Western Europe (professional years only)",
    "All experience years (proxy-inclusive sensitivity)",
]

# Type sizes live here and nowhere else. They sit above the floors in
# docs/figure-conventions/SKILL.md section 9, which allows scaling up for
# presentation use; this app is meant to be read on a projector or a shared
# screen, where the 11-12pt tick floor is too small.
FONT = {
    "base": 17,
    "title": 25,
    "axis_title": 19,
    "tick": 16,
    "legend": 16,
    "annotation": 16,
}

# One layout template, registered once, so every chart in the app shares the
# same typography and spacing (docs/figure-conventions/SKILL.md section 9).
pio.templates["so_audit"] = go.layout.Template(
    layout=go.Layout(
        font={
            "family": "Source Sans Pro, sans-serif",
            "size": FONT["base"],
            "color": NEUTRAL_INK,
        },
        title={"font": {"size": FONT["title"]}, "x": 0.0, "xanchor": "left"},
        margin={"l": 90, "r": 40, "t": 90, "b": 80},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=list(COHORT_COLOURS.values()),
        legend={
            "font": {"size": FONT["legend"]},
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.0,
        },
        hoverlabel={"font": {"size": FONT["tick"]}},
        annotationdefaults={"font": {"size": FONT["annotation"]}},
        xaxis={
            "showgrid": False,
            "linecolor": GRID_INK,
            "ticks": "outside",
            "tickcolor": GRID_INK,
            "tickfont": {"size": FONT["tick"]},
            "title": {"font": {"size": FONT["axis_title"]}},
        },
        yaxis={
            "gridcolor": GRID_INK,
            "zeroline": False,
            "linecolor": GRID_INK,
            "tickfont": {"size": FONT["tick"]},
            "title": {"font": {"size": FONT["axis_title"]}},
        },
    )
)
pio.templates.default = "so_audit"

# Minimal type bump for Streamlit's own text. Streamlit sizes in rem, so
# raising the root size scales prose, widget labels and captions together.
BASE_TYPE_CSS = """
<style>
  html { font-size: 19px; }
  [data-testid="stMetricValue"] { font-size: 2.1rem; }
</style>
"""

PLOTLY_CONFIG = {"displayModeBar": False, "scrollZoom": False}


def show_chart(figure: go.Figure) -> None:
    """Render a chart. `theme=None` keeps the so_audit template's typography;
    Streamlit's default plotly theme would otherwise override the font sizes."""
    st.plotly_chart(figure, width="stretch", config=PLOTLY_CONFIG, theme=None)


def percent_axis(figure: go.Figure, title: str) -> None:
    """Percent axes run 0-100 with a percent suffix, on every chart."""
    figure.update_yaxes(range=[0, 100], ticksuffix="%", title_text=title)


# --------------------------------------------------------------------------
# Markdown table parsing
# --------------------------------------------------------------------------
def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\|[\s:\-|]+\|", line.strip()))


def _block_to_frame(block: list[str]) -> pd.DataFrame | None:
    if len(block) < 3 or not _is_separator(block[1]):
        return None
    header = _split_row(block[0])
    rows = [_split_row(line) for line in block[2:]]
    rows = [row for row in rows if len(row) == len(header)]
    if not rows:
        return None
    # Duplicate header names occur in the audit (the FACT CHECK table repeats
    # "Year"); those tables are addressed by column position instead.
    return pd.DataFrame(rows, columns=header)


@st.cache_data(show_spinner=False)
def load_tables(relative_path: str) -> dict[str, list[pd.DataFrame]]:
    """Return every markdown table in a file, keyed by its enclosing heading."""
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    tables: dict[str, list[pd.DataFrame]] = {}
    heading = "(preamble)"
    block: list[str] = []

    def flush() -> None:
        frame = _block_to_frame(block)
        if frame is not None:
            tables.setdefault(heading, []).append(frame)
        block.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            block.append(stripped)
            continue
        if block:
            flush()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
    if block:
        flush()
    return tables


def _num(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(",", "", regex=False)
    cleaned = cleaned.str.replace("%", "", regex=False).str.strip()
    return pd.to_numeric(cleaned, errors="coerce")


def _wilson(series: pd.Series) -> pd.DataFrame:
    parts = series.astype(str).str.strip("[] ").str.split(",", expand=True)
    return pd.DataFrame(
        {
            "ci_low": pd.to_numeric(parts[0].str.strip(), errors="coerce"),
            "ci_high": pd.to_numeric(parts[1].str.strip(), errors="coerce"),
        }
    )


# --------------------------------------------------------------------------
# Typed loaders over the audit tables
# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def cohort_series() -> pd.DataFrame:
    """Annual junior/mid/senior proportions with Wilson intervals (AUDIT.md)."""
    table = load_tables("outputs/audit/AUDIT.md")["EXPERIENCE COHORTS"][0]
    frame = pd.DataFrame({"Year": _num(table["Year"]).astype(int)})
    frame["n_total"] = _num(table["n_total"])
    frame["n_parsable"] = _num(table["n_with_valid_experience"])
    for cohort in ("junior", "mid", "senior"):
        frame[cohort] = _num(table[f"{cohort} proportion"])
        bounds = _wilson(table[f"{cohort} Wilson 95% CI"])
        frame[f"{cohort}_lo"] = bounds["ci_low"]
        frame[f"{cohort}_hi"] = bounds["ci_high"]
    frame["is_proxy"] = frame["Year"].isin(PROXY_YEARS)
    return frame


@st.cache_data(show_spinner=False)
def junior_by_series() -> pd.DataFrame:
    """The three regression samples' annual junior shares (ROBUSTNESS.md)."""
    table = load_tables("outputs/audit/ROBUSTNESS.md")["Annual junior series"][0]
    frame = pd.DataFrame(
        {
            "series": table["Series"],
            "Year": _num(table["Year"]).astype(int),
            "n": _num(table["Parsable n"]),
            "junior": _num(table["Junior"]),
        }
    )
    bounds = _wilson(table["Wilson 95% CI"])
    frame["ci_low"] = bounds["ci_low"]
    frame["ci_high"] = bounds["ci_high"]
    # Rows reading NOT AVAILABLE parse to NaN and are dropped; the audit marks
    # 2015, 2016 and 2025 that way for the professional-years samples.
    return frame.dropna(subset=["junior"]).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def placebo_scan() -> pd.DataFrame:
    """Slope change, p-value and R-squared per candidate break (ROBUSTNESS.md)."""
    table = load_tables("outputs/audit/ROBUSTNESS.md")["Placebo-scan summary"][0]
    frame = pd.DataFrame(
        {
            "break_year": _num(table["Break year"]).astype(int),
            "series": table["Series"],
            "slope_change": _num(table["Slope change"]),
            "p_value": _num(table["p-value"]),
            "r_squared": _num(table["R-squared"]),
        }
    )
    frame["rank"] = (
        frame.groupby("series")["r_squared"].rank(ascending=False, method="min").astype(int)
    )
    return frame


@st.cache_data(show_spinner=False)
def piecewise_coefficients() -> pd.DataFrame:
    """Fitted const / time / slope_change per series and break (ROBUSTNESS.md).

    These are the audit's own estimates. The app only evaluates them; it never
    refits the model.
    """
    table = load_tables("outputs/audit/ROBUSTNESS.md")["Piecewise regressions"][0]
    frame = pd.DataFrame(
        {
            "series": table["Series"],
            "break_year": _num(table["Break"]).astype(int),
            "coefficient": table["Coefficient"],
            "estimate": _num(table["Estimate"]),
        }
    )
    return frame.pivot_table(
        index=["series", "break_year"], columns="coefficient", values="estimate"
    ).reset_index()


@st.cache_data(show_spinner=False)
def mde_table() -> pd.DataFrame:
    """Minimum detectable slope change per break year per series."""
    table = load_tables("outputs/audit/ROBUSTNESS.md")["Power note"][0]
    return pd.DataFrame(
        {
            "series": table["Series"],
            "break_year": _num(table["Break"]).astype(int),
            "n": _num(table["n"]).astype(int),
            "mde": _num(table["MDE (slope-change units/year)"]),
        }
    )


@st.cache_data(show_spinner=False)
def belonging_series() -> pd.DataFrame:
    """Yes / no / excluded belonging shares per year (COMMUNITY.md)."""
    table = load_tables("outputs/audit/COMMUNITY.md")["Belonging, 2017-2025"][0]
    frame = pd.DataFrame(
        {
            "Year": _num(table["Year"]).astype(int),
            "answered": _num(table["n answered"]),
            "n_total": _num(table["n total"]),
            "nonresponse": _num(table["non-response rate"]),
        }
    )
    for key in ("yes/agree", "no/disagree", "excluded"):
        frame[f"{key}_count"] = _num(table[f"{key} count"])
        frame[key] = _num(table[f"{key} share"])
        bounds = _wilson(table[f"{key} Wilson 95% CI"])
        frame[f"{key}_lo"] = bounds["ci_low"]
        frame[f"{key}_hi"] = bounds["ci_high"]
    return frame


@st.cache_data(show_spinner=False)
def participation_series() -> pd.DataFrame:
    """Frequent-participation share per year (COMMUNITY.md)."""
    heading = "Participation at least a few times per month, 2019-2025"
    table = load_tables("outputs/audit/COMMUNITY.md")[heading][0]
    frame = pd.DataFrame(
        {
            "Year": _num(table["Year"]).astype(int),
            "answered": _num(table["n answered"]),
            "n_total": _num(table["n total"]),
            "nonresponse": _num(table["non-response rate"]),
            "frequent_count": _num(table["frequent count"]),
            "frequent": _num(table["frequent share"]),
        }
    )
    bounds = _wilson(table["frequent Wilson 95% CI"])
    frame["frequent_lo"] = bounds["ci_low"]
    frame["frequent_hi"] = bounds["ci_high"]
    return frame


@st.cache_data(show_spinner=False)
def category_mapping(question: str) -> pd.DataFrame:
    """Raw response categories and what each maps to (COMMUNITY.md)."""
    heading = f"{question} raw-category mapping"
    table = load_tables("outputs/audit/COMMUNITY.md")[heading][0]
    return pd.DataFrame(
        {
            "Year": _num(table["Year"]).astype(int),
            "Raw response category": table["Raw response category"],
            "Count": _num(table["Count"]).astype(int),
            "Mapped figure value": table["Mapped figure value"],
        }
    )


@st.cache_data(show_spinner=False)
def cluster_sizes() -> pd.DataFrame:
    table = load_tables("outputs/audit/CLUSTERING.md")["5. Cluster sizes"][0]
    return pd.DataFrame(
        {
            "cluster": _num(table["Cluster"]).astype(int),
            "rows": _num(table["Rows"]).astype(int),
            "share": _num(table["Share of input"]) / 100.0,
        }
    )


@st.cache_data(show_spinner=False)
def cluster_composition() -> pd.DataFrame:
    table = load_tables("outputs/audit/CLUSTERING.md")["6. Composition table behind the heatmap"][0]
    return table.set_index("Category").apply(_num)


@st.cache_data(show_spinner=False)
def k_selection() -> pd.DataFrame:
    table = load_tables("outputs/audit/CLUSTERING.md")["2. Selection criterion and its value per K"][0]
    return pd.DataFrame(
        {
            "K": _num(table["K"]).astype(int),
            "cost": _num(table["Cost"]),
            "elbow_distance": _num(table["Elbow distance"]),
            "selected_by_elbow": table["Selected"].str.contains("YES"),
        }
    )


@st.cache_data(show_spinner=False)
def cluster_modal_profiles() -> pd.DataFrame:
    table = load_tables("outputs/audit/CLUSTERING.md")["7. Modal profile of every cluster"][0]
    return pd.DataFrame(
        {
            "cluster": _num(table["Cluster"]).astype(int),
            "column": table["Column"].str.strip("`"),
            "modal_value": table["Modal value"],
            "count": _num(table["Count"]),
            "share": _num(table["Share of cluster"]) / 100.0,
        }
    )


def consecutive_runs(years: list[int]) -> list[list[int]]:
    runs: list[list[int]] = []
    for year in years:
        if runs and year == runs[-1][-1] + 1:
            runs[-1].append(year)
        else:
            runs.append([year])
    return runs


# --------------------------------------------------------------------------
# Tab 1 — the claim
# --------------------------------------------------------------------------
def figure_cohorts(
    frame: pd.DataFrame, cohorts: list[str], show_proxy: bool, year_range: tuple[int, int]
) -> go.Figure:
    window = frame[frame["Year"].between(*year_range)]
    comparable = window[~window["is_proxy"]]
    proxy = window[window["is_proxy"]]
    figure = go.Figure()

    for cohort in cohorts:
        colour = COHORT_COLOURS[cohort]
        label = cohort.capitalize()
        # Comparable years are drawn as one trace per consecutive run, so no
        # line ever crosses a proxy year.
        for index, run in enumerate(consecutive_runs(list(comparable["Year"]))):
            block = comparable[comparable["Year"].isin(run)]
            figure.add_trace(
                go.Scatter(
                    x=block["Year"],
                    y=block[cohort] * 100,
                    mode="lines+markers",
                    name=label,
                    legendgroup=cohort,
                    showlegend=index == 0,
                    line={"color": colour, "width": 2.5},
                    marker={"color": colour, "size": 7},
                    error_y={
                        "type": "data",
                        "symmetric": False,
                        "array": (block[f"{cohort}_hi"] - block[cohort]) * 100,
                        "arrayminus": (block[cohort] - block[f"{cohort}_lo"]) * 100,
                        "color": colour,
                        "thickness": 1.2,
                        "width": 3,
                    },
                    hovertemplate=f"{label} %{{x}}<br>%{{y:.1f}}%<extra></extra>",
                )
            )
        if show_proxy and not proxy.empty:
            figure.add_trace(
                go.Scatter(
                    x=proxy["Year"],
                    y=proxy[cohort] * 100,
                    mode="markers",
                    name=f"{label}, general experience",
                    legendgroup=cohort,
                    showlegend=False,
                    marker={
                        "color": "rgba(0,0,0,0)",
                        "size": 10,
                        "line": {"color": colour, "width": 2},
                    },
                    error_y={
                        "type": "data",
                        "symmetric": False,
                        "array": (proxy[f"{cohort}_hi"] - proxy[cohort]) * 100,
                        "arrayminus": (proxy[cohort] - proxy[f"{cohort}_lo"]) * 100,
                        "color": colour,
                        "thickness": 1.2,
                        "width": 3,
                    },
                    hovertemplate=(
                        f"{label} %{{x}}, general experience<br>%{{y:.1f}}%<extra></extra>"
                    ),
                )
            )

    if show_proxy and not proxy.empty:
        figure.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                name="2015, 2016, 2025: general experience, not comparable",
                marker={
                    "color": "rgba(0,0,0,0)",
                    "size": 10,
                    "line": {"color": NEUTRAL_INK, "width": 2},
                },
            )
        )

    if "junior" in cohorts:
        for year, text, shift in ((2018, "2018 peak", 40), (2023, "2023 low", -40)):
            if year_range[0] <= year <= year_range[1]:
                value = frame.loc[frame["Year"] == year, "junior"].iloc[0] * 100
                figure.add_annotation(
                    x=year,
                    y=value,
                    text=f"{text}: {value:.1f}%",
                    showarrow=True,
                    arrowhead=0,
                    arrowcolor=COHORT_COLOURS["junior"],
                    ax=0,
                    ay=shift,
                    font={"color": COHORT_COLOURS["junior"], "size": FONT["annotation"]},
                )

    title = (
        "The junior share peaked in 2018 and fell through 2023"
        if "junior" in cohorts
        else "Cohort composition of survey respondents, 2011-2025"
    )
    figure.update_layout(title=title, height=600, hovermode="x unified")
    figure.update_xaxes(title_text="Survey year", dtick=1, tickangle=-45)
    percent_axis(figure, "Share of respondents with parsable experience")
    return figure


def tab_claim() -> None:
    frame = cohort_series()
    st.header("The claim")
    st.markdown(
        "Since the release of ChatGPT in November 2022, Stack Overflow has been "
        "widely described as losing its junior developers, on the argument that "
        "newcomers now ask a chat assistant instead of the site. The annual "
        "survey gives one way to check the composition claim: the share of "
        "respondents with three or fewer years of professional experience. That "
        "share is 39.2% in 2018 and 20.1% in 2023."
    )

    controls, spacer = st.columns([3, 2])
    with controls:
        boxes = st.columns(3)
        cohorts = [
            cohort
            for cohort, column in zip(("junior", "mid", "senior"), boxes)
            if column.checkbox(cohort.capitalize(), value=True, key=f"cohort_{cohort}")
        ]
        show_proxy = st.toggle("Proxy-experience years", value=True)
    with spacer:
        year_range = st.slider(
            "Year range",
            min_value=int(frame["Year"].min()),
            max_value=int(frame["Year"].max()),
            value=(int(frame["Year"].min()), int(frame["Year"].max())),
            step=1,
        )

    if not cohorts:
        st.info("Select at least one cohort.")
        return

    show_chart(figure_cohorts(frame, cohorts, show_proxy, year_range))
    st.caption(
        "Source: outputs/audit/AUDIT.md, EXPERIENCE COHORTS. Cohorts are junior "
        "(<=3 years), mid (4-7), senior (>=8); the allocator splits reported "
        "ranges across integer years, so counts are fractional. Error bars are "
        "Wilson 95% intervals on the parsable-response denominator."
    )
    st.markdown(
        "The 2015, 2016 and 2025 questionnaires measure general rather than "
        "professional experience, so those three points sit on a different "
        "scale and are drawn unconnected. The 2024 to 2025 junior change of "
        "-19.7 percentage points is dominated by that instrument change."
    )


# --------------------------------------------------------------------------
# Tab 2 — the test
# --------------------------------------------------------------------------
def figure_fit(
    observed: pd.DataFrame, coefficients: pd.Series, series: str, knot: int
) -> go.Figure:
    colour = SERIES_COLOURS[series]
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=observed["Year"],
            y=observed["junior"] * 100,
            mode="markers",
            name="Observed junior share",
            marker={"color": colour, "size": 8},
            error_y={
                "type": "data",
                "symmetric": False,
                "array": (observed["ci_high"] - observed["junior"]) * 100,
                "arrayminus": (observed["junior"] - observed["ci_low"]) * 100,
                "color": colour,
                "thickness": 1.2,
                "width": 3,
            },
            hovertemplate="%{x}<br>observed %{y:.1f}%<extra></extra>",
        )
    )

    # The line is the audit's own fitted model evaluated at each year: the knot
    # is added as an explicit vertex so the two slopes meet exactly there.
    years = sorted({*observed["Year"].tolist(), knot})
    time = np.array(years, dtype=float) - knot
    fitted = (
        coefficients["const"]
        + coefficients["time"] * time
        + coefficients["slope_change"] * np.maximum(time, 0.0)
    )
    figure.add_trace(
        go.Scatter(
            x=years,
            y=fitted * 100,
            mode="lines",
            name=f"Two-slope fit at {knot}",
            line={"color": NEUTRAL_INK, "width": 2.5, "dash": "solid"},
            hovertemplate="%{x}<br>fitted %{y:.1f}%<extra></extra>",
        )
    )
    figure.add_vline(
        x=knot,
        line={"color": MUTED_FILL, "width": 2, "dash": "dash"},
        annotation_text=f"knot {knot}",
        annotation_position="top",
        annotation_font_size=FONT["annotation"],
    )

    scan = placebo_scan()
    row = scan[(scan["series"] == series) & (scan["break_year"] == knot)].iloc[0]
    figure.update_layout(
        title=(
            f"A break at {knot} explains {row['r_squared']:.0%} of the variance "
            f"in the junior share"
        ),
        height=560,
        hovermode="x unified",
    )
    figure.update_xaxes(title_text="Survey year", dtick=1, tickangle=-45)
    percent_axis(figure, "Junior share")
    return figure


def figure_r_squared(scan: pd.DataFrame, series: str, knot: int) -> go.Figure:
    block = scan[scan["series"] == series].sort_values("break_year")
    colours = [
        SERIES_COLOURS[series] if year == knot else MUTED_FILL
        for year in block["break_year"]
    ]
    figure = go.Figure(
        go.Bar(
            x=block["break_year"],
            y=block["r_squared"] * 100,
            marker={"color": colours},
            hovertemplate="break %{x}<br>R-squared %{y:.1f}%<extra></extra>",
        )
    )
    figure.update_layout(
        title="Fit decays as the candidate break moves toward 2023",
        height=430,
        showlegend=False,
        bargap=0.28,
    )
    figure.update_xaxes(title_text="Candidate break year", dtick=1)
    percent_axis(figure, "R-squared of the fit")
    return figure


def tab_test() -> None:
    scan = placebo_scan()
    mde = mde_table()
    observed_all = junior_by_series()
    coefficients = piecewise_coefficients()

    st.header("The test")
    st.markdown(
        "A continuous broken-stick regression of the annual junior share on "
        "time estimates one slope before a candidate break year and a slope "
        "change after it. The audit fits that model at every candidate break "
        "from 2016 to 2023, for three samples."
    )

    left, right = st.columns([2, 3])
    with left:
        series = st.radio("Sample", SERIES_ORDER, index=0)
    with right:
        knot = st.slider(
            "Candidate break year",
            min_value=CANDIDATE_BREAKS[0],
            max_value=CANDIDATE_BREAKS[-1],
            value=CANDIDATE_BREAKS[0],
            step=1,
        )

    observed = observed_all[observed_all["series"] == series].sort_values("Year")
    fit = coefficients[
        (coefficients["series"] == series) & (coefficients["break_year"] == knot)
    ].iloc[0]

    show_chart(figure_fit(observed, fit, series, knot))
    st.caption(
        "The line evaluates the audit's reported coefficients for this sample "
        "and knot (outputs/audit/ROBUSTNESS.md, 'Piecewise regressions'): "
        f"const {fit['const']:.4f}, pre-break slope {fit['time']:+.4f} per "
        f"year, slope change {fit['slope_change']:+.4f}. Nothing is refitted "
        "in the app. Points are the annual junior shares from the same file, "
        "with Wilson 95% intervals."
    )

    show_chart(figure_r_squared(scan, series, knot))

    block = scan[scan["break_year"] == knot].merge(mde, on=["series", "break_year"], how="left")
    selected = block[block["series"] == series].iloc[0]
    first, second, third = st.columns(3)
    first.metric("R-squared", f"{selected['r_squared']:.3f}")
    second.metric("p-value", f"{selected['p_value']:.4f}")
    third.metric("R-squared rank", f"{selected['rank']} of 8")
    st.caption(
        "Source: outputs/audit/ROBUSTNESS.md, 'Placebo-scan summary'. Rank is "
        "the position of this break year's R-squared among the eight "
        "candidates within the selected sample."
    )

    with st.expander("All three samples at this knot, with slope change and power"):
        table = pd.DataFrame(
            {
                "Sample": block["series"],
                "Annual points (n)": block["n"],
                "Slope change per year": block["slope_change"],
                "p-value": block["p_value"],
                "R-squared": block["r_squared"],
                "R-squared rank (of 8)": block["rank"],
                "Minimum detectable slope change": block["mde"],
            }
        ).sort_values("Sample")
        st.dataframe(
            table.style.format(
                {
                    "Slope change per year": "{:+.4f}",
                    "p-value": "{:.4f}",
                    "R-squared": "{:.3f}",
                    "Minimum detectable slope change": "{:.4f}",
                }
            ),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Source: outputs/audit/ROBUSTNESS.md, sections 'Placebo-scan "
            "summary' and 'Power note'."
        )

    st.markdown(
        "At a 2022 knot the minimum detectable slope change at 80% power is "
        "0.117 per year against an observed estimate of -0.046, so "
        "non-significance reflects the resolution of an annual series, not "
        "proof of no effect. Those two values are for the all-respondents "
        "professional-years sample, which has twelve annual points."
    )
    st.markdown(
        "The three samples are measurement and geography variants, not the "
        "junior, mid and senior cohorts. Only the junior share is regressed; "
        "the audit reports no placebo scan for the mid or senior series."
    )


# --------------------------------------------------------------------------
# Tab 3 — community
# --------------------------------------------------------------------------
def _add_series(
    figure: go.Figure,
    frame: pd.DataFrame,
    column: str,
    label: str,
    colour: str,
    comparable_years: tuple[int, ...],
) -> None:
    """Draw a share series, splitting off years measured on another instrument."""
    comparable = frame[frame["Year"].isin(comparable_years)]
    other = frame[~frame["Year"].isin(comparable_years)]

    def error_bars(block: pd.DataFrame) -> dict:
        return {
            "type": "data",
            "symmetric": False,
            "array": (block[f"{column}_hi"] - block[column]) * 100,
            "arrayminus": (block[column] - block[f"{column}_lo"]) * 100,
            "color": colour,
            "thickness": 1.2,
            "width": 3,
        }

    for index, run in enumerate(consecutive_runs(list(comparable["Year"]))):
        block = comparable[comparable["Year"].isin(run)]
        figure.add_trace(
            go.Scatter(
                x=block["Year"],
                y=block[column] * 100,
                mode="lines+markers",
                name=label,
                legendgroup=label,
                showlegend=index == 0,
                line={"color": colour, "width": 2.5},
                marker={"color": colour, "size": 7},
                error_y=error_bars(block),
                hovertemplate=f"{label} %{{x}}<br>%{{y:.1f}}%<extra></extra>",
            ),
            row=1,
            col=1,
        )
    if not other.empty:
        figure.add_trace(
            go.Scatter(
                x=other["Year"],
                y=other[column] * 100,
                mode="markers",
                name=f"{label}, other instrument",
                legendgroup=label,
                showlegend=False,
                marker={
                    "color": "rgba(0,0,0,0)",
                    "size": 10,
                    "line": {"color": colour, "width": 2},
                },
                error_y=error_bars(other),
                hovertemplate=(
                    f"{label} %{{x}}, different answer scale<br>%{{y:.1f}}%<extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )


def _add_nonresponse(figure: go.Figure, frame: pd.DataFrame) -> None:
    figure.add_trace(
        go.Scatter(
            x=frame["Year"],
            y=frame["nonresponse"] * 100,
            mode="lines+markers",
            name="Left the question blank",
            line={"color": NONRESPONSE_COLOUR, "width": 2, "dash": "dot"},
            marker={"color": NONRESPONSE_COLOUR, "size": 6},
            hovertemplate="%{x}<br>%{y:.1f}% blank<extra></extra>",
        ),
        row=2,
        col=1,
    )


def _two_row_figure(title: str, height: int) -> go.Figure:
    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.10,
        row_heights=[0.68, 0.32],
    )
    figure.update_layout(title=title, height=height, hovermode="x unified")
    figure.update_xaxes(title_text="Survey year", dtick=1, row=2, col=1)
    for row in (1, 2):
        figure.update_yaxes(range=[0, 100], ticksuffix="%", row=row, col=1)
    figure.update_yaxes(title_text="Non-response", row=2, col=1)
    return figure


def figure_belonging(frame: pd.DataFrame, show_bounds: bool) -> go.Figure:
    figure = _two_row_figure(
        "More respondents rejected than claimed belonging from 2023 onward", 700
    )
    comparable = tuple(range(2019, 2026))
    for column, label in (
        ("yes/agree", "Yes or agree"),
        ("no/disagree", "No or disagree"),
        ("excluded", "Neutral, excluded from the split"),
    ):
        _add_series(figure, frame, column, label, BELONGING_COLOURS[column], comparable)

    figure.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            name="2017, 2018: different answer scale",
            marker={
                "color": "rgba(0,0,0,0)",
                "size": 10,
                "line": {"color": NEUTRAL_INK, "width": 2},
            },
        ),
        row=1,
        col=1,
    )

    if show_bounds:
        row = frame[frame["Year"] == 2025].iloc[0]
        lower = row["yes/agree_count"] / row["n_total"]
        upper = (row["yes/agree_count"] + (row["n_total"] - row["answered"])) / row["n_total"]
        # Drawn as a band rather than an error bar: these are bounds on what
        # the non-responders could have said, not a confidence interval.
        figure.add_shape(
            type="rect",
            x0=2024.72,
            x1=2025.28,
            y0=lower * 100,
            y1=upper * 100,
            fillcolor="rgba(0, 114, 178, 0.16)",
            line={"width": 0},
            layer="below",
            row=1,
            col=1,
        )
        figure.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                name=(
                    f"2025 bounds on the yes share, {lower:.1%} to {upper:.1%} "
                    "(computed in-app)"
                ),
                marker={"color": "rgba(0, 114, 178, 0.30)", "size": 13, "symbol": "square"},
            ),
            row=1,
            col=1,
        )

    figure.update_yaxes(title_text="Share of respondents who answered", row=1, col=1)
    _add_nonresponse(figure, frame)
    return figure


def figure_participation(frame: pd.DataFrame) -> go.Figure:
    figure = _two_row_figure(
        "Frequent participation fell from 36.1% in 2019 to 22.0% in 2024", 640
    )
    _add_series(
        figure,
        frame,
        "frequent",
        "Participates at least a few times per month",
        PARTICIPATION_COLOUR,
        tuple(range(2019, 2025)),
    )
    figure.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            name="2025: two lower-frequency options added",
            marker={
                "color": "rgba(0,0,0,0)",
                "size": 10,
                "line": {"color": NEUTRAL_INK, "width": 2},
            },
        ),
        row=1,
        col=1,
    )
    figure.update_yaxes(title_text="Share of respondents who answered", row=1, col=1)
    _add_nonresponse(figure, frame)
    return figure


def tab_community() -> None:
    belonging = belonging_series()
    participation = participation_series()

    st.header("Community")
    st.markdown(
        "Two questions track how respondents relate to the site: whether they "
        "feel part of the community, asked from 2017, and how often they take "
        "part in questions and answers, asked from 2019. Both are read here "
        "from outputs/audit/COMMUNITY.md, which reports the shares behind the "
        "two committed figures."
    )

    st.subheader("Belonging")
    show_bounds = st.toggle("2025 bounds on the yes share", value=True)
    show_chart(figure_belonging(belonging, show_bounds))
    st.caption(
        "Source: outputs/audit/COMMUNITY.md, 'Belonging, 2017-2025'. Shares are "
        "of respondents who answered; the lower panel gives that year's "
        "non-response rate from the same table. Error bars are Wilson 95% "
        "intervals."
    )
    st.markdown(
        "Neutral answers are excluded from the yes/no split, which is why the "
        "two series do not sum to 100%. The excluded share is 0.0% in 2017 and "
        "2018, because neither questionnaire offered a neutral option, and runs "
        "between 20.2% and 21.7% from 2019 on."
    )
    st.markdown(
        "Not-sure answers are not excluded: the mapping table assigns both "
        "2018's 'I'm not sure' and 2019-2025's 'Not sure' to no/disagree. The "
        "2017 and 2018 points use different answer scales again, an agree/"
        "disagree scale and a yes/no scale, so they are drawn unconnected."
    )

    if show_bounds:
        row = belonging[belonging["Year"] == 2025].iloc[0]
        blank = row["n_total"] - row["answered"]
        lower = row["yes/agree_count"] / row["n_total"]
        upper = (row["yes/agree_count"] + blank) / row["n_total"]
        st.caption(
            f"The 2025 band is computed in-app, not sourced from the audit. "
            f"With {blank:,.0f} of {row['n_total']:,.0f} respondents leaving "
            f"the question blank, the yes share over all 2025 respondents lies "
            f"between {lower:.1%} (every non-responder a no) and {upper:.1%} "
            f"(every non-responder a yes). The plotted point, {row['yes/agree']:.1%}, "
            f"is the share among the {row['answered']:,.0f} who answered."
        )

    st.subheader("Participation")
    show_chart(figure_participation(participation))
    st.caption(
        "Source: outputs/audit/COMMUNITY.md, 'Participation at least a few "
        "times per month, 2019-2025'. Shares are of respondents who answered; "
        "the lower panel gives that year's non-response rate from the same "
        "table. Error bars are Wilson 95% intervals."
    )
    st.markdown(
        "The 2025 point is not directly comparable and is drawn unconnected. "
        "Its mapping table adds two lower-frequency options absent in "
        "2019-2024, 'Infrequently, less than once per year' (12,057 responses) "
        "and 'Less than once every 2 - 3 months' (4,586), both counted as "
        "infrequent."
    )

    with st.expander("Raw response categories and what each maps to"):
        question = st.radio(
            "Question", ["Belonging", "Participation"], index=0, horizontal=True
        )
        mapping = category_mapping(question)
        year = st.select_slider(
            "Survey year",
            options=sorted(mapping["Year"].unique()),
            value=int(mapping["Year"].max()),
        )
        block = mapping[mapping["Year"] == year].drop(columns="Year")
        st.dataframe(
            block.style.format({"Count": "{:,.0f}"}), hide_index=True, width="stretch"
        )
        st.caption(
            f"Source: outputs/audit/COMMUNITY.md, '{question} raw-category "
            "mapping'. Counts are before the figure's share calculation."
        )


# --------------------------------------------------------------------------
# Tab 4 — clusters
# --------------------------------------------------------------------------
# The composition matrix published by the audit covers two variable groups.
# The remaining groups exist only as modal profiles, and are offered there.
COMPOSITION_GROUPS = {"Age": "Age", "AI usage": "AI_Usage_Status"}
MODAL_GROUPS = {
    "Age": ["Age"],
    "Experience": ["Years_of_Experience", "experience_is_proxy"],
    "Education": ["Education_Level"],
    "AI usage": ["AI_Usage_Status", "AI_Tool_Usage"],
    "Belonging": [
        "Part_of_community",
        "Participates_in_questions",
        "Visits_SO_freq",
        "Has_SO_account",
    ],
    "Employment": ["Employment_Status", "Yearly_Compensation"],
}


def figure_sizes(sizes: pd.DataFrame, chosen: list[int]) -> go.Figure:
    colours = [
        "#3E7C8C" if cluster in chosen else MUTED_FILL for cluster in sizes["cluster"]
    ]
    figure = go.Figure(
        go.Bar(
            x=[f"Cluster {cluster}" for cluster in sizes["cluster"]],
            y=sizes["share"] * 100,
            marker={"color": colours},
            text=[f"{share:.1%}<br>{rows:,}" for share, rows in zip(sizes["share"], sizes["rows"])],
            textposition="outside",
            hovertemplate="%{x}<br>%{y:.2f}% of rows<extra></extra>",
        )
    )
    figure.update_layout(
        title="The largest 2025 cluster is defined by unanswered questions",
        height=450,
        showlegend=False,
        bargap=0.32,
    )
    figure.update_xaxes(title_text="Cluster")
    percent_axis(figure, "Share of the 49,123 clustered rows")
    return figure


def figure_heatmap(matrix: pd.DataFrame) -> go.Figure:
    values = matrix.to_numpy(dtype=float)
    figure = go.Figure(
        go.Heatmap(
            z=values,
            x=list(matrix.columns),
            y=list(matrix.index),
            colorscale="Viridis",
            zmin=0,
            zmax=100,
            colorbar={"title": {"text": "Share of cluster", "side": "right"}, "ticksuffix": "%"},
            hovertemplate="%{x}<br>%{y}<br>%{z:.2f}%<extra></extra>",
        )
    )
    for row, label in enumerate(matrix.index):
        for column, cluster in enumerate(matrix.columns):
            value = values[row, column]
            figure.add_annotation(
                x=cluster,
                y=label,
                text=f"{value:.0f}%",
                showarrow=False,
                font={
                    "size": FONT["annotation"],
                    "color": "white" if value < 55 else "#111111",
                },
            )
    figure.update_layout(
        title="Cluster 1 is 88% non-answers on the AI question",
        height=140 + 56 * len(matrix.index),
        margin={"l": 420, "r": 40, "t": 90, "b": 80},
    )
    figure.update_xaxes(title_text="Cluster", showgrid=False)
    figure.update_yaxes(autorange="reversed", showgrid=False, ticksuffix="  ")
    return figure


def tab_clusters() -> None:
    sizes = cluster_sizes()
    matrix = cluster_composition()
    grid = k_selection()
    profiles = cluster_modal_profiles()

    st.header("Clusters")
    st.markdown(
        "K-modes partitions the 2025 rows only, 49,123 respondents, using all "
        "14 harmonized columns as categorical features. Nulls are passed to "
        "K-modes as a literal Missing category rather than dropped, so the "
        "cluster sizes sum to the full input."
    )

    left, right = st.columns(2)
    with left:
        chosen = st.multiselect(
            "Clusters",
            options=list(sizes["cluster"]),
            default=list(sizes["cluster"]),
            format_func=lambda cluster: f"Cluster {cluster}",
        )
    with right:
        groups = st.multiselect(
            "Variable groups in the composition heatmap",
            options=list(COMPOSITION_GROUPS),
            default=list(COMPOSITION_GROUPS),
        )

    show_chart(figure_sizes(sizes, chosen))
    st.caption("Source: outputs/audit/CLUSTERING.md section 5.")

    st.subheader("Choice of K")
    st.markdown(
        "The elbow criterion selects K=3, with an elbow distance of 0.2123 "
        "against 0.1409 at K=5. The reported partition uses K=5, which the "
        "audit records as a deliberate human override on interpretability "
        "grounds rather than a criterion-driven selection."
    )
    with st.expander("Cost and elbow distance for every K searched"):
        st.dataframe(
            pd.DataFrame(
                {
                    "K": grid["K"],
                    "Cost": grid["cost"],
                    "Elbow distance": grid["elbow_distance"],
                    "Selected by the elbow": np.where(grid["selected_by_elbow"], "yes", ""),
                    "Used in the report": np.where(grid["K"] == 5, "yes", ""),
                }
            ).style.format({"Cost": "{:,.0f}", "Elbow distance": "{:.4f}"}),
            hide_index=True,
            width="stretch",
        )
        st.caption("Source: outputs/audit/CLUSTERING.md section 2.")

    st.subheader("Composition")
    if not chosen or not groups:
        st.info("Select at least one cluster and one variable group.")
    else:
        prefixes = tuple(f"{COMPOSITION_GROUPS[group]}:" for group in groups)
        rows = [label for label in matrix.index if label.startswith(prefixes)]
        columns = [f"Cluster {cluster}" for cluster in sorted(chosen)]
        show_chart(figure_heatmap(matrix.loc[rows, columns]))
    st.caption(
        "Source: outputs/audit/CLUSTERING.md section 6, the matrix behind "
        "outputs/figures/cluster_developers_heatmap.png. Each cluster's rows "
        "sum to 100% within a single source column, so a filtered view no "
        "longer sums to 100%. The published matrix covers age and AI usage "
        "only; the other variable groups appear below as modal values."
    )

    with st.expander("Modal answer per cluster for the variables not in the heatmap"):
        st.markdown(
            "For the variables the audit does not publish a full composition "
            "matrix for, it reports the most common answer in each cluster and "
            "the share of the cluster giving it."
        )
        modal_groups = st.multiselect(
            "Variable groups in the modal profiles",
            options=list(MODAL_GROUPS),
            default=["Experience", "Education", "Belonging"],
        )
        wanted = [column for group in modal_groups for column in MODAL_GROUPS[group]]
        block = profiles[profiles["cluster"].isin(chosen) & profiles["column"].isin(wanted)]
        if block.empty:
            st.info("Select at least one cluster and one variable group.")
        else:
            st.dataframe(
                pd.DataFrame(
                    {
                        "Cluster": block["cluster"],
                        "Column": block["column"],
                        "Modal value": block["modal_value"],
                        "Share of cluster": block["share"],
                    }
                ).style.format({"Share of cluster": "{:.1%}"}),
                hide_index=True,
                width="stretch",
            )
        st.caption("Source: outputs/audit/CLUSTERING.md section 7.")

    st.subheader("Cluster 1 is a survey drop-off cohort")
    st.markdown(
        "Cluster 1 holds 34.4% of the input and its modal value is Missing on "
        "every engagement column: 99.3% on belonging, 98.5% on participation, "
        "96.5% on account ownership, 88.4% on AI usage. It groups respondents "
        "who stopped answering partway through, an artefact of encoding nulls "
        "as a category rather than a designed step in the analysis."
    )


# --------------------------------------------------------------------------
# Streamlit's widgets are react-aria, which resolves its own text direction in
# JavaScript from `navigator.language` -- not from CSS. On a machine whose
# browser locale is an RTL language (Hebrew here), react-aria reports
# `direction: 'rtl'` and the slider inverts its thumb position with
# `percent = 1 - percent`, so the handles and the filled track run opposite to
# the axis captions, which Streamlit renders as ordinary LTR text. No CSS rule
# can reach that code path. React-aria reads this symbol before it falls back
# to `navigator.language`, so pinning it is the supported override; dispatching
# `languagechange` makes already-mounted widgets re-read it.
LOCALE_PIN = """
<script>
(function () {
  var app = window.parent;
  if (!app) { return; }
  var key = Symbol.for('react-aria.i18n.locale');
  if (app[key] === 'en-US') { return; }
  app[key] = 'en-US';
  app.dispatchEvent(new Event('languagechange'));
})();
</script>
"""


def pin_widget_locale() -> None:
    """Force react-aria widgets to LTR regardless of the browser's locale."""
    st.iframe(LOCALE_PIN, height=1, width=1)


def main() -> None:
    st.set_page_config(
        page_title="Stack Overflow survey composition, 2011-2025",
        layout="wide",
    )
    pin_widget_locale()
    st.markdown(BASE_TYPE_CSS, unsafe_allow_html=True)
    st.title("Stack Overflow survey composition, 2011-2025")
    st.markdown(
        "Every figure and table below is read from the markdown audit files in "
        "outputs/. The app does not load the harmonized master dataset."
    )

    claim, test, community, clusters = st.tabs(
        ["The claim", "The test", "Community", "Clusters"]
    )
    with claim:
        tab_claim()
    with test:
        tab_test()
    with community:
        tab_community()
    with clusters:
        tab_clusters()


main()
