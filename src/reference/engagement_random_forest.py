"""Reference-only Stack Overflow engagement random forest.

This module is retained solely to reproduce the reported held-out evaluation
(accuracy 0.541542, majority baseline 0.571659, ROC-AUC 0.547924).  It is not
part of the substantive reported analysis or the main figure pipeline.
"""

from __future__ import annotations

import logging
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from src.models.community_demographics_ml import YEAR_MAX, experience_to_years


LOGGER = logging.getLogger(__name__)
RECENT_YEAR_MIN = 2022
RANDOM_STATE = 42
MODEL_FEATURES = ["Years_of_Experience", "Yearly_Compensation", "Education_Level"]
NUMERIC_FEATURES = ["Years_of_Experience", "Yearly_Compensation"]
CATEGORICAL_FEATURES = ["Education_Level"]
FEATURE_LABELS = {
    "Years_of_Experience": "Professional experience",
    "Yearly_Compensation": "Annual compensation",
    "Education_Level": "Education level",
}


def engagement_target(data: pd.DataFrame) -> tuple[pd.Series, str]:
    """Map the best-covered engagement measure to active (1) / inactive (0)."""
    community_map = {
        "yes, definitely": 1.0, "yes, somewhat": 1.0, "neutral": 0.0,
        "no, not really": 0.0, "no, not at all": 0.0,
    }
    visit_map = {
        "multiple times per day": 1.0, "daily or almost daily": 1.0,
        "a few times per week": 1.0, "a few times per month or weekly": 0.0,
        "less than once per month or monthly": 0.0,
        "i have never visited stack overflow (before today)": 0.0,
    }
    community = data["Part_of_community"].astype("string").str.strip().str.lower().map(community_map)
    visits = data["Visits_SO_freq"].astype("string").str.strip().str.lower().map(visit_map)
    if community.notna().sum() >= 100 and community.nunique(dropna=True) == 2:
        return community, "Part of the Stack Overflow community"
    if visits.notna().sum() >= 100 and visits.nunique(dropna=True) == 2:
        return visits, "Frequent Stack Overflow visits"
    raise ValueError("Recent survey rows do not contain a binary engagement target with at least 100 usable responses.")


def _mode_or_default(series: pd.Series, default: object) -> object:
    modes = series.dropna().mode()
    return modes.iloc[0] if not modes.empty else default


def fit_model_feature_encoder(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, list[str]], dict[str, object]]:
    """Fit the established feature preprocessing on training data only."""
    parts: list[pd.DataFrame] = []
    groups: dict[str, list[str]] = {}
    state: dict[str, object] = {"numeric_fill": {}, "categorical_fill": {}, "categories": {}}
    for column in NUMERIC_FEATURES:
        values = data[column].map(experience_to_years) if column == "Years_of_Experience" else pd.to_numeric(data[column], errors="coerce")
        values = values.replace([np.inf, -np.inf], np.nan)
        median = _mode_or_default(values, 0.0) if values.notna().sum() == 0 else values.median()
        parts.append(values.fillna(median).astype(float).to_frame(column))
        groups[column] = [column]
        state["numeric_fill"][column] = float(median)
    for column in CATEGORICAL_FEATURES:
        values = data[column].astype("string").str.strip().replace("", pd.NA)
        fill_value = _mode_or_default(values, "Not available")
        part = pd.get_dummies(values.fillna(fill_value), prefix=column, prefix_sep="=", dtype=float)
        if part.shape[1] == 0:
            part[f"{column}=Not available"] = 1.0
        parts.append(part)
        groups[column] = part.columns.tolist()
        state["categorical_fill"][column] = str(fill_value)
        state["categories"][column] = part.columns.tolist()
    encoded = pd.concat(parts, axis=1)
    if encoded.isna().any().any():
        raise ValueError("Feature encoding unexpectedly produced missing values.")
    return encoded, groups, state


