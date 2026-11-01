"""Local Streamlit dashboard for the PaySim-based educational prototype."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

from app_core import (
    APP_ROOT, MAX_BATCH_ROWS, TRANSACTION_TYPES,
    InputValidationError, load_model_bundle, predict_transactions,
    read_batch_csv, validate_single_transaction,
)


st.set_page_config(
    page_title="UPI Fraud Detection | Research Prototype",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner="Loading the saved Random Forest pipeline…")
def get_bundle():
    return load_model_bundle()


def style_page():
    st.markdown("""
    <style>
      :root {
        --sage: #B2B39D;
        --queen-blue: #476998;
        --blue-nude: #28518A;
        --navy: #043473;
        --gotham-grey: #8B9091;
        --pale-sage: #D7D6AE;
        --gold: #E4D076;
        --ivory: #F7F6F0;
        --ink: #1D2B3A;
        --line: #E2E4DE;
      }
      html, body, [class*="css"] {
        font-family: "Aptos", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
      }
      .stApp { background: var(--ivory); color: var(--ink); }
      [data-testid="stAppViewContainer"] { background: var(--ivory); }
      .block-container { max-width: 1280px; padding: 2.15rem 2.5rem 2rem; }
      h1, h2, h3 { color: var(--navy); letter-spacing: -0.025em; }
      h2 { margin-top: 1.55rem; font-size: 1.32rem; }
      h3 { font-size: 1.08rem; }
      p, li { color: var(--ink); line-height: 1.62; }
      [data-testid="stCaptionContainer"] p { color: #68727C; font-size: .84rem; }

      /* Restrained institutional wordmark and page banner. */
      .hero { padding: 1.85rem 2.1rem 1.9rem; border-radius: 15px; color: #fff;
        background: var(--navy); border: 1px solid #143F78; border-left: 5px solid var(--gold);
        margin-bottom: 1.35rem; box-shadow: 0 8px 24px rgba(4, 52, 115, .09); }
      .hero-kicker { color: var(--gold); text-transform: uppercase; letter-spacing: .14em;
        font-size: .68rem; font-weight: 700; margin-bottom: .7rem; }
      .hero h1 { color: #fff; margin: 0 0 .42rem; font-size: clamp(1.65rem, 3vw, 2.2rem);
        line-height: 1.17; }
      .hero p { color: #E4EAF1; margin: 0; font-size: .98rem; }
      .subtle { color: #596875; font-size: .93rem; }
      .notice { background: #F0F0E7; border-left: 4px solid var(--sage); padding: .85rem 1rem;
        border-radius: 7px; color: #283342; }
      .result-card { border-radius: 12px; padding: 1.15rem 1.35rem; background: #EDF0EA;
        border: 1px solid #D8DCCF; }

      /* Persistent navigation in navy with clear selected-state contrast. */
      [data-testid="stSidebar"] { background: var(--navy); border-right: 1px solid #143F78; }
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
      [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
      [data-testid="stSidebar"] label { color: #F5F6F4 !important; }
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 { letter-spacing: -.02em; }
      [data-testid="stSidebar"] [data-testid="stRadio"] label { padding: .42rem .52rem;
        border-radius: 7px; }
      [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: rgba(255,255,255,.08); }
      [data-testid="stSidebar"] [data-testid="stRadioOption"] { border-radius: 8px; }
      [data-testid="stSidebar"] [data-testid="stRadioOption"] input[type="radio"] {
        accent-color: #B2B39D !important; }
      [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input[type="radio"]:checked) {
        background: #B2B39D !important; color: #043473 !important;
        outline: 1px solid #B2B39D; }
      [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input[type="radio"]:checked) > div {
        background: #B2B39D !important; color: #043473 !important; }
      [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input[type="radio"]:checked) *,
      [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input[type="radio"]:checked) p {
        color: #043473 !important; }
      /* Streamlit draws its radio mark with styled divs around a checked native input. */
      [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input[type="radio"]:checked) > div > div:first-child,
      [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input[type="radio"]:checked) > label > div > div:first-child {
        border-color: #B2B39D !important; background-color: #B2B39D !important; }
      [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input[type="radio"]:checked) > div > div:first-child > div,
      [data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input[type="radio"]:checked) > label > div > div:first-child > div {
        background-color: #B2B39D !important; border-color: #B2B39D !important; }
      [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.22); }

      /* Metric tiles and forms use a consistent, quiet card treatment. */
      div[data-testid="stMetric"] { background: #fff; border: 1px solid var(--line);
        border-radius: 11px; padding: .95rem 1rem; min-height: 102px;
        box-shadow: 0 3px 12px rgba(31, 45, 61, .035); }
      div[data-testid="stMetricLabel"] p { color: #68727C; font-size: .79rem; font-weight: 600; }
      div[data-testid="stMetricValue"] { color: var(--navy); font-size: 1.55rem; font-weight: 700; }
      [data-testid="stForm"] { background: #fff; border: 1px solid var(--line);
        border-radius: 13px; padding: 1.1rem 1.15rem .55rem; }
      [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
      [data-testid="stSelectbox"] [role="combobox"] { border-radius: 8px; }
      [data-testid="stTextInput"] input:focus, [data-testid="stNumberInput"] input:focus {
        border-color: var(--queen-blue); box-shadow: 0 0 0 1px var(--queen-blue); }
      .stButton > button, [data-testid="stFormSubmitButton"] button,
      [data-testid="stDownloadButton"] button { border-radius: 8px; font-weight: 650;
        min-height: 2.65rem; transition: border-color .15s ease, background .15s ease; }
      .stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"],
      [data-testid="stDownloadButton"] button[kind="primary"] {
        background: var(--queen-blue) !important; border-color: var(--queen-blue) !important;
        color: #fff !important; box-shadow: 0 2px 5px rgba(4, 52, 115, .13); }
      /* Streamlit 1.66 emits form submits with kind=primaryFormSubmit. */
      [data-testid="stFormSubmitButton"] [data-testid="stBaseButton-primaryFormSubmit"] {
        background: #B2B39D !important; border-color: #B2B39D !important; color: #043473 !important;
        box-shadow: 0 2px 5px rgba(4, 52, 115, .13); }
      [data-testid="stFormSubmitButton"] [data-testid="stBaseButton-primaryFormSubmit"] * {
        color: #043473 !important; }
      .stButton > button[kind="primary"]:hover,
      [data-testid="stFormSubmitButton"] button[kind="primary"]:hover,
      [data-testid="stDownloadButton"] button[kind="primary"]:hover {
        background: var(--navy) !important; border-color: var(--navy) !important;
        color: #fff !important; box-shadow: 0 3px 8px rgba(4, 52, 115, .2); }
      [data-testid="stFormSubmitButton"] [data-testid="stBaseButton-primaryFormSubmit"]:hover {
        background: #D7D6AE !important; border-color: #D7D6AE !important; color: #043473 !important;
        box-shadow: 0 3px 8px rgba(4, 52, 115, .2); }
      [data-testid="stFormSubmitButton"] [data-testid="stBaseButton-primaryFormSubmit"]:hover * {
        color: #043473 !important; }

      /* Native alerts, data tables, and plotted images remain legible and calm. */
      [data-testid="stAlert"] { border-radius: 9px; border-width: 1px; }
      [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 10px;
        overflow: hidden; background: #fff; }
      [data-testid="stImage"] img { border: 1px solid var(--line); border-radius: 10px;
        background: #fff; padding: .3rem; }
      [data-testid="stExpander"] { border: 1px solid var(--line); border-radius: 9px; background: #fff; }
      a { color: var(--blue-nude); }
      a:hover { color: var(--navy); }
      .app-footer { margin-top: 2.1rem; padding: 1.05rem .25rem .1rem;
        border-top: 1px solid #D7D9D2; display: flex; flex-wrap: wrap;
        align-items: center; justify-content: space-between; gap: .45rem 1rem; }
      .app-footer .author { color: var(--navy); font-weight: 700; font-size: .91rem; }
      .app-footer .meta { color: #52606D; font-size: .82rem; }
      @media (max-width: 720px) {
        .block-container { padding: 1.25rem 1rem 1.5rem; }
        .hero { padding: 1.35rem 1.3rem; }
        div[data-testid="stMetric"] { padding: .75rem; min-height: 88px; }
      }
    </style>
    """, unsafe_allow_html=True)


def hero(title: str, subtitle: str):
    st.markdown(f'<div class="hero"><div class="hero-kicker">Financial analytics · research prototype</div><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def format_pct(value):
    return f"{float(value):.2%}"


def show_header_note():
    st.info("Educational research prototype using **synthetic PaySim mobile-money data** as a proxy. It is not trained or validated on actual UPI transactions.")


def page_home(bundle):
    hero("UPI Transaction Fraud Detection", "Machine learning research prototype · PaySim proxy data")
    show_header_note()
    st.markdown("Explore a saved Random Forest model that scores transaction-like inputs using transaction step, type and amount. The interface reuses the fitted preprocessing and model pipeline; it does not train a model.")
    cols = st.columns(4)
    test = bundle.test_metrics["test_metrics"]
    cols[0].metric("Selected model", "Random Forest")
    cols[1].metric("Approved threshold", f"{bundle.threshold:.9f}")
    cols[2].metric("Test precision", format_pct(test["precision"]))
    cols[3].metric("Test recall", format_pct(test["recall"]))
    st.markdown("### Frozen test evaluation")
    metric_cols = st.columns(5)
    metric_cols[0].metric("F1-score", f"{test['f1']:.4f}")
    metric_cols[1].metric("PR-AUC (Average Precision)", f"{test['pr_auc_average_precision']:.4f}")
    metric_cols[2].metric("ROC-AUC", f"{test['roc_auc']:.4f}")
    metric_cols[3].metric("Fraud detected", f"{test['true_positives']:,} / {test['fraud_count']:,}")
    metric_cols[4].metric("Fraud missed", f"{test['false_negatives']:,}")
    st.markdown('<div class="notice"><b>Interpretation:</b> At the frozen test threshold, the model missed 3,230 of 4,010 fraud-labeled records. A prediction is an indication from this model, not proof or a guarantee about a payment.</div>', unsafe_allow_html=True)
    st.caption("The test results are a frozen evaluation from the selected threshold. The application does not change or recompute them.")


def page_single(bundle):
    hero("Single Transaction Analysis", "Score one transaction-like record with the saved model")
    show_header_note()
    with st.form("single_transaction_form"):
        col1, col2, col3 = st.columns(3)
        step = col1.number_input("Simulation step", min_value=1, max_value=743, value=400, step=1, help="PaySim relative simulation step; not a calendar date.")
        tx_type = col2.selectbox("Transaction type", TRANSACTION_TYPES)
        amount = col3.number_input("Transaction amount", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
        submitted = st.form_submit_button("Predict", type="primary", use_container_width=True)
    if submitted:
        try:
            normalized = validate_single_transaction(step, tx_type, amount)
            features = pd.DataFrame([normalized], columns=["step", "type", "amount"])
            result = predict_transactions(bundle, features).iloc[0]
        except InputValidationError as exc:
            st.error(str(exc))
            return
        is_flagged = result["prediction"] == "Fraud indication"
        if is_flagged:
            st.error(f"Fraud indication · model score {result['fraud_probability_percent']:.2f}%")
        else:
            st.success(f"No fraud indication at the approved threshold · model score {result['fraud_probability_percent']:.2f}%")
        c1, c2, c3 = st.columns(3)
        c1.metric("Model score", f"{result['fraud_probability_percent']:.2f}%")
        c2.metric("Threshold", f"{bundle.threshold:.9f}")
        c3.metric("Prediction", result["prediction"])
        st.caption("The score is the saved model’s output, not a calibrated real-world UPI fraud probability. It is an indication, not a guarantee.")


def page_performance(bundle):
    hero("Model Performance", "Reported experiments from the frozen PaySim evaluation")
    show_header_note()
    comparison = bundle.comparison
    display_columns = ["model", "threshold", "precision", "recall", "f1", "pr_auc_average_precision", "roc_auc", "accuracy", "training_time_seconds"]
    rename = {
        "model": "Model", "threshold": "Validation threshold", "precision": "Precision",
        "recall": "Recall", "f1": "F1", "pr_auc_average_precision": "PR-AUC / AP",
        "roc_auc": "ROC-AUC", "accuracy": "Accuracy (secondary)", "training_time_seconds": "Fit time (s)",
    }
    st.markdown("### Validation model comparison")
    st.dataframe(comparison.loc[:, display_columns].rename(columns=rename).style.format({
        "Validation threshold": "{:.6f}", "Precision": "{:.4f}", "Recall": "{:.4f}", "F1": "{:.4f}",
        "PR-AUC / AP": "{:.4f}", "ROC-AUC": "{:.4f}", "Accuracy (secondary)": "{:.4f}", "Fit time (s)": "{:.2f}",
    }), use_container_width=True, hide_index=True)
    test = bundle.test_metrics["test_metrics"]
    st.markdown("### Selected Random Forest · frozen test metrics")
    cols = st.columns(5)
    cols[0].metric("Precision", f"{test['precision']:.4f}")
    cols[1].metric("Recall", f"{test['recall']:.4f}")
    cols[2].metric("F1-score", f"{test['f1']:.4f}")
    cols[3].metric("PR-AUC / AP", f"{test['pr_auc_average_precision']:.4f}")
    cols[4].metric("ROC-AUC", f"{test['roc_auc']:.4f}")
    st.error("At the frozen threshold, the model missed 3,230 of 4,010 fraud cases in the test set.")
    st.markdown("### Saved evaluation figures")
    image_map = [
        ("Confusion matrix · frozen test", "results/confusion_matrix.png"),
        ("Precision–recall curve · validation", "results/precision_recall_curve.png"),
        ("ROC curve · validation", "results/roc_curve.png"),
        ("Feature importance / coefficient magnitudes", "results/feature_importance.png"),
    ]
    for caption, relative_path in image_map:
        image_path = APP_ROOT / relative_path
        if image_path.is_file():
            st.image(str(image_path), caption=caption, use_container_width=True)
        else:
            st.warning(f"Saved figure unavailable: {caption}")
    with st.expander("Metric definitions"):
        st.markdown("- **Precision:** Among transactions flagged, how many were fraud-labeled. Lower precision means more false alarms.\n- **Recall:** Among fraud-labeled transactions, how many the model found. Lower recall means more missed fraud.\n- **F1-score:** A single summary that balances precision and recall at a chosen threshold.\n- **PR-AUC / Average Precision:** How well the model ranks fraud above legitimate transactions across thresholds; especially useful when fraud is rare.")
    st.caption("These results describe synthetic PaySim transactions. They do not demonstrate performance on actual UPI traffic.")


def page_batch(bundle):
    hero("Batch Analysis", "Score a CSV locally and download the annotated results")
    show_header_note()
    st.markdown("Upload a CSV with columns `step`, `type`, and `amount`. Extra columns are ignored. Up to 200,000 rows are accepted per upload. The file is processed by this local app and is not sent to an external prediction service.")
    sample = pd.DataFrame({"step": [400, 500], "type": ["TRANSFER", "PAYMENT"], "amount": [1500.0, 75.5]})
    st.download_button("Download sample CSV", sample.to_csv(index=False).encode("utf-8"), "sample_transactions.csv", "text/csv")
    uploaded = st.file_uploader("Choose transaction CSV", type=["csv"], accept_multiple_files=False)
    if uploaded is None:
        return
    try:
        features = read_batch_csv(BytesIO(uploaded.getvalue()))
        predictions = predict_transactions(bundle, features)
        result = pd.concat([features, predictions], axis=1)
    except (InputValidationError, pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
        st.error(f"Could not analyze this file: {exc}")
        return
    fraud_count = int((result["prediction"] == "Fraud indication").sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows scored", f"{len(result):,}")
    c2.metric("Fraud indications", f"{fraud_count:,}")
    c3.metric("Approved threshold", f"{bundle.threshold:.9f}")
    st.dataframe(result, use_container_width=True, hide_index=True)
    st.download_button("Download prediction results", result.to_csv(index=False).encode("utf-8"), "fraud_predictions.csv", "text/csv", type="primary")
    st.caption("Predictions are model indications only. They are not confirmations about real payments or UPI transactions.")


def page_about(bundle):
    hero("About & Limitations", "What this prototype can and cannot tell you")
    st.markdown("""
    ### Dataset and provenance

    This project uses **PaySim**, a synthetic mobile-money transaction simulator. The public Kaggle distribution is [Synthetic Financial Datasets For Fraud Detection](https://www.kaggle.com/datasets/ealaxi/paysim1); the simulator is described in the [PaySim research paper](https://www.msc-les.org/proceedings/emss/2016/EMSS2016_249.pdf). The records are generated by simulation based on aggregated mobile-money activity. **They are not actual UPI, NPCI, Indian bank, or production payment records.**

    ### Experiment design

    The chronological split uses PaySim step ranges: train 1–322, validation 323–377, and test 378–743. The selected input features are `step`, `type`, and `amount`. The model excludes `nameOrig`, `nameDest`, all four balance fields, and `isFlaggedFraud`. The fitted preprocessing and Random Forest pipeline are reused; the app never retrains it.

    ### Class imbalance and temporal shift

    Fraud is rare: the training rate is 0.081941%, validation rate is 0.058571%, and test rate is 0.419568%. The later test period has a substantially higher fraud prevalence than earlier periods. Threshold-level precision and recall can therefore shift over time. The frozen test evaluation missed 3,230 of 4,010 fraud-labeled records at the approved threshold.

    ### Limitations

    This is an educational research prototype, not a production banking security system. It has not been validated on real UPI transaction data, does not verify payment identities or recipient details, and does not guarantee that a transaction is safe or fraudulent. Model scores are not calibrated probabilities of real-world UPI fraud. Use it to explore the saved model and its evaluation, not to authorize or block real payments.
    """)
    st.caption(f"Approved educational threshold: {bundle.threshold:.9f}. It was selected using validation data.")


def main():
    style_page()
    with st.sidebar:
        st.markdown("## 🛡️ UPI Fraud Lab")
        st.caption("Local educational prototype")
        page = st.radio("Navigate", ["Home / Overview", "Single Transaction", "Model Performance", "Batch Analysis", "About / Limitations"], label_visibility="collapsed")
        st.divider()
        st.caption("PaySim proxy data · Not actual UPI")
    try:
        bundle = get_bundle()
    except Exception as exc:
        st.error("The saved model or evaluation artifacts could not be loaded. Confirm the project files are present and install the requirements listed in `requirements.txt`.")
        st.caption(f"Diagnostic category: {type(exc).__name__}. No local artifact path is shown here.")
        st.stop()

    page_functions = {
        "Home / Overview": page_home,
        "Single Transaction": page_single,
        "Model Performance": page_performance,
        "Batch Analysis": page_batch,
        "About / Limitations": page_about,
    }
    page_functions[page](bundle)
    st.markdown("""
    <footer class="app-footer">
      <span class="author">Made by Shreya Thapa and Harshita Bagwe</span>
      <span class="meta">Machine Learning Research Project · 2026</span>
      <span class="meta">Research prototype · Predictions are indicators, not guarantees · Data is processed locally</span>
    </footer>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
