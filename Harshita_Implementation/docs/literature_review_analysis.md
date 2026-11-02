# Literature survey analysis: UPI transaction fraud detection

## Scope and evidence notes

This report records the analysis of the ten supplied PDFs in `research_materials/`. It distinguishes details stated in the papers from information unavailable or internally inconsistent in the PDFs. No claims below should be treated as independently reproduced results. Several papers provide too little information about data, splits, or evaluation to support a reliable comparison.

## Paper-by-paper analysis

### 1. Advancing Secure and Trustworthy Facial Recognition Payment Systems in India: Investigating User Privacy, Trust, & Technological Challenges

- **Authors:** Justus Edem Kwaku Tsar; Vijeshwar Singh Gandhi.
- **Year and venue:** 2025, *International Journal for Multidisciplinary Research*, vol. 7, issue 6 (November–December 2025).
- **Problem:** Trust, privacy, usability, and security challenges in facial-recognition payment systems in India.
- **Method:** The paper mixes a proposed CNN-based payment pipeline with a small user study/interviews and usability analysis. It mentions CNNs and discusses MobileFaceNet, ViT, and MAHA-Net, but does not give enough detail to reproduce a defined model pipeline.
- **Dataset:** No named or publicly accessible image dataset is identified. The user study is described as involving 30 participants; the exact interview/usability sample and protocol are unclear.
- **Models:** CNN is named; several face-recognition architectures are discussed. No controlled model comparison is documented.
- **Results:** It claims 58.3% recognition accuracy, 41.7% FAR, 1% FRR, 95% spoofing detection, and 99.2% transaction success under two seconds; user experience is reported as 92%. Denominators, test split, and measurement protocol are not adequately specified, and the figures are difficult to reconcile.
- **Limitations:** Results are not reproducible from the information given; biometric authentication is not equivalent to transaction fraud classification; privacy and fairness are discussed more broadly than measured.
- **Relevance:** Useful context for user trust, biometric privacy, spoofing, and adoption. Not a suitable benchmark for tabular UPI fraud detection.

### 2. Detection of Fraudulent Activities in Unified Payments Interface using Machine Learning - LSTM Networks

- **Authors:** M. Naga Raju; Yarramreddy Chandrasena Reddy; Polavarapu Nagendra Babu; Venkata Sai Pavan Ravipati; Velpula Chaitanya.
- **Year and venue:** 2024, IEEE International Conference on Computing, Power and Communication Technologies (ICCPCT); DOI 10.1109/ICCPCT61902.2024.10672890.
- **Problem:** Detect fraudulent UPI transactions with sequential machine learning.
- **Method:** Stacked LSTM, with synthetic data/GAN augmentation and imbalance treatment described. The actual generation, preprocessing, and sequence construction are not sufficiently specified.
- **Dataset:** The paper refers to synthetic and real data and online sources, but does not identify a reproducible dataset, record count, label prevalence, or exact source.
- **Models:** Stacked LSTM; GAN-generated augmentation; random oversampling and SMOTE are mentioned.
- **Results:** Reported accuracy 99.74%, precision 99.31%, recall 99.57%, and F1 99.19%. The stated precision and recall imply an F1 of approximately 99.44%, so the reported values appear inconsistent. No independently checkable confusion matrix or split details are supplied.
- **Limitations:** Unclear dataset provenance and possible synthetic-to-real mixing; insufficient split and leakage controls; metric inconsistency; no reproducible baseline comparison.
- **Relevance:** Directly on UPI and sequence modeling, but its claims should motivate a more transparent evaluation rather than be adopted as established performance.

### 3. Leveraging Machine Learning Techniques of Real Time Detection of UPI Fraud

