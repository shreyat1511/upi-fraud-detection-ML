# Local Streamlit application implementation report

## Implementation summary

The local Streamlit dashboard is a presentation layer over the completed PaySim research experiment. It reuses the saved fitted Random Forest and its preprocessing pipeline; it contains no training or refitting path. The user interface consistently describes PaySim as **synthetic mobile-money proxy data, not real UPI data**.

### Artifact discovery and reuse

The selected saved Random Forest pipeline is `models/random_forest_pipeline.joblib`. Its model metadata is `models/model_selection.json`. The application verifies that metadata identifies Random Forest and the approved threshold (`0.925415475`, within floating point tolerance), then checks the frozen evaluation files `results/validation_metrics.json`, `results/final_test_metrics.json`, and `results/model_comparison.csv` before exposing the dashboard. The final saved model alias also exists at `models/final_model_pipeline.joblib`; the app loads the specifically identified Random Forest pipeline rather than guessing from directory contents.

The preprocessor inside the joblib pipeline is reused for all inputs. The app supplies only `step`, `type`, and `amount`; it does not use `nameOrig`, `nameDest`, balances, `isFlaggedFraud`, or a supplied target column. The classification threshold is the approved validation-selected value. Existing frozen test metrics and plots are displayed from saved experiment artifacts without recomputation or modification.

## User-facing sections

- **Home / Overview:** Project framing, selected model, approved threshold, actual frozen test metrics, and the 3,230 missed test fraud cases.
- **Single Transaction:** Validates step 1–743, one of the five known transaction types, and finite nonnegative amount; predicts only after the user presses Predict. It describes the score as an indication, not a guarantee.
- **Model Performance:** Shows the saved Logistic Regression, Decision Tree, and Random Forest validation comparison, selected-model frozen test metrics, confusion matrix, validation PR/ROC curves, feature-importance graphic, and metric definitions.
- **Batch Analysis:** Parses CSV locally, requires `step`, `type`, and `amount`, validates every row, ignores extra columns, limits uploads to 200,000 records, displays results, and provides a downloadable annotated CSV. Invalid files produce actionable messages.
- **About / Limitations:** Describes PaySim provenance, the chronological split, severe class imbalance and temporal prevalence shift, excluded features, and the prototype’s non-production status.

The application code contains no external prediction endpoint. Uploaded transaction rows are handled in the local Streamlit process and are not sent to an external service by this code.

## Validation and checks performed

Seven automated checks were run with `python -m unittest discover -s tests -v`; all passed:

1. Load the saved Random Forest pipeline and verify its saved metadata and threshold.
2. Run a valid single-transaction prediction and check that the returned score is within 0–100% and carries threshold `0.925415475`.
3. Reject invalid single transaction step, type, and amount values.
4. Parse a CSV byte stream, normalize transaction type, validate its feature columns, and run batch predictions.
5. Reject invalid batch headers, values, and malformed CSV input.
6. Parse application and core source ASTs to confirm there is no `.fit()` call in application startup/prediction code.
7. Compile `app.py`, `app_core.py`, and the test module successfully.

**Model loading succeeded**, including actual inference for a valid single input and a two-row CSV batch through the saved pipeline. The frozen test results were not edited, and no training or model fitting occurred.

## Streamlit runtime status

The base Python environment did not have Streamlit installed. A project-local `.venv` was started, and the dependency download was authorized, but installing `requirements.txt` failed with `No space left on device` while installing Streamlit and its dependencies (the workspace drive had about 105 MB free afterward). The Streamlit process and browser-rendered interface could not be smoke-tested here. The UI source compiles, and its prediction, validation, and artifact-loading logic passed the tests above. Install the declared dependencies in an environment with sufficient disk space, then launch with:

```powershell
streamlit run app.py
```

or, after creating/activating `.venv`:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

No cloud deployment was performed. No screenshots or runtime results are claimed.

The incomplete `.venv` is ignored by `.gitignore` and was left in place after a cleanup command was rejected by the automatic action review. It is not a verified runnable environment; recreate it before installation if needed.

## Files created

- `app.py` — Streamlit pages and dashboard layout.
- `app_core.py` — artifact loading, input validation, and saved-pipeline inference helpers.
- `requirements.txt` — runtime dependencies, with scikit-learn pinned to the training artifact version.
- `.gitignore` — ignores local environments, caches, raw local dataset files, and optional processed partitions.
- `tests/test_application_core.py` — focused checks for artifact loading, predictions, validation, threshold use, and no fitting.
- `README.md` — project overview, setup, run instructions, reported metrics, and limitations.

No research report, training script, saved model, or frozen evaluation result was overwritten. The app does not change the approved saved threshold.
