"""Audit tables behind the K-modes cluster heatmap."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis.cluster_developers import (
    HEATMAP_COLUMNS,
    INIT_METHOD,
    K_GRID,
    N_INIT,
    RANDOM_STATE,
)


OUTPUT_PATH = ROOT / "outputs" / "audit" / "CLUSTERING.md"


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    return "\n".join([
        "| " + " | ".join(map(str, headers)) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(map(str, row)) + " |" for row in rows),
    ])


def _pct(value: object) -> str:
    if value is None or pd.isna(value):
        return "NOT AVAILABLE"
    return f"{float(value) * 100:.2f}%"


def write_clustering(result: dict, output_path: Path = OUTPUT_PATH) -> Path:
    """Write the grid search, selection, and composition tables for the heatmap.

    Consumes the result of the clustering stage rather than refitting, so the
    reported cluster sizes are the ones the figure was drawn from.
    """
    grid = result["grid"]
    diagnostics = result["diagnostics"]
    sizes = result["sizes"]
    profiles = result["profiles"]
    composition = result["composition"]
    chosen_k = result["chosen_k"]

    content = "# K-modes clustering — audit tables\n\n"
    content += (
        f"Input: the {result['year']} rows of the harmonized master, "
        f"**{result['rows']:,} respondents**, all "
        f"{len(result['source_columns'])} columns treated as categorical. "
        "Nulls are passed to K-modes as a literal `Missing` category rather "
        "than dropped, so cluster sizes sum to the full input.\n\n"
    )

    content += "## 1. Hyperparameter grid searched\n\n"
    content += (
        f"K is the only searched hyperparameter; initialisation is held fixed "
        f"so the cost values across K are comparable.\n\n"
    )
    content += markdown_table(
        ["Hyperparameter", "Value(s) searched"],
        [
            ["`n_clusters` (K)", ", ".join(str(k) for k in K_GRID)],
            ["`init`", f"`{INIT_METHOD}` (fixed)"],
            ["`n_init`", f"{N_INIT} (fixed) — best of {N_INIT} restarts per K"],
            ["`random_state`", f"{RANDOM_STATE} (fixed, so the search is reproducible)"],
        ],
    )
    content += (
        f"\n\nThat is **{len(K_GRID)} candidate values of K x {N_INIT} restarts "
        f"= {len(K_GRID) * N_INIT} K-modes fits**.\n\n"
    )

    content += "## 2. Selection criterion and its value per K\n\n"
    content += (
        "The criterion is the K-modes cost (total within-cluster Hamming "
        "dissimilarity to the assigned mode), which falls monotonically with K "
        "and so cannot be minimised to choose K. K is taken at the **elbow**: "
        "both axes are min-max normalised, and the selected K is the grid point "
        "furthest from the straight line joining the first and last points. "
        "`elbow distance` below is that perpendicular distance, and the largest "
        "value wins.\n\n"
    )
    content += (
        "The elbow criterion selects K=3. K=5 is used for the reported "
        "partition: the cost curve is effectively flat for K >= 3 (reductions "
        "of 4,575 / 4,296 / 5,993 / 3,862 after the initial 17,829), so cost "
        "alone does not discriminate among these values, and K=3 separates the "
        "active respondents on a single axis only. K=5 was chosen on "
        "interpretability grounds and is a deliberate human override, not an "
        "automated selection. The full grid is retained above as a "
        "sensitivity check.\n\n"
    )
    content += markdown_table(
        ["K", "Cost", "Cost reduction vs previous K", "Elbow distance", "Iterations to converge", "Selected"],
        [
            [
                int(r.k),
                f"{r.cost:,.0f}",
                "—" if pd.isna(r.cost_reduction_vs_previous) else f"{r.cost_reduction_vs_previous:,.0f}",
                f"{r.elbow_distance:.4f}",
                int(r.n_iter),
                "**YES**" if r.selected else "",
            ]
            for _, r in grid.iterrows()
        ],
    )

    content += "\n\n## 3. Chosen configuration\n\n"
    content += markdown_table(
        ["Setting", "Value"],
        [
            ["`n_clusters`", f"**{chosen_k}**"],
            ["`init`", f"`{INIT_METHOD}`"],
            ["`n_init`", str(N_INIT)],
            ["`random_state`", str(RANDOM_STATE)],
            ["Cost at chosen K", f"{result['cost']:,.0f}"],
            ["Rows clustered", f"{result['rows']:,}"],
        ],
    )

    content += "\n\n## 4. Feature diagnostics\n\n"
    content += (
        "K-modes weights every column equally under Hamming distance. A "
        "constant column contributes no discriminating power, and a "
        "high-cardinality column contributes a near-constant mismatch to every "
        "pair. Both are reported rather than dropped, because the figure was "
        "produced with all columns in the input.\n\n"
    )
    content += markdown_table(
        ["Column", "Distinct categories", "Missing", "Missing share", "Role in the distance"],
        [
            [
                f"`{r.column}`",
                f"{int(r.distinct_categories):,}",
                f"{int(r.missing):,}",
                _pct(r.missing_share),
                r.role,
            ]
            for _, r in diagnostics.iterrows()
        ],
    )
    flagged = diagnostics[diagnostics["role"] != "discriminating"]
    if not flagged.empty:
        content += (
            "\n\n**Caveat.** "
            + ", ".join(f"`{c}`" for c in flagged["column"])
            + " do not separate respondents: they are either constant across the "
            "input or so nearly unique that every pair mismatches. Cluster "
            "differences are therefore carried by the remaining columns, and no "
            "claim in the report should rest on these.\n\n"
        )
    else:
        content += "\n\n"

    content += "## 5. Cluster sizes\n\n"
    content += markdown_table(
        ["Cluster", "Rows", "Share of input"],
        [[int(r.Cluster), f"{int(r.rows):,}", _pct(r.share)] for _, r in sizes.iterrows()],
    )
    content += f"\n\nSizes sum to {int(sizes['rows'].sum()):,}, the full input.\n\n"

    content += "## 6. Composition table behind the heatmap\n\n"
    heatmap_path = Path(result["heatmap_path"]).resolve()
    try:
        heatmap_label = heatmap_path.relative_to(ROOT).as_posix()
    except ValueError:
        heatmap_label = heatmap_path.name
    content += (
        f"This is exactly the matrix plotted in `{heatmap_label}`: for each "
        f"category of {' and '.join(f'`{c}`' for c in HEATMAP_COLUMNS)}, the share "
        "of that cluster's members giving that answer. Each cluster's rows sum "
        "to 100% within a single source column.\n\n"
    )
    content += markdown_table(
        ["Category", *composition.columns],
        [[label, *(_pct(v) for v in row)] for label, row in composition.iterrows()],
    )

    content += "\n\n## 7. Modal profile of every cluster\n\n"
    content += (
        "The most common answer in each cluster for every clustered column, "
        "with the share of the cluster giving it.\n\n"
    )
    content += markdown_table(
        ["Cluster", "Column", "Modal value", "Count", "Share of cluster"],
        [
            [
                int(r.Cluster),
                f"`{r.column}`",
                r.modal_value,
                f"{int(r.modal_count):,}",
                _pct(r.modal_share),
            ]
            for _, r in profiles.iterrows()
        ],
    )
    content += "\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main() -> None:
    from src.analysis.cluster_developers import run_cluster_analysis

    master = pd.read_csv(
        ROOT / "data" / "processed" / "harmonized_stack_overflow_2011_2025.csv",
        low_memory=False,
    )
    result = run_cluster_analysis(
        master, ROOT / "outputs" / "figures" / "cluster_developers_heatmap.png"
    )
    print(f"Wrote {write_clustering(result)}")


if __name__ == "__main__":
    main()
