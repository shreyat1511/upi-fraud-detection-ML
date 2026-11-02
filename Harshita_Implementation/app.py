"""Local Streamlit dashboard for the PaySim-based educational prototype."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

import numpy as np
import pandas as pd
import streamlit as st

from app_core import (
    APP_ROOT, MAX_BATCH_ROWS, TRANSACTION_TYPES,
    InputValidationError, load_model_bundle, predict_transactions,
    read_batch_csv, validate_single_transaction,
)
from ui_components import (
    brand_html, batch_by_type, batch_hist, callout_html, cards_html, comparison_table_html,
    confusion_html, curve_chart, feed_html, fmt_inr, hero_html, icon, info_cards_html,
    model_bars, score_curve, sequence_html, session_chart, simulation_html,
)
from ui_theme import inject_theme

st.set_page_config(
    page_title="UPI Fraud Lab | Research Prototype",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="auto",
)

NAV = ["Overview", "Payment simulator", "Model performance", "Batch check", "About and limits"]

# One-click scenarios for the simulator: (button label, type, amount, step)
PRESETS = [
    ("Café payment", "PAYMENT", 250.0, 400),
    ("Monthly rent", "TRANSFER", 50000.0, 400),
    ("Cash withdrawal", "CASH_OUT", 5000.0, 400),
    ("Large cash-out", "CASH_OUT", 1000000.0, 400),
    ("Very large transfer", "TRANSFER", 10000000.0, 150),
]


@st.cache_resource(show_spinner="Loading the saved Random Forest pipeline…")
def get_bundle():
    return load_model_bundle()


_NEW_STREAMLIT = hasattr(st, "iframe")


def stretch() -> dict:
    """Full-width kwargs that work on both current and older Streamlit releases."""
    return {"width": "stretch"} if _NEW_STREAMLIT else {"use_container_width": True}


def show_html(markup: str, height: int) -> None:
    """Embed a self-contained HTML page (used for the payment animation)."""
    if _NEW_STREAMLIT:
        st.iframe(markup, height="content")
    else:  # pragma: no cover - older Streamlit
        import streamlit.components.v1 as components
        components.html(markup, height=height, scrolling=True)


def pct(value) -> str:
    return f"{float(value):.1%}"


def go_to(page: str):
    st.session_state["nav"] = page


# ------------------------------------------------------------------ pages
def page_home(bundle):
    t = bundle.test_metrics["test_metrics"]
    missed_share = t["false_negatives"] / t["fraud_count"]
    st.markdown(hero_html(
        "See how a fraud model checks a payment, and where it falls short",
        "A Random Forest trained on synthetic PaySim mobile-money data, with a live payment simulator, "
        "frozen test results and batch scoring.",
        stat={
            "big": f"{missed_share:.0%}",
            "caption": f"of fraud-labelled records in the test period were missed at the approved threshold "
                       f"({t['false_negatives']:,} of {t['fraud_count']:,}).",
            "pct": (1 - missed_share) * 100,
            "left": f"{t['true_positives']:,} caught",
            "right": f"{t['false_negatives']:,} missed",
        },
    ), unsafe_allow_html=True)
    st.button("Open the payment simulator", type="primary", on_click=go_to, args=("Payment simulator",))

    st.markdown("## How a payment is checked")
    st.markdown(sequence_html([
        ("Enter the payment", "Three inputs only: simulation step, transaction type and amount."),
        ("Prepare the features", "The amount is log-scaled and the type is one-hot encoded by the saved pipeline."),
        ("Score with 50 trees", "Each tree votes. The average becomes the model score from 0 to 100%."),
        ("Compare with the threshold",
         f"A score of {bundle.threshold:.1%} or higher is flagged. The threshold was picked on validation data."),
    ]), unsafe_allow_html=True)

    st.markdown("## Frozen test results")
    st.markdown(cards_html([
        {"label": "Precision", "value": pct(t["precision"]), "note": "Of flagged payments, share that were fraud", "tone": ""},
        {"label": "Recall", "value": pct(t["recall"]), "note": "Of fraud records, share the model caught", "tone": "yellow"},
        {"label": "F1-score", "value": f"{t['f1']:.3f}", "note": "Balance of precision and recall", "tone": "ivory"},
        {"label": "ROC-AUC", "value": f"{t['roc_auc']:.3f}", "note": "How well scores rank fraud above legitimate", "tone": ""},
    ]), unsafe_allow_html=True)
    st.markdown(callout_html(
        f"<b>Read this before trusting any score.</b> Precision is high because the model flags rarely. "
        f"Recall is low: it missed {t['false_negatives']:,} of {t['fraud_count']:,} fraud-labelled records. "
        "A prediction is an indication from this model, not proof or a guarantee about a payment.", "warn"),
        unsafe_allow_html=True)
    st.caption("These figures come from the frozen test evaluation. The app does not recompute or change them.")


def apply_preset(tx_type: str, amount: float, step: int):
    st.session_state.update(sim_type=tx_type, sim_amount=amount, sim_step=step, sim_run=True)


def page_simulator(bundle):
    threshold_pct = bundle.threshold * 100
    trees = int(getattr(bundle.pipeline.named_steps["model"], "n_estimators", 0))
    st.session_state.setdefault("sim_step", 400)
    st.session_state.setdefault("sim_type", "PAYMENT")
    st.session_state.setdefault("sim_amount", 1000.0)
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("last", None)

    st.markdown(hero_html(
        "Payment simulator",
        "Send a payment and watch it pass through the same saved model and threshold the rest of this app uses.",
    ), unsafe_allow_html=True)

    st.markdown("**Try a scenario**")
    cols = st.columns(len(PRESETS))
    for col, (label, tx_type, amount, step) in zip(cols, PRESETS):
        col.button(label, key=f"preset_{label}", **stretch(),
                   on_click=apply_preset, args=(tx_type, amount, step),
                   help=f"{tx_type} of ₹{fmt_inr(amount)} at step {step}")

    with st.form("single_transaction_form"):
        c1, c2, c3 = st.columns([1, 1, 1.3])
        c1.selectbox("Transaction type", TRANSACTION_TYPES, key="sim_type")
        c2.number_input("Simulation step", min_value=1, max_value=743, step=1, key="sim_step",
                        help="PaySim relative simulation step (1 to 743). It is not a calendar date.")
        c3.number_input("Amount (₹)", min_value=0.0, step=100.0, format="%.2f", key="sim_amount",
                        help="Amount in PaySim units. The dataset does not define a real currency.")
        submitted = st.form_submit_button("Send payment", type="primary", **stretch())

    run = submitted or st.session_state.pop("sim_run", False)
    if run:
        try:
            tx = validate_single_transaction(st.session_state.sim_step, st.session_state.sim_type, st.session_state.sim_amount)
            result = predict_transactions(bundle, pd.DataFrame([tx], columns=["step", "type", "amount"])).iloc[0]
        except InputValidationError as exc:
            st.error(str(exc))
            st.session_state.last = None
        else:
            flagged = result["prediction"] == "Fraud indication"
            st.session_state.last = {**tx, "score": float(result["fraud_probability_percent"]), "flagged": flagged}
            st.session_state.history.insert(0, {
                "time": datetime.now().strftime("%H:%M:%S"), "type": tx["type"], "step": tx["step"],
                "amount": tx["amount"], "score": st.session_state.last["score"], "flagged": flagged,
            })
            del st.session_state.history[50:]

    last = st.session_state.last
    show_html(simulation_html(last, threshold_pct, trees), height=575)

    if last:
        verdict = "Fraud indication" if last["flagged"] else "No fraud indication"
        st.markdown(cards_html([
            {"label": "Model score", "value": f"{last['score']:.2f}%", "tone": "alert" if last["flagged"] else "mid",
             "note": "Not a calibrated probability of real-world fraud"},
            {"label": "Flag threshold", "value": f"{threshold_pct:.2f}%", "tone": "ivory",
             "note": "Chosen on validation data"},
            {"label": "Result", "value": verdict, "tone": "alert" if last["flagged"] else "",
             "note": f"{last['type']} · ₹{fmt_inr(last['amount'])} · step {last['step']}"},
        ], cols=3), unsafe_allow_html=True)

        st.markdown("### Why this score")
        st.caption(f"Score for {last['type']} payments at step {last['step']} as the amount changes. "
                   "Only the amount moves; the dot marks your payment.")
        curve = score_curve(bundle, last["type"], last["step"])
        st.altair_chart(curve_chart(curve, last["amount"], last["score"], threshold_pct, last["type"]),
                        **stretch())

    st.markdown("### Payments checked this session")
    st.markdown(feed_html(st.session_state.history[:8], threshold_pct), unsafe_allow_html=True)
    if st.session_state.history:
        if len(st.session_state.history) > 1:
            with st.expander("Score history chart"):
                st.altair_chart(session_chart(st.session_state.history, threshold_pct), **stretch())
        a, b, _ = st.columns([1, 1, 3])
        hist_df = pd.DataFrame(st.session_state.history)
        a.download_button("Download history", hist_df.to_csv(index=False).encode("utf-8"),
                          "simulator_history.csv", "text/csv", **stretch())
        if b.button("Clear history", **stretch()):
            st.session_state.history = []
            st.session_state.last = None
            st.rerun()
    st.caption("Simulation only. Nothing is sent or blocked. The model sees step, type and amount, never names, "
               "balances or recipients, and the app cannot stop a real payment.")


def page_performance(bundle):
    st.markdown(hero_html("Model performance", "Reported experiments from the frozen PaySim evaluation."),
                unsafe_allow_html=True)
    t = bundle.test_metrics["test_metrics"]
    tab1, tab2, tab3 = st.tabs(["Model comparison", "Selected model on test data", "Saved figures"])

    with tab1:
        st.markdown("### Three models on validation data")
        st.markdown(comparison_table_html(bundle.comparison, bundle.metadata["selected_model"]), unsafe_allow_html=True)
        st.caption("Green bold marks the best value in each column. Random Forest was chosen by validation PR-AUC, "
                   "then F1, then recall.")
        st.altair_chart(model_bars(bundle.comparison), **stretch())
        st.markdown(callout_html(
            "<b>Why PR-AUC and not accuracy?</b> Legitimate payments dominate the data, so a model that never "
            "flags anything still scores about 99.9% accuracy. PR-AUC shows how well fraud is ranked above legitimate payments.",
            "info"), unsafe_allow_html=True)

    with tab2:
        st.markdown(cards_html([
            {"label": "Precision", "value": f"{t['precision']:.4f}", "tone": ""},
            {"label": "Recall", "value": f"{t['recall']:.4f}", "tone": "yellow"},
            {"label": "F1-score", "value": f"{t['f1']:.4f}", "tone": "ivory"},
            {"label": "PR-AUC", "value": f"{t['pr_auc_average_precision']:.4f}", "tone": ""},
            {"label": "ROC-AUC", "value": f"{t['roc_auc']:.4f}", "tone": ""},
        ], cols=5), unsafe_allow_html=True)
        left, right = st.columns([1.15, 1])
        with left:
            st.markdown("### Confusion matrix")
            st.markdown(confusion_html(t["true_negatives"], t["false_positives"], t["false_negatives"], t["true_positives"]),
                        unsafe_allow_html=True)
        with right:
            st.markdown("### What it means")
            st.markdown(callout_html(
                f"At the approved threshold the model caught <b>{t['true_positives']:,}</b> of "
                f"<b>{t['fraud_count']:,}</b> fraud-labelled records and missed <b>{t['false_negatives']:,}</b>. "
                f"It wrongly flagged only {t['false_positives']:,} of {t['legitimate_count']:,} legitimate records.", "alert"),
                unsafe_allow_html=True)
            st.markdown(callout_html(
                f"Test-period fraud prevalence ({t['fraud_prevalence']:.2%}) is higher than in training and validation, "
                "so threshold-level results shift over time.", "info"), unsafe_allow_html=True)
        with st.expander("Metric definitions"):
            st.markdown(
                "- **Precision:** Among payments flagged, how many were fraud-labelled. Low precision means more false alarms.\n"
                "- **Recall:** Among fraud-labelled payments, how many the model found. Low recall means more missed fraud.\n"
                "- **F1-score:** One number balancing precision and recall at a chosen threshold.\n"
                "- **PR-AUC (Average Precision):** How well fraud ranks above legitimate payments across thresholds.\n"
                "- **ROC-AUC:** Ranking quality across thresholds; it looks flattering when fraud is rare."
            )

    with tab3:
        image_map = [
            ("Confusion matrix, frozen test", "results/confusion_matrix.png"),
            ("Precision-recall curve, validation", "results/precision_recall_curve.png"),
            ("ROC curve, validation", "results/roc_curve.png"),
            ("Feature importance", "results/feature_importance.png"),
        ]
        cols = st.columns(2)
        for i, (caption, rel) in enumerate(image_map):
            path = APP_ROOT / rel
            with cols[i % 2]:
                if path.is_file():
                    st.image(str(path), caption=caption, **stretch())
                else:
                    st.warning(f"Saved figure unavailable: {caption}")
    st.caption("These results describe synthetic PaySim transactions. They do not show performance on real UPI traffic.")


def demo_batch(n: int = 300, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "step": rng.integers(1, 744, n),
        "type": rng.choice(TRANSACTION_TYPES, size=n, p=[.2, .25, .05, .35, .15]),
        "amount": np.round(np.exp(rng.uniform(np.log(20), np.log(3e6), n)), 2),
    })


def page_batch(bundle):
    threshold_pct = bundle.threshold * 100
    st.markdown(hero_html("Batch check", "Score a whole CSV locally and download the annotated results."),
                unsafe_allow_html=True)
    st.markdown(cards_html([
        {"label": "Columns needed", "value": "3", "note": "step, type, amount. Extra columns are ignored.", "tone": ""},
        {"label": "Row limit", "value": f"{MAX_BATCH_ROWS:,}", "note": "Per upload", "tone": "ivory"},
        {"label": "Where it runs", "value": "Locally", "note": "Rows are never sent to an outside service.", "tone": "yellow"},
    ], cols=3), unsafe_allow_html=True)

    sample = pd.DataFrame({"step": [400, 500], "type": ["TRANSFER", "PAYMENT"], "amount": [1500.0, 75.5]})
    c1, c2, _ = st.columns([1, 1.3, 2])
    c1.download_button("Download sample CSV", sample.to_csv(index=False).encode("utf-8"), "sample_transactions.csv",
                       "text/csv", **stretch())
    if c2.button("Try 300 generated payments", **stretch()):
        st.session_state["demo_batch"] = demo_batch()
    uploaded = st.file_uploader("Drop a transaction CSV here", type=["csv"], accept_multiple_files=False)

    try:
        if uploaded is not None:
            st.session_state.pop("demo_batch", None)
            features = read_batch_csv(BytesIO(uploaded.getvalue()))
            source = uploaded.name
        elif "demo_batch" in st.session_state:
            from app_core import validate_batch_frame
            features = validate_batch_frame(st.session_state["demo_batch"])
            source = "300 generated payments (random, for demonstration)"
        else:
            st.markdown(callout_html("Upload a CSV or try the generated payments to see scores, charts and a downloadable result.", "info"),
                        unsafe_allow_html=True)
            return
        predictions = predict_transactions(bundle, features)
        result = pd.concat([features, predictions], axis=1)
    except (InputValidationError, pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
        st.error(f"Could not analyze this file: {exc}")
        return

    flagged = int((result["prediction"] == "Fraud indication").sum())
    st.markdown(f"### Results for {source}")
    st.markdown(cards_html([
        {"label": "Rows scored", "value": f"{len(result):,}", "tone": ""},
        {"label": "Fraud indications", "value": f"{flagged:,}", "tone": "alert" if flagged else "mid",
         "note": f"{flagged / len(result):.1%} of rows"},
        {"label": "Highest score", "value": f"{result['fraud_probability_percent'].max():.1f}%", "tone": "ivory"},
        {"label": "Flag threshold", "value": f"{threshold_pct:.2f}%", "tone": "yellow"},
    ]), unsafe_allow_html=True)

    a, b = st.columns(2)
    with a:
        st.markdown("**Score distribution**")
        st.altair_chart(batch_hist(result, threshold_pct), **stretch())
    with b:
        st.markdown("**Outcome by transaction type**")
        st.altair_chart(batch_by_type(result), **stretch())

    view = st.segmented_control("Show", ["All rows", "Flagged only"], default="All rows") or "All rows"
    shown = result if view == "All rows" else result[result["prediction"] == "Fraud indication"]
    st.dataframe(
        shown, **stretch(), hide_index=True,
        column_config={
            "fraud_probability_percent": st.column_config.ProgressColumn("Model score", min_value=0, max_value=100, format="%.1f%%"),
            "amount": st.column_config.NumberColumn("Amount", format="%.2f"),
            "threshold": None,
            "prediction": "Result", "step": "Step", "type": "Type",
        },
    )
    st.download_button("Download prediction results", result.to_csv(index=False).encode("utf-8"),
                       "fraud_predictions.csv", "text/csv", type="primary")
    st.caption("Predictions are model indications only. They are not confirmations about real payments.")


def page_about(bundle):
    st.markdown(hero_html("About and limits", "What this prototype can and cannot tell you."), unsafe_allow_html=True)
    st.markdown(info_cards_html([
        {"icon": icon("flask"), "title": "Synthetic data",
         "body": "PaySim simulates mobile-money activity. It is not UPI, NPCI, bank or production payment data.", "tone": "ivory"},
        {"icon": icon("clock"), "title": "Chronological split",
         "body": "Train on steps 1 to 322, validate on 323 to 377, test on 378 to 743. Preprocessing is fitted on training data only.", "tone": ""},
        {"icon": icon("keyboard"), "title": "Three inputs",
         "body": "step, type and amount. Names, all four balance fields and isFlaggedFraud are excluded.", "tone": "yellow"},
    ]), unsafe_allow_html=True)

    st.markdown("### Dataset and provenance")
    st.markdown(
        "This project uses **PaySim**. The public Kaggle distribution is "
        "[Synthetic Financial Datasets For Fraud Detection](https://www.kaggle.com/datasets/ealaxi/paysim1) and the simulator is "
        "described in the [PaySim research paper](https://www.msc-les.org/proceedings/emss/2016/EMSS2016_249.pdf). "
        "The fitted preprocessing and Random Forest pipeline are reused; the app never retrains it.")

    st.markdown("### Class imbalance and temporal shift")
    st.markdown(cards_html([
        {"label": "Training fraud rate", "value": "0.0819%", "tone": ""},
        {"label": "Validation fraud rate", "value": "0.0586%", "tone": ""},
        {"label": "Test fraud rate", "value": "0.4196%", "tone": "yellow", "note": "About 5 to 7 times higher"},
    ], cols=3), unsafe_allow_html=True)
    st.markdown("Fraud is rare, and the later test period has far more of it than earlier periods, so precision and recall at a fixed threshold can shift over time.")

    st.markdown("### Limitations")
    st.markdown(callout_html(
        "This is an educational research prototype, not a production banking security system. It has not been validated on "
        "real UPI data, does not verify identities or recipients, and does not guarantee a payment is safe or fraudulent. "
        "Scores are not calibrated probabilities of real-world fraud. Do not use it to authorize or block real payments.",
        "alert"), unsafe_allow_html=True)
    st.caption(f"Approved educational threshold: {bundle.threshold:.9f}, selected using validation data.")


# ------------------------------------------------------------------ main
def main():
    inject_theme()
    st.session_state.setdefault("nav", NAV[0])
    with st.sidebar:
        st.markdown(brand_html(), unsafe_allow_html=True)
        st.write("")
        page = st.radio("Navigate", NAV, key="nav", label_visibility="collapsed")
        st.write("")
        st.markdown('<div class="side-note">Trained on synthetic PaySim data, not real UPI payments. '
                    'Everything runs on your machine.</div>', unsafe_allow_html=True)
    try:
        bundle = get_bundle()
    except Exception as exc:
        st.error("The saved model or evaluation artifacts could not be loaded. Confirm the project files are present and install the requirements listed in `requirements.txt`.")
        st.caption(f"Diagnostic category: {type(exc).__name__}. No local artifact path is shown here.")
        st.stop()

    {
        "Overview": page_home,
        "Payment simulator": page_simulator,
        "Model performance": page_performance,
        "Batch check": page_batch,
        "About and limits": page_about,
    }[page](bundle)

    st.markdown(
        '<div class="app-footer"><b>Made by Shreya Thapa and Harshita Bagwe</b>'
        '<span>Machine Learning Research Project, 2026</span>'
        '<span>Predictions are indicators, not guarantees. Data is processed locally.</span></div>',
        unsafe_allow_html=True)


if __name__ == "__main__":
    main()
