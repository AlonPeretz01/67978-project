"""K-modes clustering of developer survey respondents."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from kmodes.kmodes import KModes


HEATMAP_COLUMNS = ("Age", "AI_Usage_Status")


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


def cluster_developers(
    df: pd.DataFrame,
    n_clusters: int,
    heatmap_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Cluster a dataset with k-modes and print each cluster's characteristics.

    Also builds a heatmap of within-cluster shares for Age and
    AI_Usage_Status. All columns are treated as categorical. Missing
    values are filled with ``Missing`` so they do not drop respondents from
    the clustering. Returns a copy of ``df`` with a ``Cluster`` column added.
    """
    if n_clusters < 1:
        raise ValueError("n_clusters must be at least 1.")
    if df.empty:
        raise ValueError("Cannot cluster an empty DataFrame.")

    labeled = df.copy()
    categorical = labeled.astype("string").fillna("Missing")
    features = categorical.to_numpy()

    model = KModes(n_clusters=n_clusters, init="Huang", n_init=5, random_state=42)
    labels = model.fit_predict(features)
    labeled["Cluster"] = labels

    total = len(labeled)
    print(f"K-modes clustering: {n_clusters} clusters, {total:,} rows\n")

    for cluster_id in range(n_clusters):
        cluster = labeled[labeled["Cluster"] == cluster_id]
        share = len(cluster) / total
        print(f"Cluster {cluster_id}: {len(cluster):,} rows ({share:.1%})")

        for column in df.columns:
            counts = cluster[column].astype("string").fillna("Missing").value_counts(dropna=False)
            mode_value = counts.index[0]
            mode_share = counts.iloc[0] / len(cluster)
            print(f"  {column}: {mode_value} ({mode_share:.1%})")
        print()

    if heatmap_path is None:
        heatmap_path = Path("outputs/figures/cluster_developers_heatmap.png")
    Path(heatmap_path).parent.mkdir(parents=True, exist_ok=True)
    plot_cluster_heatmap(labeled, n_clusters, heatmap_path)
    print(f"Saved cluster heatmap to {heatmap_path}")

    return labeled


if __name__ == "__main__":
    df = pd.read_csv("data/processed/harmonized_stack_overflow_2011_2025.csv")
    df = df[df["Year"] == 2025]
    df = cluster_developers(df, n_clusters=5)
