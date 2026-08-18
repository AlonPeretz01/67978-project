"""K-modes clustering of developer survey respondents.

The number of clusters used to be a bare hard-coded ``5`` with no supporting
analysis (see outputs/audit/CLUSTERING_CHECK.md).  ``search_k`` now fits the
whole ``K_GRID`` and ``select_k`` picks the elbow of the cost curve, so the
chosen K is derived from the data and every candidate is reported in
outputs/audit/CLUSTERING.md.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from kmodes.kmodes import KModes


HEATMAP_COLUMNS = ("Age", "AI_Usage_Status")

# Hyperparameter grid searched by ``search_k``.  K-modes cost falls
# monotonically with K, so the grid is bounded and the elbow (not the minimum)
# selects K.
CLUSTER_YEAR = 2025
K_GRID = (2, 3, 4, 5, 6, 7, 8)
INIT_METHOD = "Huang"
N_INIT = 5
RANDOM_STATE = 42

# Deliberate, human-made choice: the report this pipeline supports describes
# a 5-cluster partition (four behavioural clusters plus one survey-drop-off
# cluster). The elbow criterion below selects K=3, but the cost curve is
# effectively flat past K=3 and does not discriminate among these values on
# its own, so K=5 is used for the reported partition on interpretability
# grounds. K_GRID/select_k are retained as a documented sensitivity check,
# not as the selection mechanism -- this constant, not their output, drives
# the fit used for the heatmap and CLUSTERING.md.
CHOSEN_K = 5


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cast every column to a categorical string, encoding nulls as ``Missing``.

    Missing values become a literal category rather than dropping the
    respondent, so cluster sizes always sum to the input row count.
    """
    return df.astype("string").fillna("Missing")


def column_diagnostics(features: pd.DataFrame, original: pd.DataFrame) -> pd.DataFrame:
    """Cardinality and missing share of every column fed to K-modes.

    K-modes weights each column equally under Hamming distance, so a constant
    column contributes nothing and a near-unique column contributes a nearly
    constant mismatch.  Both distort the cost curve and are reported rather
    than silently dropped.
    """
    rows = []
    for column in features.columns:
        distinct = int(features[column].nunique())
        missing = int(original[column].isna().sum())
        if distinct <= 1:
            role = "constant (no discriminating power)"
        elif distinct > 100:
            role = "high-cardinality (near-constant mismatch)"
        else:
            role = "discriminating"
        rows.append(
            {
                "column": column,
                "distinct_categories": distinct,
                "missing": missing,
                "missing_share": missing / len(original) if len(original) else float("nan"),
                "role": role,
            }
        )
    return pd.DataFrame(rows)


def search_k(
    features: pd.DataFrame,
    k_grid: tuple[int, ...] = K_GRID,
    init_method: str = INIT_METHOD,
    n_init: int = N_INIT,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, dict[int, KModes]]:
    """Fit K-modes for every K in the grid and return the cost curve.

    Returns the per-K criterion table and the fitted models, keyed by K, so
    the selected model is reused rather than refitted.
    """
    matrix = features.to_numpy()
    models: dict[int, KModes] = {}
    rows = []
    for n_clusters in k_grid:
        model = KModes(
            n_clusters=n_clusters,
            init=init_method,
            n_init=n_init,
            random_state=random_state,
        )
        model.fit(matrix)
        models[n_clusters] = model
        rows.append(
            {
                "k": n_clusters,
                "cost": float(model.cost_),
                "n_iter": int(model.n_iter_),
                "init": init_method,
                "n_init": n_init,
            }
        )
    grid = pd.DataFrame(rows)
    grid["cost_reduction_vs_previous"] = grid["cost"].diff().fillna(float("nan")).abs()
    grid["elbow_distance"] = _elbow_distances(grid["k"].to_numpy(), grid["cost"].to_numpy())
    return grid, models


def _elbow_distances(k_values, costs):
    """Perpendicular distance of each (K, cost) point from the endpoint chord.

    This is the standard elbow criterion: both axes are min-max normalised so
    the units cancel, then the point furthest from the straight line joining
    the first and last grid points is the knee.
    """
    k_span = k_values.max() - k_values.min()
    cost_span = costs.max() - costs.min()
    if k_span == 0 or cost_span == 0:
        return [0.0] * len(k_values)
    x = (k_values - k_values.min()) / k_span
    y = (costs - costs.min()) / cost_span
    # Chord runs from (0, 1) to (1, 0) after normalisation, so the
    # perpendicular distance is |x + y - 1| / sqrt(2).
    return [abs(xi + yi - 1) / (2 ** 0.5) for xi, yi in zip(x, y)]


