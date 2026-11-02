#!/usr/bin/env python
"""Validation-only threshold analysis for the saved PaySim Random Forest.

Loads the fitted pipeline and scores only steps 323–377. It does not fit or
retrain a model and never evaluates or selects a threshold using test labels.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_curve, precision_score, recall_score


INPUT = Path("data/raw/PS_20174392719_1491204439457_log.csv")
PIPELINE = Path("models/random_forest_pipeline.joblib")
CURRENT_THRESHOLD = 0.925415475
VALIDATION_LOW, VALIDATION_HIGH = 323, 377


def collect_validation(path: Path) -> pd.DataFrame:
    parts = []
    for chunk in pd.read_csv(
        path, usecols=["step", "type", "amount", "isFraud"],
        dtype={"step": "int16", "type": "string", "amount": "float32", "isFraud": "uint8"},
        chunksize=250_000,
    ):
        val = chunk.loc[chunk["step"].between(VALIDATION_LOW, VALIDATION_HIGH), ["step", "type", "amount", "isFraud"]]
        if not val.empty:
            parts.append(val)
    if not parts:
        raise ValueError("No validation records found")
    validation = pd.concat(parts, ignore_index=True)
    if not validation["step"].between(VALIDATION_LOW, VALIDATION_HIGH).all():
        raise AssertionError("Non-validation rows entered threshold analysis")
    return validation


def metric_row(y: np.ndarray, p: np.ndarray, threshold: float, scenario: str) -> dict:
    pred = p >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "scenario": scenario,
        "threshold": float(threshold),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1_score": float(f1_score(y, pred, zero_division=0)),
        "false_positives": int(fp), "false_negatives": int(fn),
        "true_positives": int(tp), "true_negatives": int(tn),
    }


def main() -> None:
    if not INPUT.is_file() or not PIPELINE.is_file():
        raise FileNotFoundError(f"Required input or model missing: {INPUT}, {PIPELINE}")

    model = joblib.load(PIPELINE)
    validation = collect_validation(INPUT)
    y = validation["isFraud"].to_numpy(dtype=np.uint8)
    fitted_encoder = model.named_steps["preprocess"].named_transformers_["type"]
    categories = fitted_encoder.categories_[0]
    X = pd.DataFrame({
        "step": validation["step"].to_numpy(dtype=np.float32),
        "type": pd.Categorical(validation["type"].astype(str), categories=categories),
        "amount": validation["amount"].to_numpy(dtype=np.float32),
    })
    probabilities = model.predict_proba(X)[:, 1]

    precision, recall, thresholds = precision_recall_curve(y, probabilities)
    f1_values = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-15)
    max_f1 = np.nanmax(f1_values)
    f1_options = np.flatnonzero(np.isclose(f1_values, max_f1))
    f1_index = f1_options[np.argmax(thresholds[f1_options])]
    f1_threshold = float(thresholds[f1_index])

    # Educational high-recall point: among observed score thresholds reaching
    # at least 50% validation recall, choose the highest threshold (thus the
    # smallest alert set meeting that recall target).
    high_recall_options = np.flatnonzero(recall[:-1] >= 0.50)
    if not len(high_recall_options):
        raise RuntimeError("No threshold reaches the requested 50% validation recall")
    high_recall_threshold = float(thresholds[high_recall_options[-1]])

    grid = np.round(np.arange(0.05, 1.0001, 0.01), 2)
    named = {
        CURRENT_THRESHOLD: "currently_selected",
        f1_threshold: "validation_max_f1",
        high_recall_threshold: "higher_recall_at_least_50pct",
    }
    threshold_values = sorted(set(float(x) for x in grid) | set(named))
    rows = []
    for threshold in threshold_values:
        scenario = named.get(threshold, "grid")
        rows.append(metric_row(y, probabilities, threshold, scenario))
    table = pd.DataFrame(rows).sort_values("threshold").reset_index(drop=True)

    out = Path("results")
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "threshold_analysis.csv", index=False, float_format="%.12g")

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(table["threshold"], table["precision"], label="Precision", linewidth=1.8)
    axes[0].plot(table["threshold"], table["recall"], label="Recall", linewidth=1.8)
    axes[0].plot(table["threshold"], table["f1_score"], label="F1", linewidth=1.8)
    axes[0].set_ylabel("Score")
    axes[0].set_ylim(0, 1.02)
    axes[0].grid(alpha=0.25)
    axes[0].legend(loc="best")
    axes[0].set_title("Random Forest threshold analysis — validation steps 323–377 only")

    fp_line, = axes[1].plot(table["threshold"], table["false_positives"], label="False positives", linewidth=1.8, color="tab:blue")
    axes[1].set_xlabel("Probability threshold")
    axes[1].set_ylabel("False positives", color="tab:blue")
    axes[1].tick_params(axis="y", labelcolor="tab:blue")
    axes[1].grid(alpha=0.25)
    fn_axis = axes[1].twinx()
    fn_line, = fn_axis.plot(table["threshold"], table["false_negatives"], label="False negatives", linewidth=1.8, color="tab:orange")
    fn_axis.set_ylabel("False negatives", color="tab:orange")
    fn_axis.tick_params(axis="y", labelcolor="tab:orange")
    axes[1].legend([fp_line, fn_line], [fp_line.get_label(), fn_line.get_label()], loc="center left")
    marker_specs = [
        (CURRENT_THRESHOLD, "Current / max F1"),
        (high_recall_threshold, "Recall ≥ 50%"),
    ]
    for threshold, label in marker_specs:
        for ax in axes:
            ax.axvline(threshold, linestyle="--", linewidth=1, alpha=0.75)
        axes[0].annotate(label, (threshold, 0.98), xytext=(3, -4), textcoords="offset points", rotation=90, va="top", fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "threshold_comparison.png", dpi=160)
    plt.close(fig)

    summary = {
        "rows": len(validation), "fraud": int(y.sum()),
        "legitimate": int(len(y) - y.sum()),
        "fraud_prevalence": float(y.mean()),
        "current": metric_row(y, probabilities, CURRENT_THRESHOLD, "currently_selected"),
        "max_f1": metric_row(y, probabilities, f1_threshold, "validation_max_f1"),
        "higher_recall": metric_row(y, probabilities, high_recall_threshold, "higher_recall_at_least_50pct"),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