def encode_model_features(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Median/mode-impute and one-hot encode predictors for the forest."""
    encoded, groups, _ = fit_model_feature_encoder(data)
    return encoded, groups


def transform_model_features(data: pd.DataFrame, state: dict[str, object]) -> pd.DataFrame:
    """Apply fitted forest preprocessing without learning from held-out rows."""
    parts: list[pd.DataFrame] = []
    for column in NUMERIC_FEATURES:
        values = data[column].map(experience_to_years) if column == "Years_of_Experience" else pd.to_numeric(data[column], errors="coerce")
        values = values.replace([np.inf, -np.inf], np.nan)
        parts.append(values.fillna(state["numeric_fill"][column]).astype(float).to_frame(column))
    for column in CATEGORICAL_FEATURES:
        values = data[column].astype("string").str.strip().replace("", pd.NA)
        values = values.fillna(state["categorical_fill"][column])
        part = pd.get_dummies(values, prefix=column, prefix_sep="=", dtype=float)
        parts.append(part.reindex(columns=state["categories"][column], fill_value=0.0))
    encoded = pd.concat(parts, axis=1)
    if encoded.isna().any().any():
        raise ValueError("Feature transformation unexpectedly produced missing values.")
    return encoded


def evaluate_engagement_model(data: pd.DataFrame) -> dict[str, object]:
    """Evaluate the retained forest with the documented stratified 70/30 split."""
    recent = data[data["Year"].between(RECENT_YEAR_MIN, YEAR_MAX)].copy()
    target, target_name = engagement_target(recent)
    labelled = recent.loc[target.notna(), MODEL_FEATURES + ["Year"]].copy()
    y = target.loc[target.notna()].astype(int)
    train_ids, test_ids = train_test_split(labelled.index, test_size=0.30, random_state=RANDOM_STATE, stratify=y)
    train_data, test_data = labelled.loc[train_ids], labelled.loc[test_ids]
    y_train, y_test = y.loc[train_ids], y.loc[test_ids]
    x_train, groups, state = fit_model_feature_encoder(train_data[MODEL_FEATURES])
    x_test = transform_model_features(test_data[MODEL_FEATURES], state)
    model = RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1, class_weight="balanced")
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    # Scikit-learn emits this compatibility warning under the project's
    # parallel configuration. Suppress only that known warning and only for
    # this call; the estimator, scoring, and parallelism are unchanged.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r".*sklearn\.utils\.parallel\.delayed should be used with.*sklearn\.utils\.parallel\.Parallel.*",
            category=UserWarning,
        )
        permutation = permutation_importance(model, x_test, y_test, n_repeats=10, random_state=RANDOM_STATE, n_jobs=-1, scoring="accuracy")
    return {
        "target_name": target_name, "target_years": sorted(labelled["Year"].unique().tolist()),
        "features": x_train, "groups": groups, "model": model, "y_train": y_train, "y_test": y_test,
        "metrics": {
            "accuracy": accuracy_score(y_test, predictions),
            "precision": precision_score(y_test, predictions, zero_division=0),
            "recall": recall_score(y_test, predictions, zero_division=0),
            "f1": f1_score(y_test, predictions, zero_division=0),
            "roc_auc": roc_auc_score(y_test, probabilities),
            "majority_class_accuracy": float((y_test == y_test.mode().iloc[0]).mean()),
        },
        "permutation_importance": pd.DataFrame({"feature": x_train.columns, "mean": permutation.importances_mean, "std": permutation.importances_std}),
    }


def fit_engagement_model(data: pd.DataFrame) -> pd.Series:
    """Fit the reference forest and aggregate one-hot importances by source feature."""
    recent = data[data["Year"].between(RECENT_YEAR_MIN, YEAR_MAX)].copy()
    target, target_name = engagement_target(recent)
    labelled = recent.loc[target.notna(), MODEL_FEATURES + ["Year"]].copy()
    y = target.loc[target.notna()].astype(int)
    if y.nunique() != 2:
        raise ValueError("The engagement target must contain both binary classes.")
    LOGGER.info("Training retained engagement reference model for '%s' on %s labelled responses.", target_name, len(labelled))
    features, groups = encode_model_features(labelled[MODEL_FEATURES])
    model = RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1, class_weight="balanced")
    model.fit(features, y)
    encoded = pd.Series(model.feature_importances_, index=features.columns)
    grouped = pd.Series({feature: float(encoded.reindex(columns, fill_value=0).sum()) for feature, columns in groups.items()}, name="importance")
    return (grouped / grouped.sum()).sort_values() if grouped.sum() > 0 else grouped.sort_values()


def plot_feature_importance(importances: pd.Series, output_path: Path) -> None:
    """Plot retained impurity importances when explicitly requested for reference."""
    labels = [FEATURE_LABELS.get(feature, feature) for feature in importances.index]
    fig, axis = plt.subplots(figsize=(13, 8))
    bars = axis.barh(labels, importances.values, color="#1F4E79", edgecolor="white")
    axis.bar_label(bars, labels=[f"{value:.3f}" for value in importances.values], padding=5, fontsize=11)
    axis.set_xlim(0, max(float(importances.max()) * 1.18, 0.1))
    axis.set_xlabel("Aggregated random-forest importance", fontsize=13)
    axis.set_ylabel("Predictor", fontsize=13)
    axis.set_title("Reference random-forest impurity importances", fontsize=17, pad=18, weight="semibold")
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