- **Authors:** Rethisha R.; Sweetie Cyindia H.; Geetha R.
- **Year and venue:** 2025, IEEE International Conference on Intelligent Systems and Information Security (ICISS); DOI 10.1109/ICISS63372.2025.11076419.
- **Problem:** Real-time UPI fraud detection under class imbalance.
- **Method:** Compares Random Forest, Decision Tree, Logistic Regression, Naive Bayes, and Linear Regression; mentions B-SMOTE, Tomek links, and BIRCH. Features include amount, daily average, foreign/high-risk-country flag, and chargeback ratio.
- **Dataset:** Dataset name, source, size, time range, and class distribution are not established in the supplied paper.
- **Models:** The listed classifiers and imbalance/clustering methods above.
- **Results:** The paper gives multiple incompatible figures: 97% in the abstract, 98.3% for different models elsewhere, and a confusion matrix with TP=129, TN=784, FP=5, FN=5 (98.9% accuracy; precision and recall 96.3%). Another passage states recall 87.5% and F1 88.2%. These cannot all describe the same evaluation.
- **Limitations:** Missing data provenance and evaluation protocol; inconsistent metrics; chargeback ratio may be known only after a transaction has already been processed, creating a timing/target-leakage concern for pre-authorization detection.
- **Relevance:** Directly addresses UPI and common tabular baselines. Its feature-timing and metric issues are useful design cautions.

### 4. Secure UPI Transaction System using Face Authentication

- **Authors:** Bhakti Kailas Pawal; Anjali Chandrakant Jadhav; Pallavi Narhari Pawar; Sakshi Dipak Lad; T. S. Pawar.
- **Year and venue:** 2026, *International Journal of Innovative Research in Technology* (IJIRT), vol. 12, issue 10, March 2026.
- **Problem:** Add face authentication to a UPI transaction flow.
- **Method:** Android/web application flow using a camera, OpenCV, face matching, and transaction confirmation.
- **Dataset:** No face dataset, transaction dataset, sample size, or split is specified.
- **Models:** OpenCV/face matching is named; the specific trained face model is not documented.
- **Results:** Qualitative prototype description; no numerical fraud-detection or authentication evaluation is reported.
- **Limitations:** Prototype/security claims are not supported by a reproducible threat model or quantitative evaluation. Authentication does not itself detect fraudulent transaction behavior.
- **Relevance:** Context for a possible authentication layer; not a fraud dataset or classifier study.

### 5. Secure and Assistive UPI Transaction System for Visually Impaired People

- **Authors:** Jagdish Pimple; Aditi Dhawad; Mitesh Thummar; Nishant Wailkar; Khushi Bakde; Nihal Akhare; Anushka Pannase.
- **Year and venue:** 2025, *International Journal on Advanced Computer Engineering and Communication Technology*, vol. 14, issue 03s.
- **Problem:** Make UPI payment flows more accessible while adding confirmation/security aids.
- **Method:** Voice input and text-to-speech, QR scanning (Google ML Kit), Android biometric checks, and proposed Braille support. The implementation description varies across sections, which also mention Node/MS SQL/JWT and Java.
- **Dataset:** None reported; no participant study or transaction corpus is documented.
- **Models:** ML Kit QR scanning and platform biometrics; no fraud classifier.
- **Results:** Qualitative feature/function description without measured user or security outcomes.
- **Limitations:** No user evaluation, performance metrics, or consistent implementation specification.
- **Relevance:** Useful for designing alert/confirmation accessibility in a future prototype, but not a source of fraud labels or model evidence.

### 6. Secure online payment through facial recognition and proxy detection with the help of TripleDES encryption

- **Authors:** R. Venkatesan; B. Anni Princy; V. D. Ambeth Kumar; Manish Raghuraman; Mukesh Kumar Gupta; Ankit Kumar; Abhishek Kumar; Ajoy Kumar Khan.
- **Year and venue:** 2021, *Journal of Discrete Mathematical Sciences and Cryptography*, 24(8), pp. 2195–2205; DOI 10.1080/09720529.2021.2011096.
- **Problem:** Secure online payment using facial recognition, proxy detection, and encryption.
- **Method:** FaceNet/one-shot recognition, SVM and OpenCV Haar features are described; TripleDES protects payment data. A Deep Belief Network is also mentioned.
- **Dataset:** The text mentions 20 registration inputs but does not provide a complete benchmark dataset, split, or test protocol.
- **Models:** FaceNet, SVM, Haar cascade/OpenCV, and Deep Belief Network references; TripleDES is cryptography, not a predictive model.
- **Results:** Text reports around 80% in one place, precision 0.788, recall 0.631, F1 0.701, while a table gives “efficiency” of 97. A TripleDES “accuracy” of 94% is not a meaningful standard encryption-security metric.
- **Limitations:** Ambiguous evaluation and inconsistent numbers; no public dataset; combines authentication, proxy detection, and encryption without isolating their contributions.
- **Relevance:** Background on authentication and security controls, not evidence for a UPI transaction-level fraud model.

