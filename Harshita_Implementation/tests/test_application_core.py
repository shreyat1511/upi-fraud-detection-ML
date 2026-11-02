"""Focused checks for model loading and prediction/input validation helpers."""

import ast
from io import BytesIO
from pathlib import Path
import unittest

import pandas as pd

from app_core import (
    APPROVED_THRESHOLD,
    InputValidationError,
    load_model_bundle,
    predict_transactions,
    read_batch_csv,
    validate_batch_frame,
    validate_single_transaction,
)


ROOT = Path(__file__).resolve().parents[1]


class ApplicationCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_model_bundle()

    def test_saved_model_and_threshold_load(self):
        self.assertEqual(self.bundle.metadata["selected_model"], "Random Forest")
        self.assertAlmostEqual(self.bundle.threshold, APPROVED_THRESHOLD, places=9)

    def test_single_valid_prediction(self):
        row = validate_single_transaction(400, "TRANSFER", 1500)
        result = predict_transactions(self.bundle, pd.DataFrame([row]))
        self.assertEqual(len(result), 1)
        self.assertGreaterEqual(float(result.iloc[0]["fraud_probability_percent"]), 0)
        self.assertLessEqual(float(result.iloc[0]["fraud_probability_percent"]), 100)
        self.assertEqual(float(result.iloc[0]["threshold"]), APPROVED_THRESHOLD)

    def test_invalid_single_inputs(self):
        for values in [(0, "TRANSFER", 1), (1.5, "TRANSFER", 1), (743, "UNKNOWN", 1), (2, "PAYMENT", -1), (2, "PAYMENT", float("inf"))]:
            with self.subTest(values=values), self.assertRaises(InputValidationError):
                validate_single_transaction(*values)

    def test_batch_validation_and_prediction(self):
        source = b"step,type,amount,unused\n400, transfer ,1500,x\n500,PAYMENT,75.5,y\n"
        valid = read_batch_csv(BytesIO(source))
        self.assertEqual(list(valid.columns), ["step", "type", "amount"])
        self.assertEqual(valid.iloc[0]["type"], "TRANSFER")
        scored = predict_transactions(self.bundle, valid)
        self.assertEqual(len(scored), 2)
        self.assertTrue((scored["threshold"] == APPROVED_THRESHOLD).all())

    def test_invalid_uploaded_csv(self):
        with self.assertRaises(InputValidationError):
            read_batch_csv(BytesIO(b"step,type\n1,CASH_IN\n"))
        with self.assertRaises(InputValidationError):
            read_batch_csv(BytesIO(b"this is not a valid delimited table"))

    def test_invalid_batch_values_and_columns(self):
        with self.assertRaises(InputValidationError):
            validate_batch_frame(pd.DataFrame({"step": [1], "type": ["CASH_IN"]}))
        with self.assertRaises(InputValidationError):
            validate_batch_frame(pd.DataFrame({"step": [744], "type": ["CASH_IN"], "amount": [3]}))
        with self.assertRaises(InputValidationError):
            validate_batch_frame(pd.DataFrame({"step": [1], "type": ["not-a-type"], "amount": [3]}))

    def test_app_startup_source_does_not_fit_a_model(self):
        trees = [ast.parse((ROOT / filename).read_text(encoding="utf-8")) for filename in ("app.py", "app_core.py")]
        calls = [node for tree in trees for node in ast.walk(tree) if isinstance(node, ast.Call)]
        fit_calls = [node for node in calls if isinstance(node.func, ast.Attribute) and node.func.attr == "fit"]
        self.assertEqual(fit_calls, [])


if __name__ == "__main__":
    unittest.main()
