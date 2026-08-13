"""K-modes clustering of developer survey respondents."""

from __future__ import annotations

import pandas as pd
from kmodes.kmodes import KModes


def cluster_developers(df: pd.DataFrame, n_clusters: int) -> pd.DataFrame:
    """
    Cluster a dataset with k-modes and print each cluster's characteristics.

    All columns are treated as categorical. Missing values are filled with
    ``Missing`` so they do not drop respondents from the clustering.
    Returns a copy of ``df`` with a ``Cluster`` column added.
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

    return labeled

if __name__ == "__main__":
    df = pd.read_csv("data/processed/harmonized_stack_overflow_2011_2025.csv")
    df = df[df["Year"] == 2025]
    df = cluster_developers(df, n_clusters=3)