### 7. Security Analysis of Unified Payments Interface and Payment Apps in India

- **Authors:** Renuka Kumar; Sreesh Kishore; Hao Lu; Atul Prakash.
- **Year and venue:** 2020; the supplied PDF title page does not state venue. A cited bibliographic record identifies the 29th USENIX Security Symposium (USENIX Security 2020).
- **Problem:** Identify security weaknesses in UPI and payment applications.
- **Method:** Manual protocol/application reverse engineering across seven apps; analyzes account and transaction attack paths, vulnerabilities, and UPI 2.0 mitigations.
- **Dataset:** No transaction dataset; the objects of study are protocols/apps.
- **Models:** None.
- **Results:** Security findings and attack demonstrations, not classification metrics.
- **Limitations:** Analysis depends on the apps and versions examined; the threat model assumes a malicious app may be installed and does not assume a rooted victim device.
- **Relevance:** Strong UPI threat context that can guide features and threat assumptions; it does not supply labels for supervised ML.

### 8. Security Issues of Unified Payments Interface and Challenges: Case Study

- **Authors:** Yash Madwanna; Mayur Khadse; B. R. Chandavarkar.
- **Year and venue:** Not available in the supplied PDF.
- **Problem:** Review UPI security issues and challenges, with attention to BHIM 1.0 and UPI 2.0.
- **Method:** Secondary review/case-study discussion drawing on prior UPI security work.
- **Dataset:** None.
- **Models:** None.
- **Results:** Qualitative security analysis; no quantitative evaluation.
- **Limitations:** Bibliographic details and a reproducible case-study protocol are absent; it is not an independent transaction experiment.
- **Relevance:** Supports threat-model background, but cannot support model performance claims.

### 9. Unified payment interface: Gap analysis and directions for future research

- **Authors:** Dhivya M.; Anoop K. K.; Balamourougane R.
- **Year and venue:** 2025, *International Journal of Research in Finance and Management*, vol. 8, issue 1, pp. 459–466; DOI 10.33545/26175754.2025.v8.i1e.468.
- **Problem:** Identify adoption and research gaps in UPI.
- **Method:** Narrative/gap analysis; no systematic search protocol is stated.
- **Dataset:** None.
- **Models:** None.
- **Results:** Qualitative discussion including continuing user intent, trust, and fraud prevention as areas for further study.
- **Limitations:** No reproducible search strategy, user dataset, or quantitative test.
- **Relevance:** Helps frame adoption and trust implications around a fraud model; not technical model evidence.

### 10. UPI Scam Detection for QR Codes

- **Authors:** Himanshu Trigune; Sumit Pawar; Pranit Chavan; Sushant Tatpalle; Priya Borkar; Nita Pawar.
- **Year and venue:** 2025, *International Research Journal of Innovations in Engineering and Technology* (IRJIET), vol. 9, issue 12, December 2025, pp. 99–104; DOI 10.47001/IRJIET/2025.912014.
- **Problem:** Detect scam or suspicious UPI QR codes before payment.
- **Method:** CNN image classification combined with OpenCV, `qrcode`/`pyzbar`, UPI-format parsing/metadata checks, and a Django application.
- **Dataset:** More than 2,000 QR images are claimed; class counts, source, split, and labeling protocol are not supplied.
- **Models:** CNN plus QR decoding and rule/metadata checks.
- **Results:** “High accuracy” is claimed without a numeric metric; processing is claimed to take under 1.5 seconds.
- **Limitations:** No auditable dataset or quantitative class-wise evaluation; QR-image scam detection differs from transaction-level behavioral fraud detection.
- **Relevance:** Relevant to a separate QR/pre-payment risk layer, but not a substitute dataset for transaction classification.

