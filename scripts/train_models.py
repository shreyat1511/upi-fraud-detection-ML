#!/usr/bin/env python
"""Train/evaluate approved PaySim baselines using a chronological split.

The raw CSV is read only. Preprocessing is fitted separately within each model
pipeline on the training split. Test metrics are calculated once for the model
selected from validation results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
import traceback
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix,
    f1_score, precision_recall_curve, precision_score, recall_score,
    roc_auc_score, roc_curve,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier


FEATURES = ["step", "type", "amount"]
TARGET = "isFraud"
SPLITS = {"train": (1, 322), "validation": (323, 377), "test": (378, 743)}
EXCLUDED = [
    "nameOrig", "nameDest", "oldbalanceOrg", "newbalanceOrig",
    "oldbalanceDest", "newbalanceDest", "isFlaggedFraud",
]
SEED = 42
CHUNK_SIZE = 250_000


def log(message: str) -> None:
    print(message, flush=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_splits(path: Path, chunk_size: int = CHUNK_SIZE):
    """Two-pass chunked read into compact arrays; no split CSV copies needed."""
    required = ["step", "type", "amount", TARGET]
    counts = {name: 0 for name in SPLITS}
    frauds = {name: 0 for name in SPLITS}
    train_types: set[str] = set()
    for chunk in pd.read_csv(
        path, usecols=required,
        dtype={"step": "int16", "amount": "float32", TARGET: "uint8", "type": "string"},
        chunksize=chunk_size,
    ):
        if chunk[required].isna().any().any():
            raise ValueError("Missing values found in selected features/target")
        if not chunk[TARGET].isin([0, 1]).all():
            raise ValueError("Target is not binary")
        for name, (low, high) in SPLITS.items():
            mask = chunk["step"].between(low, high)
            counts[name] += int(mask.sum())
            frauds[name] += int(chunk.loc[mask, TARGET].sum())
            if name == "train":
                train_types.update(chunk.loc[mask, "type"].astype(str).unique())

    categories = sorted(train_types)
    if not categories:
        raise ValueError("No transaction types found in the training period")
    type_code = {value: i for i, value in enumerate(categories)}
    arrays = {}
    positions = {name: 0 for name in SPLITS}
    for name, n in counts.items():
        arrays[name] = {
            "step": np.empty(n, dtype=np.float32),
            "type": np.empty(n, dtype=np.int8),
            "amount": np.empty(n, dtype=np.float32),
            TARGET: np.empty(n, dtype=np.uint8),
        }

    for chunk in pd.read_csv(
        path, usecols=required,
        dtype={"step": "int16", "amount": "float32", TARGET: "uint8", "type": "string"},
        chunksize=chunk_size,
    ):
        for name, (low, high) in SPLITS.items():
            part = chunk.loc[chunk["step"].between(low, high), required]
            if part.empty:
                continue
            start = positions[name]
            end = start + len(part)
            target = arrays[name]
            target["step"][start:end] = part["step"].to_numpy(dtype=np.float32, copy=False)
            target["amount"][start:end] = part["amount"].to_numpy(dtype=np.float32, copy=False)
            codes = part["type"].astype(str).map(type_code).fillna(-1).to_numpy()
            if (codes < 0).any():
                raise ValueError(f"Unseen type category in {name} split")
            target["type"][start:end] = codes.astype(np.int8, copy=False)
            target[TARGET][start:end] = part[TARGET].to_numpy(dtype=np.uint8, copy=False)
            positions[name] = end

    if any(positions[name] != counts[name] for name in SPLITS):
        raise RuntimeError("Split row counts changed between read passes")
    return arrays, categories, counts, frauds


def as_frame(split, categories):
    return pd.DataFrame({
        "step": split["step"],
        "type": pd.Categorical.from_codes(split["type"], categories=categories),
        "amount": split["amount"],
    }, copy=False)


def make_preprocessor(scale_numeric: bool):
    step_pipe = StandardScaler() if scale_numeric else "passthrough"
    amount_pipe = Pipeline([
        ("log1p", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
        ("scale", StandardScaler() if scale_numeric else "passthrough"),
    ])
    return ColumnTransformer(
        transformers=[
            ("step", step_pipe, ["step"]),
            ("amount", amount_pipe, ["amount"]),
            ("type", OneHotEncoder(handle_unknown="ignore", sparse_output=True, dtype=np.float32), ["type"]),
        ],
        sparse_threshold=1.0,
        verbose_feature_names_out=True,
    )


def make_pipeline(model_name: str):
    if model_name == "Logistic Regression":
        estimator = LogisticRegression(
            class_weight="balanced", C=1.0, solver="lbfgs", max_iter=200,
            tol=1e-4, random_state=SEED,
        )
        scale_numeric = True
    elif model_name == "Decision Tree":
        estimator = DecisionTreeClassifier(
            class_weight="balanced", criterion="gini", max_depth=12,
            min_samples_leaf=50, random_state=SEED,
        )
        scale_numeric = False
    elif model_name == "Random Forest":
        estimator = RandomForestClassifier(
            n_estimators=50, max_depth=12, min_samples_leaf=100,
            max_features="sqrt", class_weight="balanced_subsample",
            n_jobs=2, random_state=SEED,
        )
        scale_numeric = False
    else:
        raise ValueError(model_name)
    return Pipeline([("preprocess", make_preprocessor(scale_numeric)), ("model", estimator)])


def score_predictions(y, probabilities, threshold):
    predictions = (probabilities >= threshold).astype(np.uint8)
    cm = confusion_matrix(y, predictions, labels=[0, 1])
    return {
        "threshold": float(threshold),
        "precision": float(precision_score(y, predictions, zero_division=0)),
        "recall": float(recall_score(y, predictions, zero_division=0)),
        "f1": float(f1_score(y, predictions, zero_division=0)),
        "pr_auc_average_precision": float(average_precision_score(y, probabilities)),
        "roc_auc": float(roc_auc_score(y, probabilities)),
        "accuracy": float(accuracy_score(y, predictions)),
        "confusion_matrix_tn_fp_fn_tp": cm.tolist(),
        "true_negatives": int(cm[0, 0]), "false_positives": int(cm[0, 1]),
        "false_negatives": int(cm[1, 0]), "true_positives": int(cm[1, 1]),
        "n": int(len(y)), "fraud_count": int(np.sum(y)),
        "legitimate_count": int(len(y) - np.sum(y)),
        "fraud_prevalence": float(np.mean(y)),
    }


def best_f1_threshold(y, probabilities):
    precision, recall, thresholds = precision_recall_curve(y, probabilities)
    if len(thresholds) == 0:
        return 0.5
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-15)
    maximum = np.nanmax(f1)
    choices = np.flatnonzero(np.isclose(f1, maximum))
    # For an F1 tie, prefer the higher threshold to reduce alert volume.
    idx = choices[np.argmax(thresholds[choices])]
    return float(thresholds[idx])


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def plot_curves(path: Path, curves, kind: str):
    plt.figure(figsize=(8, 6))
    for name, y, p in curves:
        if kind == "pr":
            precision, recall, _ = precision_recall_curve(y, p)
            plt.plot(recall, precision, label=f"{name} (AP={average_precision_score(y, p):.4f})")
        else:
            fpr, tpr, _ = roc_curve(y, p)
            plt.plot(fpr, tpr, label=f"{name} (AUC={roc_auc_score(y, p):.4f})")
    if kind == "pr":
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.title("Validation precision–recall curves")
    else:
        plt.plot([0, 1], [0, 1], "--", color="gray", linewidth=1)
        plt.xlabel("False positive rate")
        plt.ylabel("True positive rate")
        plt.title("Validation ROC curves")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def plot_confusion(path: Path, matrix):
    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    image = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks([0, 1], ["Legitimate", "Fraud"])
    ax.set_yticks([0, 1], ["Legitimate", "Fraud"])
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("Actual label")
    ax.set_title("Selected model: held-out test confusion matrix")
    for (i, j), value in np.ndenumerate(matrix):
        ax.text(j, i, f"{value:,}", ha="center", va="center", color="black")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_importance(path: Path, fitted, names):
    fig, axes = plt.subplots(1, len(fitted), figsize=(16, 7), sharey=False)
    for ax, (model_name, pipeline) in zip(axes, fitted.items()):
        estimator = pipeline.named_steps["model"]
        if hasattr(estimator, "feature_importances_"):
            values = estimator.feature_importances_
        elif hasattr(estimator, "coef_"):
            values = np.mean(np.abs(estimator.coef_), axis=0)
        else:
            ax.set_visible(False)
            continue
        order = np.argsort(values)[-len(values):]
        ax.barh(np.array(names)[order], values[order], color="#3977a8")
        ax.set_title(model_name)
        ax.set_xlabel("Importance" if hasattr(estimator, "feature_importances_") else "Mean absolute coefficient")
        ax.tick_params(axis="y", labelsize=8)
    fig.suptitle("Model feature importance (model-specific measures)")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main():
    global SEED
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="?", type=Path, default=Path("data/raw/PS_20174392719_1491204439457_log.csv"))
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    SEED = args.seed

    if not args.csv.is_file():
        raise FileNotFoundError(args.csv)
    models_dir = Path("models")
    results_dir = Path("results")
    models_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)

    log("Reading and partitioning CSV into compact arrays (two passes)...")
    start_load = time.perf_counter()
    arrays, categories, counts, frauds = load_splits(args.csv, args.chunk_size)
    load_seconds = time.perf_counter() - start_load
    log(f"Loaded partitions in {load_seconds:.1f}s; training transaction types: {categories}")

    X_train, y_train = as_frame(arrays["train"], categories), arrays["train"][TARGET]
    X_val, y_val = as_frame(arrays["validation"], categories), arrays["validation"][TARGET]
    X_test, y_test = as_frame(arrays["test"], categories), arrays["test"][TARGET]

    model_names = ["Logistic Regression", "Decision Tree", "Random Forest"]
    fitted = {}
    val_probabilities = {}
    thresholds = {}
    validation_metrics = {}
    comparison_rows = []
    curve_entries = []
    errors = {}
    for name in model_names:
        log(f"Training {name}...")
        pipeline = make_pipeline(name)
        fit_start = time.perf_counter()
        try:
            pipeline.fit(X_train, y_train)
            train_seconds = time.perf_counter() - fit_start
            pred_start = time.perf_counter()
            probabilities = pipeline.predict_proba(X_val)[:, 1]
            prediction_seconds = time.perf_counter() - pred_start
            threshold = best_f1_threshold(y_val, probabilities)
            metrics = score_predictions(y_val, probabilities, threshold)
            metrics["training_time_seconds"] = train_seconds
            metrics["validation_prediction_time_seconds"] = prediction_seconds
            validation_metrics[name] = metrics
            fitted[name] = pipeline
            val_probabilities[name] = probabilities
            thresholds[name] = threshold
            curve_entries.append((name, y_val, probabilities))
            comparison_rows.append({"model": name, "status": "success", **metrics})
            log(f"{name}: validation AP={metrics['pr_auc_average_precision']:.6f}, F1={metrics['f1']:.6f}, recall={metrics['recall']:.6f}, precision={metrics['precision']:.6f}, threshold={threshold:.8g}, fit={train_seconds:.1f}s")
        except Exception as exc:
            errors[name] = {"error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc()}
            comparison_rows.append({"model": name, "status": "failed", "error_type": type(exc).__name__, "error": str(exc)})
            log(f"ERROR: {name} failed: {type(exc).__name__}: {exc}")
            del pipeline

    if not fitted:
        write_json(results_dir / "validation_metrics.json", {
            "status": "all_models_failed", "errors": errors,
            "feature_columns": FEATURES, "target": TARGET,
        })
        pd.DataFrame(comparison_rows).to_csv(results_dir / "model_comparison.csv", index=False)
        raise RuntimeError("All specified models failed; see results/model_comparison.csv and validation_metrics.json")

    # Ranking is validation-only: maximize AP, then F1, then recall.
    selected_name = max(
        fitted,
        key=lambda name: (
            validation_metrics[name]["pr_auc_average_precision"],
            validation_metrics[name]["f1"], validation_metrics[name]["recall"],
        ),
    )
    selected_threshold = thresholds[selected_name]
    log(f"Selected on validation by (AP, F1, recall): {selected_name}; threshold={selected_threshold:.8g}")

    # One final test prediction/evaluation for the selected model only.
    log("Evaluating selected model on test once...")
    test_start = time.perf_counter()
    test_probabilities = fitted[selected_name].predict_proba(X_test)[:, 1]
    test_prediction_seconds = time.perf_counter() - test_start
    test_metrics = score_predictions(y_test, test_probabilities, selected_threshold)
    test_metrics["prediction_time_seconds"] = test_prediction_seconds

    input_hash = sha256(args.csv)
    common = {
        "dataset": str(args.csv.resolve()), "dataset_sha256": input_hash,
        "dataset_size_bytes": args.csv.stat().st_size,
        "dataset_framing": "Synthetic PaySim mobile-money data used as a proxy; not actual UPI data.",
        "features": FEATURES, "target": TARGET, "excluded_features": EXCLUDED,
        "split_boundaries_inclusive": {k: list(v) for k, v in SPLITS.items()},
        "split_counts": {
            k: {"rows": counts[k], "fraud": frauds[k], "legitimate": counts[k] - frauds[k],
                "fraud_prevalence": frauds[k] / counts[k]}
            for k in SPLITS
        },
        "random_seed": args.seed,
        "versions": {"python": platform.python_version(), "pandas": pd.__version__,
                     "numpy": np.__version__, "scipy": scipy.__version__, "scikit_learn": sklearn.__version__},
        "load_time_seconds_two_passes": load_seconds,
        "preprocessing": {
            "type": "OneHotEncoder(handle_unknown='ignore', sparse_output=True), fitted on training data",
            "amount": "log1p; StandardScaler for Logistic Regression, passthrough scaling for tree models",
            "step": "StandardScaler for Logistic Regression, raw numeric for tree models",
            "imbalance": "class_weight='balanced' for Logistic Regression and Decision Tree; balanced_subsample for Random Forest; validation/test unchanged",
        },
    }
    write_json(results_dir / "validation_metrics.json", {
        **common, "model_parameters": {
            "Logistic Regression": {"C": 1.0, "solver": "lbfgs", "max_iter": 200, "tol": 1e-4, "class_weight": "balanced"},
            "Decision Tree": {"criterion": "gini", "max_depth": 12, "min_samples_leaf": 50, "class_weight": "balanced"},
            "Random Forest": {"n_estimators": 50, "max_depth": 12, "min_samples_leaf": 100, "max_features": "sqrt", "class_weight": "balanced_subsample", "n_jobs": 2},
        },
        "threshold_selection": "For each model, maximize validation F1 over thresholds; ties choose the higher threshold. Select final model by validation PR-AUC (Average Precision), then F1, then recall.",
        "validation_metrics_by_model": validation_metrics,
        "model_errors": errors,
        "selected_model": selected_name, "selected_threshold": selected_threshold,
    })
    write_json(results_dir / "final_test_metrics.json", {
        **common, "selected_model": selected_name,
        "selected_threshold_from_validation": selected_threshold,
        "selection_rule": "Validation PR-AUC (Average Precision), then validation F1, then recall.",
        "test_metrics": test_metrics,
        "validation_metrics_for_selected_model": validation_metrics[selected_name],
    })
    pd.DataFrame(comparison_rows).to_csv(results_dir / "model_comparison.csv", index=False)
    plot_curves(results_dir / "precision_recall_curve.png", curve_entries, "pr")
    plot_curves(results_dir / "roc_curve.png", curve_entries, "roc")
    plot_confusion(results_dir / "confusion_matrix.png", np.array(test_metrics["confusion_matrix_tn_fp_fn_tp"]))
    names = fitted[selected_name].named_steps["preprocess"].get_feature_names_out()
    plot_importance(results_dir / "feature_importance.png", fitted, names)
    for model_name, pipeline in fitted.items():
        safe_name = model_name.lower().replace(" ", "_")
        joblib.dump(pipeline, models_dir / f"{safe_name}_pipeline.joblib", compress=3)
    joblib.dump(fitted[selected_name], models_dir / "final_model_pipeline.joblib", compress=3)
    write_json(models_dir / "model_selection.json", {
        "selected_model": selected_name, "threshold": selected_threshold,
        "validation_selection_rule": "highest PR-AUC (Average Precision), then F1, then recall",
        "features": FEATURES, "target": TARGET, "random_seed": args.seed,
        "dataset_sha256": input_hash,
    })

    log("Completed. Generated model, validation/test metrics, comparison table, and plots.")
    if errors:
        log("One or more specified models failed; details are recorded and no substitute was used.")
        sys.exit(2)


if __name__ == "__main__":
    main()
