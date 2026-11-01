"""Shared loading, validation, and inference helpers for the local Streamlit app."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


APP_ROOT = Path(__file__).resolve().parent
PIPELINE_PATH = APP_ROOT / "models" / "random_forest_pipeline.joblib"
METADATA_PATH = APP_ROOT / "models" / "model_selection.json"
VALIDATION_PATH = APP_ROOT / "results" / "validation_metrics.json"
TEST_PATH = APP_ROOT / "results" / "final_test_metrics.json"
COMPARISON_PATH = APP_ROOT / "results" / "model_comparison.csv"
APPROVED_THRESHOLD = 0.925415475
FEATURE_COLUMNS = ("step", "type", "amount")
TRANSACTION_TYPES = ("CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER")
MIN_STEP, MAX_STEP = 1, 743
MAX_BATCH_ROWS = 200_000


class InputValidationError(ValueError):
    """Raised when single or batch transaction data fails validation."""


@dataclass
class ModelBundle:
    pipeline: Any
    threshold: float
    metadata: dict
    validation_metrics: dict
    test_metrics: dict
    comparison: pd.DataFrame


def load_model_bundle() -> ModelBundle:
    """Load only the saved fitted Random Forest pipeline and its result files."""
    required = [PIPELINE_PATH, METADATA_PATH, VALIDATION_PATH, TEST_PATH, COMPARISON_PATH]
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Required application artifact(s) are missing: " + ", ".join(missing))

    with METADATA_PATH.open(encoding="utf-8") as handle:
        metadata = json.load(handle)
    if metadata.get("selected_model") != "Random Forest":
        raise ValueError("Saved model metadata does not identify Random Forest as the selected model")
    threshold = float(metadata.get("threshold", float("nan")))
    if not np.isfinite(threshold) or not np.isclose(threshold, APPROVED_THRESHOLD, rtol=0, atol=1e-8):
        raise ValueError("Saved threshold metadata does not match the approved application threshold")

    pipeline = joblib.load(PIPELINE_PATH)
    if not hasattr(pipeline, "predict_proba") or not hasattr(pipeline, "named_steps"):
        raise ValueError("Saved artifact is not a fitted preprocessing/model pipeline")
    if "preprocess" not in pipeline.named_steps or "model" not in pipeline.named_steps:
        raise ValueError("Saved pipeline is missing its fitted preprocessing or model step")
    encoder = pipeline.named_steps["preprocess"].named_transformers_.get("type")
    if encoder is None or not hasattr(encoder, "categories_"):
        raise ValueError("Saved pipeline does not contain the fitted transaction type encoder")

    with VALIDATION_PATH.open(encoding="utf-8") as handle:
        validation_metrics = json.load(handle)
    with TEST_PATH.open(encoding="utf-8") as handle:
        test_metrics = json.load(handle)
    comparison = pd.read_csv(COMPARISON_PATH)
    if test_metrics.get("selected_model") != "Random Forest":
        raise ValueError("Frozen test results do not identify Random Forest as the selected model")
    if not np.isclose(float(test_metrics.get("selected_threshold_from_validation", np.nan)), threshold, rtol=0, atol=1e-8):
        raise ValueError("Frozen test metrics use a different threshold from saved model metadata")

    return ModelBundle(pipeline, APPROVED_THRESHOLD, metadata, validation_metrics, test_metrics, comparison)


def validate_single_transaction(step: Any, transaction_type: Any, amount: Any) -> dict:
    """Validate and normalize one user-supplied transaction."""
    if isinstance(step, bool):
        raise InputValidationError("Step must be a whole number from 1 to 743.")
    try:
        step_num = float(step)
    except (TypeError, ValueError):
        raise InputValidationError("Step must be a whole number from 1 to 743.") from None
    if not np.isfinite(step_num) or not step_num.is_integer() or not MIN_STEP <= step_num <= MAX_STEP:
        raise InputValidationError("Step must be a whole number from 1 to 743.")

    tx_type = str(transaction_type).strip().upper()
    if tx_type not in TRANSACTION_TYPES:
        raise InputValidationError("Choose one of the five supported transaction types.")

    try:
        amount_num = float(amount)
    except (TypeError, ValueError):
        raise InputValidationError("Amount must be a finite number greater than or equal to 0.") from None
    if not np.isfinite(amount_num) or amount_num < 0:
        raise InputValidationError("Amount must be a finite number greater than or equal to 0.")
    return {"step": int(step_num), "type": tx_type, "amount": amount_num}


def validate_batch_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Return normalized feature-only rows or raise with actionable errors."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise InputValidationError("The CSV is empty or could not be read as a table.")
    if len(frame) > MAX_BATCH_ROWS:
        raise InputValidationError(f"The CSV exceeds the {MAX_BATCH_ROWS:,}-row local processing limit.")
    missing = [name for name in FEATURE_COLUMNS if name not in frame.columns]
    if missing:
        raise InputValidationError("Missing required column(s): " + ", ".join(missing))

    out = frame.loc[:, list(FEATURE_COLUMNS)].copy()
    problems: list[str] = []
    step_values = pd.to_numeric(out["step"], errors="coerce")
    invalid_step = step_values.isna() | ~np.isfinite(step_values) | (step_values % 1 != 0) | (step_values < MIN_STEP) | (step_values > MAX_STEP)
    for idx in np.flatnonzero(invalid_step.to_numpy())[:10]:
        problems.append(f"row {idx + 2}: step must be a whole number from 1 to 743")

    tx_values = out["type"].astype("string").str.strip().str.upper()
    invalid_type = tx_values.isna() | ~tx_values.isin(TRANSACTION_TYPES)
    for idx in np.flatnonzero(invalid_type.to_numpy())[:10]:
        problems.append(f"row {idx + 2}: type must be one of {', '.join(TRANSACTION_TYPES)}")

    amount_values = pd.to_numeric(out["amount"], errors="coerce")
    invalid_amount = amount_values.isna() | ~np.isfinite(amount_values) | (amount_values < 0)
    for idx in np.flatnonzero(invalid_amount.to_numpy())[:10]:
        problems.append(f"row {idx + 2}: amount must be a finite number >= 0")

    if problems:
        total_bad_rows = int((invalid_step | invalid_type | invalid_amount).sum())
        suffix = f" Showing up to 10 issues; {total_bad_rows:,} row(s) contain invalid values." if total_bad_rows > 10 else ""
        raise InputValidationError("Invalid transaction data: " + "; ".join(problems) + suffix)

    out["step"] = step_values.astype(np.int16)
    out["type"] = tx_values.astype(str)
    out["amount"] = amount_values.astype(np.float32)
    return out.reset_index(drop=True)


def read_batch_csv(file_obj) -> pd.DataFrame:
    """Parse and validate an uploaded CSV without persisting or transmitting it."""
    try:
        frame = pd.read_csv(file_obj, nrows=MAX_BATCH_ROWS + 1)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError, ValueError) as exc:
        raise InputValidationError("Upload must be a readable CSV with a header row.") from exc
    if len(frame) > MAX_BATCH_ROWS:
        raise InputValidationError(f"The CSV exceeds the {MAX_BATCH_ROWS:,}-row local processing limit.")
    return validate_batch_frame(frame)


def predict_transactions(bundle: ModelBundle, features: pd.DataFrame) -> pd.DataFrame:
    """Score validated feature rows with the persisted pipeline and threshold."""
    if list(features.columns) != list(FEATURE_COLUMNS):
        raise InputValidationError("Prediction input must contain only step, type, and amount in that order.")
    preprocessor = bundle.pipeline.named_steps["preprocess"]
    categories = preprocessor.named_transformers_["type"].categories_[0]
    model_input = pd.DataFrame({
        "step": features["step"].to_numpy(dtype=np.float32),
        "type": pd.Categorical(features["type"].astype(str), categories=categories),
        "amount": features["amount"].to_numpy(dtype=np.float32),
    })
    probabilities = bundle.pipeline.predict_proba(model_input)[:, 1]
    labels = probabilities >= bundle.threshold
    return pd.DataFrame({
        "fraud_probability_percent": probabilities * 100,
        "prediction": np.where(labels, "Fraud indication", "No fraud indication"),
        "threshold": bundle.threshold,
    })
