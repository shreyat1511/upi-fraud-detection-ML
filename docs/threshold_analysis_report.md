# Random Forest threshold analysis

## Scope and safeguards

This analysis loads the saved Random Forest pipeline and evaluates it on **validation only** (steps 323–377; 973,173 rows, including 570 fraud and 972,603 legitimate transactions). No model was retrained, no test rows or labels were used for threshold selection or comparison, and the original CSV was not modified. The previously reported final test metrics remain the frozen evaluation in `results/final_test_metrics.json` and were not changed.

The analysis recalculated validation probabilities from the saved fitted pipeline to produce the threshold sweep. It uses `step`, `type`, and `amount`; no excluded IDs, balances, or rule flag were introduced.

## Threshold comparison

The CSV contains a sweep from 0.05 to 1.00 in 0.01 increments, plus the exact currently selected threshold and the two validation-derived operating points. Counts below use `prediction = score >= threshold`; confusion matrix order is `[[TN, FP], [FN, TP]]`.

| Validation operating point | Threshold | Precision | Recall | F1 | False positives | False negatives | True positives | True negatives |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Currently selected | 0.925415475 | 0.388889 | 0.171930 | 0.238443 | 154 | 472 | 98 | 972,449 |
| Validation maximum F1 | 0.9254154750209512 | 0.388889 | 0.171930 | **0.238443** | 154 | 472 | 98 | 972,449 |
| Higher recall (at least 50%) | 0.545923954763646 | 0.008055 | **0.500000** | 0.015854 | **35,098** | 285 | 285 | 937,505 |

The current threshold and validation F1-maximizing threshold are effectively the same and produce identical predictions. This confirms the stored threshold was selected at the validation F1 optimum.

At the 50% recall point, the model detects 187 more fraud cases than at the current threshold (285 vs. 98) and misses 187 fewer. It also flags 34,944 additional legitimate transactions (35,098 vs. 154). Precision falls from 38.89% to 0.81%, or roughly 123 false alerts per true positive. This threshold demonstrates a recall/false-alarm trade-off; it does **not** have better overall performance. Its F1 is much lower.

The plot shows precision, recall, F1 and both error counts over the threshold sweep. False-positive and false-negative counts use separate vertical scales in the lower panel so both remain visible.

![Validation threshold comparison](/C:/Users/somiv/Desktop/UPI-Fraud-Detection-ML/results/threshold_comparison.png)

## Recommendation for the educational application

Use **0.925415475 as the default demonstration threshold**, subject to approval before updating any application setting. It is the validation F1 optimum for the selected Random Forest and produces a compact alert set on validation (252 flagged transactions: 98 fraud and 154 legitimate). It is a defensible starting point for a demonstration that makes both precision and missed fraud visible.

The demonstration must also show the limitation: this default detects only 17.19% of validation fraud, missing 472 of 570 cases. An optional lower-threshold comparison can teach the recall trade-off, but it should show the accompanying false-positive count prominently. For example, the 50%-recall point detects 285 fraud cases and misses 285, while producing 35,098 false positives. Presenting only its recall would be misleading.

These scores are outputs from a class-weighted Random Forest trained on synthetic PaySim mobile-money data, not calibrated real-world UPI fraud probabilities. The dataset is a proxy, not actual UPI data. The recommendation is for an educational demonstration only, not a production payment decision.

## Generated files

- Threshold table: [`results/threshold_analysis.csv`](../results/threshold_analysis.csv)
- Threshold plot: [`results/threshold_comparison.png`](../results/threshold_comparison.png)
- Reproducible validation-only analysis script: [`scripts/analyze_thresholds.py`](../scripts/analyze_thresholds.py)

The script loads `models/random_forest_pipeline.joblib`, filters validation steps, and writes the sweep and plot. It does not write to `models/`, change the saved threshold, or access test metrics for this analysis.
