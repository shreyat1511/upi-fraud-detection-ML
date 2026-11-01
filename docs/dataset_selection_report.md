# Dataset selection report: UPI transaction fraud detection

## Executive recommendation

No transaction dataset is currently present in the project workspace. Among the candidates reviewed, use **PaySim as the primary reproducible development benchmark**, while stating plainly that it is a **synthetic mobile-money proxy, not actual UPI data**. It has millions of transactions, thousands of labeled fraud examples, transaction types, and a relative event sequence suitable for a chronological holdout. Use `step` for time-ordered evaluation; exclude `isFlaggedFraud` as a predictor; and exclude post-transaction balance fields for a pre-authorization task.

This recommendation is conditional on accepting the domain gap: PaySim simulates an African mobile-money service, not Indian UPI. No publicly available, clearly documented, independently verified real UPI transaction dataset with meaningful labels was established in this investigation. A UPI-branded synthetic dataset may be considered only as an additional exploratory dataset after inspecting its actual files, label construction, leakage, and current license.

## 1. Workspace audit

The recursive inventory of `project workspace` found only ten research PDFs and `research_materials/existing_ieee_paper.tex` (0 bytes). No CSV, TSV, Parquet, spreadsheet, database dump, or other transaction dataset was found. The `docs/` directory was absent before this report was created.

## 2. Candidate comparison

Counts and rates below refer to the named public version where one is identified. Public mirrors can change; verify the exact downloaded file and current dataset card before acquisition. “License not confirmed” means do not assume unrestricted reuse.

### A. UPI-branded Kaggle: UPI Fraud Detection Dataset (omsshete)

