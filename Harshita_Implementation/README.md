# UPI Transaction Fraud Detection Using Machine Learning

**Authors:** Shreya Thapa and Harshita Bagwe  
**Project type:** Academic machine learning research prototype

This project studies transaction fraud detection with a saved machine learning pipeline and a local Streamlit dashboard. PaySim is used as a reproducible proxy dataset. **PaySim contains synthetic mobile-money transactions, not actual UPI transaction data.** Results from this project therefore do not establish performance on UPI payments, Indian banks, NPCI systems, or production payment traffic.

## Project features

- Overview of the selected model, approved classification threshold, and frozen test results.
- Single transaction scoring with a fraud score and threshold-based indication.
- Comparison of Logistic Regression, Decision Tree, and Random Forest results.
- Batch CSV scoring with input validation and downloadable predictions.
- Documentation of dataset provenance, chronological evaluation, class imbalance, temporal shift, and limitations.
- Reuse of the saved fitted preprocessing and Random Forest pipeline. The application does not train or retrain models at startup.
- Local processing of uploaded CSV content; the application sends transaction rows to no external prediction endpoint.

## Dataset and provenance

The project uses the [PaySim1 dataset on Kaggle](https://www.kaggle.com/datasets/ealaxi/paysim1). The simulator is described in [PaySim: A Financial Mobile Money Simulator for Fraud Detection](https://www.msc-les.org/proceedings/emss/2016/EMSS2016_249.pdf). PaySim generates synthetic mobile-money records using a simulator informed by aggregated activity. Its records are **not actual UPI, NPCI, Indian bank, or production payment data**.

The raw CSV, `PS_20174392719_1491204439457_log.csv`, is intentionally excluded from GitHub because it is large. To reproduce training and evaluation, obtain the dataset from the linked Kaggle source in accordance with its current terms, then place the CSV at:

```text
data/raw/PS_20174392719_1491204439457_log.csv
```

**The saved application can run without downloading the raw dataset.** It uses the saved model pipeline, model metadata, metrics, comparison table, and figures under `models/` and `results/`. The raw CSV is needed only for data inspection or to repeat dataset preparation, training, and evaluation. After placing the CSV at the path above, training and evaluation can be repeated with `python scripts/train_models.py` from the project root.

## Features and target

The model uses these three transaction inputs:

| Feature | Description |
|---|---|
| `step` | PaySim relative simulation step; it is not a calendar timestamp. |
| `type` | One of CASH_IN, CASH_OUT, DEBIT, PAYMENT, or TRANSFER. |
| `amount` | Transaction amount in the synthetic dataset. |

The training target is `isFraud`. The model excludes `nameOrig`, `nameDest`, all four balance fields (`oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, `newbalanceDest`), and `isFlaggedFraud`. The application accepts only `step`, `type`, and `amount`; it does not request the target.

## Model and evaluation

Logistic Regression, Decision Tree, and Random Forest were compared using a chronological split: train on steps 1–322, validate on steps 323–377, and test on steps 378–743. Preprocessing was fitted on training data only. Validation and test retained their natural class distributions.

Random Forest was selected using validation PR-AUC (Average Precision), with F1 and recall as tie-breakers. The approved threshold, **0.925415475**, was selected using validation data. Test results below are the frozen evaluation of the selected model and threshold; test data was not used to choose the threshold.

| Frozen test metric | Result |
|---|---:|
| Precision | 0.883352 |
| Recall | 0.194514 |
| F1-score | 0.318823 |
| PR-AUC (Average Precision) | 0.235508 |
| ROC-AUC | 0.896722 |
| Accuracy (secondary metric) | 0.996513 |
| Confusion matrix `[[TN, FP], [FN, TP]]` | `[[951631, 103], [3230, 780]]` |

At the frozen threshold, the model detected 780 of 4,010 test fraud-labeled records and **missed 3,230**. The high precision comes with low recall; this model is not suitable for making real payment decisions. Accuracy is shown only as a secondary metric because legitimate transactions dominate the dataset.

The test-set fraud prevalence (0.419568%) is higher than the training prevalence (0.081941%) and validation prevalence (0.058571%). This temporal distribution shift can affect threshold-level performance.

## Installation and running on Windows

Use Python 3.13 and PowerShell. From the project directory, create and activate a virtual environment, then install the pinned project requirements:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The saved scikit-learn artifact was trained with scikit-learn 1.9.1; `requirements.txt` pins that version for compatible loading. If PowerShell activation is unavailable, use the environment interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Launch the local application from the project directory:

```powershell
streamlit run app.py
```

Or, without activating the environment:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The application expects these saved artifacts, which are separate from the raw dataset:

- `models/random_forest_pipeline.joblib`
- `models/model_selection.json`
- `results/validation_metrics.json`
- `results/final_test_metrics.json`
- `results/model_comparison.csv`
- Saved figures under `results/`

## Batch CSV format

The batch page accepts a CSV with `step`, `type`, and `amount` columns. Additional columns are ignored.

```csv
step,type,amount
400,TRANSFER,1500.00
500,PAYMENT,75.50
```

`step` must be a whole number from 1 through 743, `type` must be CASH_IN, CASH_OUT, DEBIT, PAYMENT, or TRANSFER, and `amount` must be a finite, nonnegative number. Uploads are limited to 200,000 rows. Results include the input features, fraud score, model indication, and threshold, and can be downloaded as CSV.

## Technologies and tests

- Python 3.13
- Streamlit
- pandas and NumPy
- scikit-learn and joblib

Run the existing application tests from the project root:

```powershell
python -m unittest discover -s tests -v
```

## Limitations and responsible interpretation

- PaySim is synthetic mobile-money data, not actual UPI transaction data. The results do not demonstrate performance on UPI payments.
- The dataset is severely imbalanced and has temporal prevalence shift. The test period's fraud prevalence is substantially higher than that of training and validation.
- Fraud recall is low at the approved threshold: 3,230 of 4,010 test fraud-labeled records were missed. Strong precision or ROC-AUC does not remove this limitation.
- The model uses only three input features. It does not inspect account history, recipient identity, UPI protocol events, or real-time bank signals.
- A model score is an indication from this synthetic-data model, not a calibrated probability of real-world UPI fraud or a guarantee that a transaction is safe or fraudulent.
- This is an educational research prototype, not a production banking security system, and it must not be used to authorize or block real payments.

## Project documentation

- [Literature review analysis](docs/literature_review_analysis.md)
- [Dataset selection report](docs/dataset_selection_report.md)
- [Dataset inspection](docs/dataset_inspection.md)
- [Experiment design](docs/experiment_design.md)
- [Model training report](docs/model_training_report.md)
- [Threshold analysis report](docs/threshold_analysis_report.md)
- [Application implementation and test report](docs/application_report.md)