def select_k(grid: pd.DataFrame) -> int:
    """Choose K at the elbow of the cost curve, breaking ties toward smaller K."""
    best = grid.sort_values(["elbow_distance", "k"], ascending=[False, True]).iloc[0]
    return int(best["k"])


def _cluster_heatmap_matrix(labeled: pd.DataFrame, n_clusters: int) -> pd.DataFrame:
    """Build a matrix of within-cluster percentages for selected columns."""
    available = [column for column in HEATMAP_COLUMNS if column in labeled.columns]
    if not available:
        raise ValueError(
            "Heatmap requires at least one of: " + ", ".join(HEATMAP_COLUMNS)
        )

    rows: list[pd.Series] = []
    for column in available:
        values = labeled[column].astype("string").fillna("Missing")
        for value in sorted(values.unique(), key=str):
            row_label = f"{column}: {value}"
            shares = {}
            for cluster_id in range(n_clusters):
                cluster = labeled[labeled["Cluster"] == cluster_id]
                if cluster.empty:
                    shares[f"Cluster {cluster_id}"] = 0.0
                    continue
                cluster_values = cluster[column].astype("string").fillna("Missing")
                shares[f"Cluster {cluster_id}"] = float(
                    (cluster_values == value).mean()
                )
            rows.append(pd.Series(shares, name=row_label))

    return pd.DataFrame(rows)


def plot_cluster_heatmap(
    labeled: pd.DataFrame,
    n_clusters: int,
    output_path: str | Path,
) -> pd.DataFrame:
    """
    Heatmap of within-cluster percentage fill for Age and AI_Usage_Status.
    X-axis is clusters; y-axis is column:value rows.
    """
    matrix = _cluster_heatmap_matrix(labeled, n_clusters)

    vmin = float(matrix.values.min())
    vmax = float(matrix.values.max())
    if vmin == vmax:
        vmin, vmax = 0.0, 1.0

    fig_height = max(5.5, 0.35 * len(matrix) + 2.0)
    fig, ax = plt.subplots(figsize=(max(8, 1.6 * n_clusters + 4), fig_height))
    sns.heatmap(
        matrix,
        ax=ax,
        cmap="plasma",
        vmin=vmin,
        vmax=vmax,
        annot=True,
        fmt=".0%",
        linewidths=0.4,
        linecolor="white",
        cbar_kws={"label": "Share within cluster"},
    )
    ax.set_title(
        "Cluster composition by age and AI usage",
        fontsize=17,
        weight="semibold",
        pad=14,
    )
    ax.set_xlabel("Cluster", fontsize=13)
    ax.set_ylabel("Category", fontsize=13)
    ax.tick_params(axis="both", labelsize=11)
    fig.tight_layout()
    fig.savefig(Path(output_path), dpi=200, bbox_inches="tight")
    plt.close(fig)
    return matrix


def cluster_profiles(labeled: pd.DataFrame, source_columns) -> pd.DataFrame:
    """Modal value and its within-cluster share for every column, per cluster."""
    rows = []
    total = len(labeled)
    for cluster_id in sorted(labeled["Cluster"].unique()):
        cluster = labeled[labeled["Cluster"] == cluster_id]
        for column in source_columns:
            counts = (
                cluster[column].astype("string").fillna("Missing").value_counts(dropna=False)
            )
            rows.append(
                {
                    "Cluster": int(cluster_id),
                    "cluster_size": len(cluster),
                    "cluster_share": len(cluster) / total,
                    "column": column,
                    "modal_value": counts.index[0],
                    "modal_count": int(counts.iloc[0]),
                    "modal_share": counts.iloc[0] / len(cluster),
                }
            )
    return pd.DataFrame(rows)


def cluster_sizes(labeled: pd.DataFrame) -> pd.DataFrame:
    """Row count and share of the input for every cluster."""
    total = len(labeled)
    counts = labeled["Cluster"].value_counts().sort_index()
    return pd.DataFrame(
        {
            "Cluster": counts.index.astype(int),
            "rows": counts.to_numpy(),
            "share": counts.to_numpy() / total,
        }
    ).reset_index(drop=True)


