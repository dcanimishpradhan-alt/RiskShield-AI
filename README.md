# RiskShield-AI

Chargebacks are one of the most expensive, time-sensitive loss categories for online merchants. When a customer disputes a payment, the merchant typically has 7–21 days to compile evidence and respond — and most merchants lose by default because they can't gather proof fast enough, submit weak evidence, or miss the deadline entirely. On top of that, coordinated fraud rings can quietly rack up losses before anyone notices a spike.

RiskShield AI is an end-to-end prototype that tackles both problems:

Risk Scoring — flags risky transactions in real time using a supervised + unsupervised ML ensemble.
Chargeback Defense — automatically assembles evidence, predicts win probability, drafts a formal dispute narrative with an LLM, and checks eligibility for Visa Compelling Evidence 3.0 (CE3.0) liability-shift rules.
Fraud Spike Detection — a lightweight statistical (non-ML) CUSUM detector that flags sudden jumps in fraud rate.
Razorpay Integration — a webhook receiver that ingests dispute events (HMAC-verified) and a live dashboard that displays them.

All transaction, customer, and dispute data used here is 100% synthetically generated, no real merchant or customer data is involved anywhere.

Architecture is as follows

Razorpay Webhooks ──▶ Signature Verification ──▶ Dispute Data
                                                       │
                                                       ▼
Synthetic Transactions ──▶ Risk Scoring (XGBoost + Isolation Forest)
        │                                             │
        ▼                                             ▼
Chargeback Case Generator ──▶ Visa CE3.0 Engine ──▶ Evidence Narrative (LLM)
        │
        ▼
Fraud Spike Detector (CUSUM)
        │
        ▼
Merchant Dashboard (index.html) ◀── FastAPI backend (component4.py)

What Each File Does

Data generation

component1a.py — Synthetic Transaction Generator Generates 10,000 realistic Razorpay-style transactions across four categories: normal (85%), friendly_fraud (8%), true_fraud (5%), and abuse_ring (2%). It builds a pool of ~800 "returning customers" with stable customer IDs, card hashes, and usual devices/IPs so that repeat-transaction history exists in the data (needed later for CE3.0 matching, which requires prior undisputed transactions on the same card). True fraud transactions get high amounts, odd hours, and foreign IPs; abuse-ring transactions share a small pool of devices/IPs. The script also does an 80/20 stratified train/test split and prints a sanity check on how many cards have 2+ undisputed transactions (i.e., are CE3.0-testable).

