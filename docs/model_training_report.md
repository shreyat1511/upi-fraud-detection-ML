# PaySim model training and evaluation report

## Summary

Three requested models were trained on the approved chronological split using `step`, `type`, and `amount` to predict `isFraud`. PaySim is synthetic mobile-money data used as a proxy; it is **not actual UPI transaction data**. No additional data was downloaded, and the raw CSV was read only.

The **Random Forest** was selected using validation results because it had the highest validation PR-AUC (Average Precision), with F1 and recall as tie-breakers. Its classification threshold, selected by maximizing validation F1, was **0.925415475**. The held-out test was evaluated once for this selected model and threshold.

The selected model has test precision 0.8834, recall 0.1945, F1 0.3188, Average Precision 0.2355, and ROC-AUC 0.8967. It identifies 780 of 4,010 fraud records at the chosen threshold, while missing 3,230. This is a high-precision, low-recall operating point and should not be described as adequate fraud coverage without an explicitly chosen business tradeoff.

## Dataset, split, and features

- **Input:** `data/raw/PS_20174392719_1491204439457_log.csv` (493,534,783 bytes).
- **SHA-256:** `16910f90577b0d981bf8ff289714510bb89bc71bff7d3f220f024e287e4eea6b`.
- **Features:** `step`, `type`, `amount`.
- **Target:** `isFraud`.
- **Excluded:** `nameOrig`, `nameDest`, `oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, `newbalanceDest`, and `isFlaggedFraud`.
- **Chronological boundaries:** train steps 1–322; validation steps 323–377; test steps 378–743. Step groups were kept intact.

| Split | Records | Legitimate | Fraud | Fraud prevalence |
|---|---:|---:|---:|---:|
| Train | 4,433,703 | 4,430,070 | 3,633 | 0.081941% |
| Validation | 973,173 | 972,603 | 570 | 0.058571% |
| Test | 955,744 | 951,734 | 4,010 | 0.419568% |

The test period’s fraud prevalence is about 7.2 times the validation prevalence and about 5.1 times the training prevalence. This substantial temporal shift is preserved rather than hidden with random splitting or resampling. It affects threshold-level precision and limits direct comparison of validation and test metrics.

## Preprocessing and model settings

Data was read in chunks twice and accumulated in compact numeric arrays. No split copies were written. For each model, a scikit-learn pipeline fit preprocessing on training data only. `type` was one-hot encoded into sparse features; validation and test retained their natural class distributions.

- Logistic Regression: `log1p(amount)` and standardized `step`/amount, `class_weight="balanced"`, `C=1.0`, `lbfgs`, `max_iter=200`, seed 42.
- Decision Tree: `log1p(amount)`, raw step, `class_weight="balanced"`, Gini, max depth 12, minimum leaf size 50, seed 42.
- Random Forest: `log1p(amount)`, raw step, `class_weight="balanced_subsample"`, 50 trees, max depth 12, minimum leaf size 100, `max_features="sqrt"`, 2 workers, seed 42.

The Random Forest configuration was bounded to keep runtime manageable. An initial, more expensive 100-tree/depth-16 attempt was stopped before producing metrics; the reported Random Forest is the completed 50-tree configuration above. No model was silently substituted.

The per-model binary classification threshold was selected on validation by maximizing F1; ties prefer the higher threshold. The final model was selected by validation Average Precision, then F1, then recall. This makes the comparison prioritize ranking quality for the rare fraud class; it explains why Random Forest was selected even though Decision Tree had slightly higher validation F1 at its own threshold. Test scores were not used for model or threshold selection.

## Validation comparison

Validation has 570 fraud cases and 972,603 legitimate cases. Confusion matrices use `[[TN, FP], [FN, TP]]` at each model’s own F1-selected validation threshold.

| Model | Threshold | Precision | Recall | F1 | PR-AUC (Average Precision) | ROC-AUC | Accuracy | Confusion matrix `[[TN,FP],[FN,TP]]` | Fit time | Validation prediction time |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| Logistic Regression | 0.9083696 | 0.006614 | 0.045614 | 0.011553 | 0.003196 | 0.882741 | 0.995428 | `[[968698,3905],[544,26]]` | 5.51 s | 0.257 s |
| Decision Tree | 0.9988298 | 0.841584 | 0.149123 | 0.253353 | 0.146312 | 0.734944 | 0.999485 | `[[972587,16],[485,85]]` | 21.20 s | 0.316 s |
| Random Forest | 0.9254155 | 0.388889 | 0.171930 | 0.238443 | **0.152985** | **0.897926** | 0.999357 | `[[972449,154],[472,98]]` | 277.23 s | 1.665 s |

Accuracy is high for all three because legitimate transactions dominate the dataset; it is not a useful primary comparison here. Logistic Regression has a high ROC-AUC but very weak Average Precision and recall at its validation F1 threshold, illustrating why ROC-AUC and accuracy alone can mislead on this rare-event task. The selected Random Forest improves validation ranking (Average Precision) and recall over the Decision Tree, at the cost of lower precision and slightly lower F1 at their respective thresholds.

## Final held-out test result

Only the validation-selected Random Forest was scored on test, once, at the frozen validation threshold **0.925415475**. Test contains 4,010 fraud and 951,734 legitimate records.

| Metric | Test result |
|---|---:|
| Precision | 0.883352 |
| Recall | 0.194514 |
| F1-score | 0.318823 |
| PR-AUC (Average Precision) | 0.235508 |
| ROC-AUC | 0.896722 |
| Accuracy (secondary) | 0.996513 |
| Prediction time (full test partition) | 1.485 s |

Confusion matrix, `[[TN, FP], [FN, TP]]`:

```text
[[951631, 103],
 [  3230, 780]]