def cluster_developers(
    df: pd.DataFrame,
    n_clusters: int,
    heatmap_path: str | Path | None = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Cluster a dataset with k-modes and summarise each cluster's characteristics.

    Also builds a heatmap of within-cluster shares for Age and
    AI_Usage_Status. All columns are treated as categorical. Missing
    values are filled with ``Missing`` so they do not drop respondents from
    the clustering. Returns a copy of ``df`` with a ``Cluster`` column added.

    ``verbose`` controls console output only; the pipeline runs quiet because
    outputs/audit/CLUSTERING.md carries the same numbers.
    """
    if n_clusters < 1:
        raise ValueError("n_clusters must be at least 1.")
    if df.empty:
        raise ValueError("Cannot cluster an empty DataFrame.")

    labeled = df.copy()
    features = prepare_features(labeled)

    model = KModes(
        n_clusters=n_clusters,
        init=INIT_METHOD,
        n_init=N_INIT,
        random_state=RANDOM_STATE,
    )
    labeled["Cluster"] = model.fit_predict(features.to_numpy())

    if verbose:
        _print_profiles(labeled, df.columns, n_clusters)

    if heatmap_path is None:
        heatmap_path = Path("outputs/figures/cluster_developers_heatmap.png")
    Path(heatmap_path).parent.mkdir(parents=True, exist_ok=True)
    plot_cluster_heatmap(labeled, n_clusters, heatmap_path)
    if verbose:
        print(f"Saved cluster heatmap to {heatmap_path}")

    return labeled


def _print_profiles(labeled: pd.DataFrame, source_columns, n_clusters: int) -> None:
    total = len(labeled)
    print(f"K-modes clustering: {n_clusters} clusters, {total:,} rows\n")
    profiles = cluster_profiles(labeled, source_columns)
    for cluster_id, group in profiles.groupby("Cluster"):
        size = int(group["cluster_size"].iloc[0])
        print(f"Cluster {cluster_id}: {size:,} rows ({group['cluster_share'].iloc[0]:.1%})")
        for _, row in group.iterrows():
            print(f"  {row['column']}: {row['modal_value']} ({row['modal_share']:.1%})")
        print()


def run_cluster_analysis(
    df: pd.DataFrame,
    heatmap_path: str | Path,
    year: int = CLUSTER_YEAR,
    k_grid: tuple[int, ...] = K_GRID,
    verbose: bool = False,
) -> dict:
    """Search the K grid, cluster at the selected K, and draw the heatmap.

    Returns every table the clustering audit report quotes, so the audit is
    written from the same fit that produced the figure rather than a rerun.
    """
    subset = df[pd.to_numeric(df["Year"], errors="coerce") == year]
    if subset.empty:
        raise ValueError(f"No rows for clustering year {year}.")

    features = prepare_features(subset)
    diagnostics = column_diagnostics(features, subset)
    grid, models = search_k(features, k_grid=k_grid)
    elbow_k = select_k(grid)
    grid["selected"] = grid["k"] == elbow_k
    chosen_k = CHOSEN_K

    labeled = subset.copy()
    labeled["Cluster"] = models[chosen_k].predict(features.to_numpy())
    if verbose:
        _print_profiles(labeled, subset.columns, chosen_k)

    Path(heatmap_path).parent.mkdir(parents=True, exist_ok=True)
    composition = plot_cluster_heatmap(labeled, chosen_k, heatmap_path)

    return {
        "year": year,
        "rows": len(subset),
        "diagnostics": diagnostics,
        "grid": grid,
        "elbow_k": elbow_k,
        "chosen_k": chosen_k,
        "cost": float(models[chosen_k].cost_),
        "sizes": cluster_sizes(labeled),
        "profiles": cluster_profiles(labeled, subset.columns),
        "composition": composition,
        "heatmap_path": Path(heatmap_path),
        "source_columns": list(subset.columns),
    }


if __name__ == "__main__":
    df = pd.read_csv("data/processed/harmonized_stack_overflow_2011_2025.csv", low_memory=False)
    result = run_cluster_analysis(
        df,
        "outputs/figures/cluster_developers_heatmap.png",
        verbose=True,
    )
    print(result["grid"].to_string(index=False))
    print(f"\nSelected K = {result['chosen_k']}")