## A. Topic categories

- **UPI protocol and security vulnerabilities:** Papers 7 and 8.
- **ML/DL-based transaction fraud detection:** Papers 2 and 3.
- **Biometric and cryptographic security:** Papers 1, 4, and 6.
- **QR code fraud detection:** Paper 10.
- **Accessibility and user adoption:** Papers 5 and 9; paper 1 also addresses trust and adoption.

## B. Findings across the supplied papers

1. UPI risk spans protocol/app weaknesses, account takeover/social engineering, QR deception, authentication, and user interaction. These are related but distinct detection problems.
2. The two papers closest to transaction-level ML do not provide enough dataset provenance and evaluation detail to reproduce their reported results. Their headline metrics are inconsistent or under-specified.
3. Authentication (face/biometrics), encryption, QR screening, and transaction behavior classification solve different parts of a payment security system. They should not be presented as interchangeable forms of fraud detection.
4. Trust, privacy, accessibility, and adoption matter to deployment, but the supplied work generally discusses these topics without rigorous user-study measures.
5. Accuracy alone is inadequate for rare-event fraud detection. Papers should report class counts, time-aware split design, precision/recall, F1, PR-AUC, confusion matrices, and operational false-positive burden.

## C. Research gaps supported by the papers

- **Transparent, reproducible UPI transaction data:** The two directly relevant ML papers do not establish a reproducible public dataset, source, label definition, or class distribution.
- **Evaluation integrity:** Inconsistent metric sets and missing split details prevent meaningful comparison; future work needs a locked test period and leakage review.
- **Realistic temporal evaluation:** Real-time claims are not supported by a documented chronological holdout, latency protocol, or drift analysis.
- **Label timing and feature availability:** Features such as chargeback history may be post-event. Studies should define whether detection occurs before authorization, during processing, or after settlement.
- **Domain gap:** The supplied security and UPI papers describe India’s UPI ecosystem, while general card/mobile-money benchmarks do not represent UPI rails, users, or fraud mechanisms.
- **Actionable, user-aware outputs:** Accessibility, trust, privacy, and explainable intervention are discussed but rarely measured together with detection performance.
- **Separate threat layers:** QR scam screening, biometric authentication, protocol security, and transaction anomaly detection need clearly defined labels and separate experiments, with system-level integration assessed afterward.

## D. Practical methodology recommendation

Use a tabular supervised baseline first, with a clearly documented dataset and label definition. Compare Logistic Regression with class weighting, a Random Forest, and a gradient-boosted tree model. Split chronologically so training precedes validation and test; keep transactions from the same entity from leaking across splits where feasible. Fit encoders, scalers, resampling, and feature selection on training data only. Do not use post-transaction fields for a pre-authorization task. Exclude any pre-existing rule flag that directly encodes a related outcome from the predictive feature set.

Report fraud prevalence and counts, precision, recall, F1, PR-AUC, ROC-AUC as a secondary measure, confusion matrices, and the false-positive rate/cost at the chosen operating threshold. Select thresholds using validation data and freeze them before test evaluation. Include a feature-timing and leakage audit. Use sequence/deep-learning models only if genuine event ordering and sufficient history exist; compare them against the tabular baselines. Describe non-UPI datasets explicitly as proxies, and treat UPI protocol, QR, and biometric studies as related security layers rather than equivalent transaction datasets.

## E. Existing IEEE paper inspection

`research_materials/existing_ieee_paper.tex` is present but is **0 bytes**. It contains no sections or claims, so there are no in-file unsupported claims or placeholder references to enumerate. The manuscript currently needs to be drafted. At minimum, plan sections for abstract, keywords, introduction/problem statement, related work, dataset/provenance and label definition, methodology, experimental protocol, results, discussion/threats to validity, ethics/privacy, conclusion/future work, and references. Add tables/figures only when backed by verified sources or measured experiments. Do not cite the inconsistent performance numbers above as established facts.

## Evidence boundary

This is a structured reading of the ten supplied PDFs. Missing details are marked unavailable rather than filled from filenames or assumptions. The recommendations in section D are the authors’ proposed project methodology, not results reported by the papers.