- **Original/public source:** Kaggle dataset card: [UPI Fraud Detection Dataset](https://www.kaggle.com/datasets/omsshete/upi-fraud-detection-dataset). The linked independent project audit describes the file as synthetic: [audit repository](https://github.com/md-faiyazkhan/upi-fraud-detector).
- **Real or synthetic:** Reported synthetic by the audit; it should not be represented as real bank/UPI traffic.
- **Records:** 26,393 rows, 65 raw columns, as reported by that audit; not re-counted locally because the dataset has not been downloaded.
- **Features:** Audit material discusses amount, input-pause patterns, geographic disparity, receiver history, time-of-day, and device indicators. The raw dataset has many more columns; verify the exact schema and semantics from the actual file before selecting features.
- **Label and distribution:** `is_fraud`; audit reports 17.2% fraud. This is not an independently recounted distribution.
- **Time:** The audit identifies a malformed time field (`MM:SS.s`) that it drops; an integer-like hour/time-of-day field remains. It does not provide a reliable full timestamp for chronological evaluation.
- **License/restrictions:** Not confirmed from accessible dataset metadata. Check the current Kaggle card and any linked license before use, publication, or redistribution.
- **Advantages:** UPI framing and receiver/device/geographic concepts may help construct a domain-specific feature discussion; reported class balance is less extreme than many fraud benchmarks.
- **Limitations:** Synthetic; time quality is weak; audit reports strong target leakage in some indicators (including a device flag), missing and constant columns. Without the actual files and generator/label documentation, provenance and validity remain uncertain.
- **Suitability:** **Low as a primary benchmark.** At most an exploratory supplementary dataset after a schema/leakage audit and license check. UPI in the title does not make the records real UPI transactions.

### B. UPI-branded/mixed Indian banking Kaggle: Banking Transactions 2019–2024 (Belbin B.)

- **Original/public source:** [Kaggle dataset card](https://www.kaggle.com/datasets/belbino/indian-banking-transactions-20192024).
- **Real or synthetic:** The card’s stated constructed fraud logic indicates simulated/synthetic labels and transactions; it is not verified authentic bank traffic. It mixes UPI with NEFT, RTGS, IMPS, and other payment activity.
- **Records:** Card reports 550,000 records and 20 columns.
- **Features:** Customer/account identifiers, dates/times, account and transaction type, amount in INR, transaction direction/balance, merchant category/location, credit/loan/KYC and channel fields are described. Verify exact field names and missingness from the source files before use.
- **Label and distribution:** `is_fraud`; the card reports an approximate fraud rate of 0.89%, not an exact verified positive count. The described rule assigns elevated risk to overnight transactions and amounts above ₹500,000, plus a base rate. This creates a risk that a model can simply recover the label-generation rule.
- **Time:** Calendar dates spanning 2019-01-01 through 2024-01-01 are reported on the card; confirm exact inclusivity and parseability in the actual file.
- **License/restrictions:** Card reports CC0. Re-check current card metadata and attribution expectations before use.
- **Advantages:** Indian context, INR, multiple payment channels, calendar chronology, and a larger record count.
- **Limitations:** Mixed payment rails; synthetic rule-based labels; likely direct leakage from the documented label rules; provenance does not establish real UPI transactions.
- **Suitability:** **Low for evaluating generalizable fraud detection.** Potentially useful as a clearly labeled synthetic exercise for testing a pipeline, but the rule-derived target makes headline model performance unpersuasive.

### C. PaySim: Synthetic Financial Datasets For Fraud Detection

- **Original/public source:** Original simulator paper: [PaySim: A Financial Mobile Money Simulator for Fraud Detection](https://www.msc-les.org/proceedings/emss/2016/EMSS2016_249.pdf). Common public CSV mirror: [Kaggle PaySim1](https://www.kaggle.com/datasets/ealaxi/paysim1). The paper explains that lack of public real transaction data motivated an agent-based simulator calibrated from aggregated mobile-money data; the synthetic transactions are not an exact replay of the source service.
- **Real or synthetic:** Entire transaction rows are synthetic, generated by PaySim. Underlying simulator parameters were informed by aggregated real service data.
- **Records:** Common CSV version reports 6,362,620 rows and 11 columns: 8,213 fraud (about 0.129%) and 6,354,407 non-fraud. Verify this against the actual file/version at download.
- **Features:** `step`, `type`, `amount`, `nameOrig`, `oldbalanceOrg`, `newbalanceOrig`, `nameDest`, `oldbalanceDest`, `newbalanceDest`, `isFraud`, `isFlaggedFraud`. Types include CASH_IN, CASH_OUT, DEBIT, PAYMENT, and TRANSFER.
- **Label and distribution:** `isFraud` is the simulator’s fraud outcome; common version has 8,213 positives. `isFlaggedFraud` is a rule flag, not the outcome label, and should not be used as an input when predicting `isFraud`.
- **Time:** `step` gives relative simulation time (744 steps, commonly described as hourly, over about 31 days); it is not a calendar timestamp. This supports ordered evaluation, but not calendar seasonality analysis.
- **License/restrictions:** Common Kaggle distribution is reported as CC BY-SA 4.0; check the exact current Kaggle card and linked terms before use. If CC BY-SA applies, attribution and share-alike obligations may apply to adapted database material.
- **Advantages:** Large, clearly labeled, published simulator provenance; thousands of positive examples; payment types and entity identifiers; repeatable public benchmark; relative time allows a chronological split.
- **Limitations:** Synthetic and non-Indian; labels reflect simulator rules; only about a month of relative time; no genuine UPI identifiers, authorization protocol, or Indian fraud ecology. Post-event balances may reveal transaction outcomes, so using them for pre-authorization detection risks target leakage.
- **Suitability:** **Best primary benchmark among those reviewed** for reproducible model development, with explicit proxy framing and pre-event feature discipline.

### D. ULB/Worldline credit-card fraud dataset

- **Original/public source:** Public benchmark mirror: [Kaggle Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud); OpenML record: [data set 42175](https://www.openml.org/search?type=data&id=42175).
- **Real or synthetic:** Real European card transaction records, anonymized and transformed.
- **Records:** 284,807 transactions; 492 fraud (about 0.173%) and 284,315 non-fraud in the canonical version.
- **Features:** 31 columns: `Time`, `V1`–`V28`, `Amount`, and `Class`. V features are anonymized PCA components, not interpretable raw transaction fields.
- **Label and distribution:** `Class` indicates legitimate versus fraud; canonical set has 492 positive cases.
- **Time:** `Time` is elapsed seconds from the first transaction, covering two days in September 2013; relative chronology, not a calendar timestamp.
- **License/restrictions:** Commonly identified as Open Database License (ODbL) for the public database distribution. Confirm exact source terms before redistribution or publishing derivatives; attribution/share-alike requirements may apply.
- **Advantages:** Real transactions and labels; canonical, widely studied benchmark; supports rare-event evaluation and time ordering.
- **Limitations:** Credit card, not UPI/mobile money; only two days and 492 frauds; anonymized PCA features constrain interpretation and domain-specific policy analysis.
- **Suitability:** **Good secondary benchmark** for testing evaluation practice and domain transfer. Less appropriate than PaySim as the single primary dataset for a UPI-focused student project because its feature semantics and payment mechanism differ substantially.

### E. BankSim

- **Original/public source:** Original paper: [BankSim: A Bank Payments Simulator for Fraud Detection Research](https://www.msc-les.org/proceedings/emss/2014/EMSS2014_144.pdf). Public mirror: [Kaggle BankSim](https://www.kaggle.com/ntnu-testimon/banksim1).
- **Real or synthetic:** Synthetic agent-based bank-payment data, calibrated using aggregated Spanish bank payment data.
- **Records:** Common version has 594,643 transactions, 7,200 fraud (about 1.21%) and 587,443 non-fraud; approximately 180 simulation steps.
- **Features:** `step`, customer, age, gender, origin ZIP, merchant, merchant ZIP, category, amount, and `fraud`.
- **Label and distribution:** `fraud` is the simulator label; 7,200 positives in common version.
- **Time:** `step` is relative, discrete simulation time (roughly six months/180 steps as commonly documented), not a real timestamp.
- **License/restrictions:** Common Kaggle mirror/README identifies CC BY-NC-SA 4.0. Verify current source terms; noncommercial/share-alike restrictions can affect publication and reuse.
- **Advantages:** Provenance in a research simulator paper; moderate number of positive examples; customer/merchant/category features and relative chronology.
- **Limitations:** Synthetic Spanish retail-payment environment, not UPI; simulator-specific patterns; noncommercial terms may constrain downstream reuse.
- **Suitability:** **Useful secondary synthetic benchmark** to compare whether conclusions depend on one simulator, if the license permits the intended academic use. Not a stand-in for real UPI.

### F. IEEE-CIS Fraud Detection

- **Original/public source:** [Kaggle IEEE-CIS competition and data](https://www.kaggle.com/competitions/ieee-fraud-detection/data). Competition discussion identifies Vesta as the data provider: [provider statement](https://www.kaggle.com/competitions/ieee-fraud-detection/discussion/100304).
- **Real or synthetic:** Real-world e-commerce/cardless payment provider data, anonymized and engineered; not UPI.
- **Records:** Training transaction table has 590,540 rows and 394 columns; identity table has 144,233 rows and 41 columns. `isFraud` has 20,663 positive and 569,877 negative training labels (about 3.50%). Confirm the exact competition release on acquisition. Test labels are withheld by the competition.
- **Features:** Amount, product/card/address/email-domain fields, engineered C/D/M/V feature groups, and device/identity fields. Identity fields only exist for part of the transaction population.
- **Label and distribution:** `isFraud` target in labeled training transactions; test labels require the competition evaluation mechanism.
- **Time:** `TransactionDT` is relative elapsed time from an unknown reference, useful for chronological ordering but not calendar interpretation.
- **License/restrictions:** Governed by Kaggle competition terms rather than a general open license. Review current competition rules and redistribution restrictions before use or publication.
- **Advantages:** Many labeled fraud examples; provider-sourced real-world data; high feature variety and useful device context; relative temporal ordering.
- **Limitations:** E-commerce/card-not-present domain, not UPI; many opaque/anonymized columns; substantial missingness; competition terms and hidden test labels add friction.
- **Suitability:** **Strong alternative** if real-world labeled fraud volume is prioritized and the project can comply with competition rules. Domain mismatch remains, and terms are less straightforward than an open benchmark.

### G. Sparkov synthetic credit-card transactions

- **Original/public source:** [Kaggle Fraud Detection dataset](https://www.kaggle.com/datasets/kartik2112/fraud-detection); generator: [Sparkov Data Generation](https://github.com/namebrandon/Sparkov_Data_Generation).
- **Real or synthetic:** Fully synthetic US card-not-present-style transactions generated by Sparkov.
- **Records:** Common combined version reports 1,852,394 transactions and 9,651 fraud (about 0.52%); common train/test files differ in row counts across versions and repackagings. Treat this as version-specific, and recount the selected files before reporting.
- **Features:** Timestamp, merchant, category, amount, synthetic card number, first/last name, gender, address, location/coordinates, city population, job, date of birth, transaction number/time, merchant coordinates, and fraud label; column counts vary with file/version and derived fields.
- **Label and distribution:** Synthetic `is_fraud`/fraud label; common version has 9,651 positive examples.
- **Time:** Full generated transaction date/time, commonly spanning 2019–2020; exact range depends on package version.
- **License/restrictions:** Kaggle card is reported as CC0 1.0; verify current card and generator terms before reuse.
- **Advantages:** Interpretable fields, detailed event timestamps, many positive examples, accessible generator for understanding provenance.
- **Limitations:** Synthetic US card data and generator-specific fraud patterns; identity/location fields can make shortcuts; package variants and counts need careful version pinning.
- **Suitability:** **Secondary synthetic benchmark** for timestamped experiments, but not a primary UPI proxy because payment context and labels are generated.

## 3. Recommendation and experimental use

### Recommended choice: PaySim as the primary development dataset

PaySim provides the best balance of a published generating process, large volume, a useful number of positive labels, transaction types, and ordered time steps among the public options reviewed. It is suitable for demonstrating a reproducible fraud-detection workflow. The project must state that results are on **synthetic mobile-money data**, not UPI transactions, and avoid claiming direct UPI effectiveness.

Recommended evaluation design:

1. Pin the exact public file/version and record source URL, retrieval date, checksum, row count, schema, and license terms after approval and acquisition.
2. Use an early-to-late chronological split by `step`; keep the final period untouched until evaluation.
3. Predict `isFraud`; exclude `isFlaggedFraud` from features. For a pre-authorization task, exclude all post-transaction balances (`newbalanceOrg`, `newbalanceDest`) and carefully justify any other fields by when they are available.
4. Compare Logistic Regression, Random Forest, and one gradient-boosted tree baseline. Do not apply oversampling before the split; any balancing must be fit only on training data.
5. Report prevalence, precision, recall, F1, PR-AUC, confusion matrix, and threshold-specific false positives. Choose the threshold on validation data, then report once on the held-out later period.
6. Treat model performance as benchmark results on PaySim. If permitted and time allows, evaluate a second dataset separately; do not pool domains and describe the result as UPI-specific.

### Alternatives by objective

- **Real transaction labels / general fraud benchmark:** ULB credit-card data is open and reproducible but has only two days, 492 positives, and opaque PCA variables. IEEE-CIS has many more positive labels and richer features but is e-commerce data under competition terms.
- **Longer synthetic payment chronology:** BankSim offers customer/merchant attributes and a different simulator, with noncommercial/share-alike constraints.
- **Full calendar timestamped synthetic data:** Sparkov is useful for timestamp-driven experiments, but contains generated card transactions and needs strong leakage and version checks.
- **UPI-branded synthetic exploration:** The two UPI-named Kaggle candidates have significant provenance/label validity concerns. The transaction-level `is_fraud` dataset in particular appears to encode fraud through generator rules; a model may learn those rules rather than general fraud behavior.

## 4. Conclusions and cautions

- No candidate in this review is verified real, labeled UPI transaction data.
- Dataset names and India/UPI fields do not prove that records came from a bank or NPCI production systems.
- Synthetic datasets are valuable for methodology development, but their results describe their simulator and label rules.
- License conditions were not equally accessible for every Kaggle mirror. Re-check the exact dataset card and terms before download, transformation, sharing, or publication.
- No dataset has been downloaded; no synthetic data has been generated; no models have been trained; no existing research file has been edited.

## Sources

Primary sources and dataset cards are linked in each candidate section. Counts and feature descriptions are version-specific and should be verified against the acquired files before they are used as experimental facts.
