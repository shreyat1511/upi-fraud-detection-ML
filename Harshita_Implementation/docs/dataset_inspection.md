# PaySim CSV inspection report

## File and schema

- **File:** `data/raw/PS_20174392719_1491204439457_log.csv`
- **Size:** 493,534,783 bytes (470.67 MiB)
- **Rows:** 6,362,620
- **Columns (11):** `step`, `type`, `amount`, `nameOrig`, `oldbalanceOrg`, `newbalanceOrig`, `nameDest`, `oldbalanceDest`, `newbalanceDest`, `isFraud`, `isFlaggedFraud`
- **Exact duplicate rows:** The count below is based on 64-bit row hashes; hash collisions are theoretically possible, so treat this as an extremely close duplicate count rather than a byte-for-byte proof.
- **Duplicate row count:** 0

## Missing values

| Column | Missing |
|---|---:|
| `step` | 0 |
| `type` | 0 |
| `amount` | 0 |
| `nameOrig` | 0 |
| `oldbalanceOrg` | 0 |
| `newbalanceOrig` | 0 |
| `nameDest` | 0 |
| `oldbalanceDest` | 0 |
| `newbalanceDest` | 0 |
| `isFraud` | 0 |
| `isFlaggedFraud` | 0 |

## Labels and class balance

- Legitimate (`isFraud=0`): 6,354,407
- Fraud (`isFraud=1`): 8,213
- Fraud percentage: 0.129082%

## Transaction types

| Type | Count |
|---|---:|
| `CASH_IN` | 1,399,284 |
| `CASH_OUT` | 2,237,500 |
| `DEBIT` | 41,432 |
| `PAYMENT` | 2,151,495 |
| `TRANSFER` | 532,909 |

## Step/time distribution

- `step` range: 1–743 (743 unique values).
- Transactions per step range: 2–51,352.
- First five step counts: 1: 2,708, 2: 1,014, 3: 552, 4: 565, 5: 665
- Last five step counts: 739: 10, 740: 6, 741: 22, 742: 14, 743: 8
- `step` is relative simulation time, not a calendar timestamp.
- Missing integer steps inside the observed range: none

## Identifier-cardinality assessment

- `nameOrig`: 6,353,307 unique non-null values; 9,313 occurrences beyond each identifier’s first occurrence; unique-value fraction 99.85%.
- `nameDest`: 2,722,362 unique non-null values; 3,640,258 occurrences beyond each identifier’s first occurrence; unique-value fraction 42.79%.
- These are high-cardinality entity identifiers and are **not automatically recommended as prediction features**. They can enable memorization or leakage across random splits. Consider them for grouping, entity-history features built using past-only information, or a separately justified experiment with chronological/entity-aware validation.

## Data checks and unexpected values

| Check | Count |
|---|---:|
| nonbinary isFraud | 0 |
| nonbinary isFlaggedFraud | 0 |
| negative amount | 0 |
| nonpositive step | 0 |
| negative balance values | 0 |
| zero amount transactions | 16 |
| `isFlaggedFraud=1` records | 16 |
| both fraud and flagged | 16 |

Fraud labels by transaction type:

| Type | Legitimate | Fraud |
|---|---:|---:|
| `CASH_IN` | 1,399,284 | 0 |
| `CASH_OUT` | 2,233,384 | 4,116 |
| `DEBIT` | 41,432 | 0 |
| `PAYMENT` | 2,151,495 | 0 |
| `TRANSFER` | 528,812 | 4,097 |

First-character identifier counts:

- `nameOrig`: C: 6,362,620
- `nameDest`: C: 4,211,125, M: 2,151,495

Numeric ranges:

| Column | Min | Max |
|---|---:|---:|
| `step` | 1 | 743 |
| `amount` | 0 | 9.24455e+07 |
| `oldbalanceOrg` | 0 | 5.9585e+07 |
| `newbalanceOrig` | 0 | 4.9585e+07 |
| `oldbalanceDest` | 0 | 3.56016e+08 |
| `newbalanceDest` | 0 | 3.56179e+08 |

### Leakage and candidate features

The following four post-transaction balance fields are explicitly excluded from candidate prediction features: `oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, and `newbalanceDest`. In particular, new balances directly describe state after processing, and balance fields can expose simulator mechanics/outcomes. They may be retained only for data-quality/accounting analysis, not as predictors in the planned pre-transaction task.

`isFlaggedFraud` is a rule/flag field and should also be excluded as a predictor when predicting `isFraud`.

## Reproducibility

Run from the project root: `python scripts/inspect_paysim.py [path-to-csv]`. The script reads the source CSV and writes this Markdown report; it does not alter the CSV or train a model.