```

At this threshold, 780 of the 4,010 test fraud cases were detected and 3,230 were missed; 103 legitimate transactions were flagged. The higher test prevalence contributes to the test precision increase relative to validation. The low recall is a material limitation, despite strong precision and ranking metrics. A different operating point could trade precision for recall, but changing it should be based on a declared operational objective and validated without using the test outcomes for tuning.

## Generated deliverables

- Training/evaluation script: [`scripts/train_models.py`](../scripts/train_models.py)
- Validation comparison CSV: [`results/model_comparison.csv`](../results/model_comparison.csv)
- Full validation metrics and configuration: [`results/validation_metrics.json`](../results/validation_metrics.json)
- Selected-model final test metrics: [`results/final_test_metrics.json`](../results/final_test_metrics.json)
- Test confusion matrix: [`results/confusion_matrix.png`](../results/confusion_matrix.png)
- Validation precision-recall curves: [`results/precision_recall_curve.png`](../results/precision_recall_curve.png)
- Validation ROC curves: [`results/roc_curve.png`](../results/roc_curve.png)
- Feature importance/coefficient plots for all three models: [`results/feature_importance.png`](../results/feature_importance.png)
- All fitted model pipelines: `models/logistic_regression_pipeline.joblib`, `models/decision_tree_pipeline.joblib`, `models/random_forest_pipeline.joblib`
- Selected-model alias and metadata: `models/final_model_pipeline.joblib`, `models/model_selection.json`

The feature-importance figure uses model-specific measures (absolute Logistic Regression coefficients and tree impurity importances), so values should not be compared as if they shared a common scale. The curves are validation curves; the final confusion matrix is for the one selected test evaluation.

## Reproducibility and limitations

Run `python scripts/train_models.py` from the workspace root to repeat training and evaluation with the same seed and split. The JSON files record the input path and SHA-256, package versions, preprocessing, boundaries, parameters, thresholds, metrics, and measured runtimes. The script reads the original CSV and does not modify it.

The data are synthetic PaySim mobile-money records, not UPI transactions. Only three initial features were used, which deliberately excludes identifiers, balances, and the rule flag. Strong temporal prevalence shift, simulator-specific labels, poor final recall at the selected threshold, and the absence of actual UPI traffic limit external validity. No web application was built.

## Runtime environment

Python 3.13.7; pandas 2.3.3; NumPy 2.2.6; SciPy 1.18.1; scikit-learn 1.9.1. Random seed: 42.