chargeback.py — Standalone Chargeback Case Generator (v1) An early, self-contained version that generates 550 synthetic chargeback cases directly (not tied to component1a's transactions). Each case gets a random reason code (13.1 Merchandise Not Received, 13.2 Not as Described, 10.4 Fraud CNP, 13.6 Credit Not Processed), a plausible evidence bundle per reason code, a response deadline, and a simulated win/loss outcome label (with higher win probability when strong evidence like 3DS authentication or delivery proof exists). Note: this file currently has a syntax error ()deadline = ...) that needs fixing before it will run.

component1c.py — Chargeback Case Generator (v2, linked to transactions) The refined version of the chargeback generator. It loads the train/test transactions produced by component1a.py, filters to only the ones flagged is_disputed == True, and generates a matching chargeback case for each (up to 550), reusing real fields like device_fingerprint and delivery_status from the underlying transaction. It also includes a NumpyEncoder helper so numpy types (bool_, integer, floating, ndarray) serialize cleanly to JSON.

Risk scoring

component2a.py — Risk Scoring Engine Defines RiskScorer, an ensemble of an Isolation Forest (unsupervised, catches novel/unseen fraud patterns) and an XGBoost classifier (supervised, high precision on known fraud patterns). extract_features() builds a small feature set (amount, hour of day, and simulated velocity/geo-distance features). predict_risk() blends the two models 70/30 (XGBoost-weighted) into a single 0–100 risk score, along with the raw fraud probability and an anomaly flag. The __main__ block trains on data/synthetic_train.json and runs a sample prediction.

component2b.py — Fraud Spike Detector (deliberately non-AI) Implements SpikeDetector, a CUSUM (cumulative sum control chart) algorithm that watches the fraud rate over time and raises an alert when it drifts significantly above a rolling baseline. This is a deliberate design choice to use classical statistics instead of ML for a problem that's already well-solved that way. Includes pytest unit tests covering normal background noise, a genuine spike triggering an alert, and manual state reset.

Chargeback defense

visa.py — Visa CE3.0 Engine driver script A demo script that imports a VisaCE3Engine (from src/chargeback/visa_ce3.py in the fuller project structure) and runs it against a mock disputed transaction plus two prior "clean" historical transactions on the same card, sharing the same IP and device fingerprint. This exercises the Visa Compelling Evidence 3.0 rule: if a merchant can show 2+ prior undisputed transactions (120–365 days old) that match on identity signals like IP/device, liability for a Reason Code 10.4 (fraud) dispute shifts back to the issuer.

component3a.py — LLM Evidence Narrative Generator Defines NarrativeGenerator, which calls the Gemini API (google.genai) to turn a structured evidence bundle (auth status, delivery proof, customer history, etc.) into a formal, persuasive dispute-response letter for the acquiring bank. It requires a GEMINI_API_KEY environment variable. The design intent is that the LLM only writes the narrative prose — every factual claim (dates, statuses, IDs) is injected from verified data rather than generated, to avoid hallucinated evidence.

Backend & webhook integration

component4.py — FastAPI Backend A small FastAPI app with three endpoints:

POST /webhook/dispute — receives a Razorpay-style dispute webhook, verifies its X-Razorpay-Signature via HMAC-SHA256, extracts the dispute entity and any Visa CE3.0 eligibility status from the payload, stores it as latest_dispute, and prints a formatted alert to the console.
GET /api/dispute — returns the most recently received dispute so the frontend can poll it.
GET /health — basic health check used by the dashboard to show connection status.

CORS is fully open (allow_origins=["*"]) since this is a local hackathon/demo setup.

webhook.py / test.py — Webhook test scripts Both scripts (near-duplicates) build a fake payment.dispute.created-style payload, compute the correct HMAC-SHA256 signature using the shared test secret (rzp_test_secret_hackathon), and POST it to http://127.0.0.1:8000/webhook/dispute to verify the backend accepts and processes it correctly.

index.html — Merchant Dashboard A single-page Tailwind-styled dashboard that:

Polls /health every 5 seconds to show whether the backend is connected.
Polls /api/dispute every 2 seconds and renders the latest captured dispute — dispute ID, status, amount (converted from paise to ₹), currency, and Visa CE3.0 eligibility status — inside a red "fraudulent transaction detected" alert card.
Shows a friendly "waiting for transaction" placeholder when nothing has come in yet.

Supporting files

rs.py — a scaffolding/bootstrap script that programmatically writes out the fuller intended project structure (requirements.txt, .env.example, src/data/synthetic_generator.py, src/risk/scorer.py, etc.) as string templates — essentially a generator for the project skeleton described in implementation_razorpay.md.
implementation_razorpay.md — the original hackathon proposal/spec: problem statement (₹8,000–15,000 Cr/year in chargeback losses), full architecture, and a component-by-component build plan (data generation, risk scoring, LLM evidence narratives, Visa CE3.0, Razorpay integration, dashboard).
riskshield_ai_submission.zip — the fuller, organized project layout (src/api, src/chargeback, src/data, src/razorpay, src/risk, src/resilience, tests/, docs/ including AI_JUDGMENT.md, METRICS.md, FAILURE_LOG.md, ARCHITECTURE.md) that the flat component scripts above were built towards.
LICENSE, _gitignore — standard project license and git-ignore rules.

Design Principles

Use AI only where it adds real value. XGBoost/Isolation Forest for tabular fraud detection (interpretable, fast); Gemini LLM only for writing narrative prose from verified facts (never for generating the facts themselves); plain CUSUM statistics for spike detection instead of ML, since it's a well-solved problem.
Defense-only. Nothing in this codebase generates fraud, evades detection, or attacks a merchant — every component here helps a merchant detect or evidence real disputes.
All data is synthetic. No real customer, card, or merchant data is used anywhere in generation, training, or testing.
