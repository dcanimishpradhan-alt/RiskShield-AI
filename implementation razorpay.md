# AI Risk Manager — Razorpay Buildathon

> **Track:** 02 — AI Risk Manager  
> **Project Name:** **RiskShield AI** — Intelligent Chargeback Evidence Auto-Responder & Fraud Spike Detector  
> **Tagline:** Stop merchants losing money to chargebacks with AI that fights back with evidence, not guesswork.

## Why This Will Win

We're building a **two-pronged system** that addresses the most expensive and time-sensitive loss class for merchants — chargebacks — while also providing proactive fraud spike detection. This gives us a unique edge because:

1. **Problem Taste (Max Points):** Chargebacks cost Indian merchants ₹8,000–₹15,000 Cr annually. Most merchants lose disputes by default because they can't compile evidence fast enough (7–21 day windows). This is the single most impactful, unsolved, real-world problem in the track.

2. **Build Quality (Max Points):** A working end-to-end pipeline with synthetic data, measured metrics, clean code architecture, and a real dashboard — not a prototype.

3. **AI Judgment (Max Points):** We deliberately use AI where it adds value (LLM for evidence narrative generation, ML for fraud pattern detection) and **explicitly choose NOT to use AI** for deterministic tasks (rule-based velocity checks, threshold alerts). This is the #1 differentiator — showing restraint.

4. **Failure Recovery (Max Points):** We'll document every failure point and how we handled it in a structured failure log. We'll also build graceful degradation into the system.

---

## The Problem We're Solving

> [!IMPORTANT]
> **Chargebacks are a ₹10,000 Cr+ annual loss for Indian e-commerce merchants.** When a customer disputes a payment, the merchant has 7–21 days to compile evidence (delivery proof, communication logs, usage data) and respond. Most merchants:
> - Miss the deadline (auto-loss)
> - Submit weak/incomplete evidence (easy reversal)  
> - Can't detect coordinated fraud rings filing multiple chargebacks
>
> **Our system automates the entire evidence-response pipeline AND detects fraud spikes before they become chargebacks.**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RiskShield AI                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │ Razorpay API │───▶│  Data Ingestion  │───▶│  Risk Scoring    │  │
│  │  (Webhooks)  │    │  Layer           │    │  Engine          │  │
│  └──────────────┘    └──────────────────┘    └──────────────────┘  │
│                              │                        │             │
│                              ▼                        ▼             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Two Core Modules                          │  │
│  │                                                              │  │
│  │  ┌────────────────────┐    ┌────────────────────────────┐   │  │
│  │  │  🛡️ Module 1:      │    │  📊 Module 2:               │   │  │
│  │  │  Chargeback        │    │  Fraud Spike               │   │  │
│  │  │  Evidence          │    │  Detector                  │   │  │
│  │  │  Auto-Responder    │    │                            │   │  │
│  │  │                    │    │  • Velocity anomaly        │   │  │
│  │  │  • Evidence gather │    │  • Cluster analysis        │   │  │
│  │  │  • LLM narrative   │    │  • Geographic anomaly      │   │  │
│  │  │  • Submission prep │    │  • Device fingerprint      │   │  │
│  │  │  • Win-rate predict│    │  • Ring detection (graph)   │   │  │
│  │  └────────────────────┘    └────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   Merchant Dashboard                         │  │
│  │  Risk Score │ Disputes │ Evidence │ Metrics │ Failure Log     │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Proposed Implementation

### Component 1: Synthetic Data Generator

> This is critical — the hackathon requires "measured precision and recall on a held-out test set." We generate realistic synthetic payment data with known fraud labels.

#### [NEW] `src/data/synthetic_generator.py`
- Generate 10,000+ synthetic transactions with realistic distributions:
  - **Normal transactions** (85%): Typical amounts, regular hours, known devices
  - **Friendly fraud/chargebacks** (8%): Legitimate purchases where buyer disputes
  - **True fraud** (5%): Stolen cards, unusual geolocations, velocity anomalies
  - **Abuse rings** (2%): Coordinated patterns across linked accounts
- Each transaction includes: amount, timestamp, device_fingerprint, ip_geo, card_hash, merchant_category, customer_history, delivery_status, communication_log
- **80/20 train/test split** with stratified sampling
- Export as Razorpay-compatible JSON format (order_id, payment_id, etc.)

#### [NEW] `src/data/chargeback_cases.py`
- Generate 500+ synthetic chargeback cases with:
  - Dispute reason codes (mapped to Visa/Mastercard codes)
  - Available evidence per case (delivery proof, IP logs, email threads)
  - Known outcome labels (won/lost) for training win-rate predictor
  - Response deadline timestamps

---

### Component 2: Risk Scoring Engine (ML — Where AI Adds Real Value)

#### [NEW] `src/risk/scorer.py`
- **Ensemble model** combining:
  - **Isolation Forest** for anomaly detection (unsupervised — catches novel fraud)
  - **XGBoost classifier** for known fraud patterns (supervised — high precision)
  - **Graph-based ring detection** using NetworkX (identifies coordinated abuse)
- Feature engineering:
  - Velocity features (txns/hour, txns/card/day, amount acceleration)
  - Geographic features (IP-to-billing distance, impossible travel)
  - Behavioral features (time-of-day patterns, device diversity)
  - Network features (shared device/IP/email clusters)
- Output: Risk score 0–100 with explainable feature contributions (SHAP values)

> [!TIP]
> **AI Judgment Differentiator:** We use XGBoost (not a deep learning model) because it's interpretable, fast, and appropriate for tabular fraud data. We'll explicitly document WHY we didn't use a transformer/LLM here — overfitting risk on small data, lack of interpretability for financial decisions. This shows the "AI judgment" the judges want to see.

#### [NEW] `src/risk/spike_detector.py`
- **Statistical process control** (NOT AI — deliberate choice):
  - CUSUM algorithm for detecting shifts in fraud rate
  - Bollinger-band style thresholds on rolling fraud velocity
- **Why not AI here:** Spike detection is a well-solved statistical problem. Using an LLM or neural network would be over-engineering. We'll call this out explicitly in our submission.

---

### Component 3: Chargeback Evidence Auto-Responder (LLM — Where AI Genuinely Helps)

#### [NEW] `src/chargeback/evidence_collector.py`
- Automatically gather evidence from:
  - Razorpay Payment API (payment details, refund status, settlement info)
  - Order API (order metadata, fulfillment status)
  - Synthetic delivery/logistics data
  - Customer communication logs (synthetic email/chat threads)
- Compile evidence package per dispute reason code:
  - **13.1 (Merchandise Not Received):** Delivery confirmation, tracking, signed POD
  - **13.2 (Not as Described):** Product photos, return policy, communication log
  - **10.4 (Fraud — Card Not Present):** AVS match, 3DS auth, device fingerprint, IP match
  - **13.6 (Credit Not Processed):** Refund receipt, policy terms

#### [NEW] `src/chargeback/narrative_generator.py`
- **This is where LLM shines:** Generate a structured, persuasive evidence narrative using an LLM (Gemini API or OpenAI)
- Template-guided generation (not free-form — reduces hallucination risk):
  ```
  DISPUTE TYPE: {reason_code} — {reason_description}
  
  EVIDENCE SUMMARY:
  1. Authentication: {3ds_status, avs_match, cvv_verified}
  2. Delivery: {tracking_number, delivery_date, signature}
  3. Customer History: {total_orders, dispute_rate, last_login}
  4. Communication: {email_timestamps, resolution_attempts}
  
  NARRATIVE: [LLM generates this section based on evidence]
  
  RECOMMENDATION: {contest / accept_loss / partial_refund}
  ```
- **Win-rate predictor** using logistic regression on case features → tells merchant whether to fight or accept

> [!IMPORTANT]
> **AI Judgment Signal:** The LLM generates ONLY the narrative paragraph. All factual claims (dates, amounts, statuses) are injected from verified data. We never let the LLM fabricate evidence. This is a critical trust/safety boundary we'll highlight.

#### [NEW] `src/chargeback/response_builder.py`
- Compile the final dispute response package
- Format for **Razorpay Disputes API** submission:
  - `PATCH /v1/disputes/:id/contest` with `action: "submit"`, `amount`, `summary`, and `evidence` (document IDs)
  - `POST /v1/disputes/:id/accept` when win probability is too low (saves dispute fees)
  - Upload evidence docs via `POST /v1/documents` with `purpose: "dispute_evidence"`
- Include confidence score and recommendation
- Generate PDF evidence bundle

#### [NEW] `src/chargeback/visa_ce3.py` — Visa Compelling Evidence 3.0 Engine
- **This is a massive competitive edge** — implements the actual Visa CE3.0 protocol:
  - For Reason Code 10.4 (Fraud - Card-Absent), automatically scans merchant transaction history to find **2 prior undisputed transactions** from 120–365 days ago on the same card
  - Proves identity overlap on **2 of 4 data elements**: IP address, device ID, user login, shipping address (at least one must be IP or device ID)
  - If CE3.0 criteria met → automatic liability shift back to issuer
- Most competitors won't know this protocol exists — it's our secret weapon

---

### Component 4: Razorpay Integration Layer

> [!WARNING]
> **Test Mode Limitation:** Razorpay Test Mode does NOT natively generate disputes/chargebacks (these originate from issuing banks in production). We build a **Mock Webhook Simulator** that sends synthetic `payment.dispute.*` events to our webhook endpoint.

#### [NEW] `src/razorpay/mock_webhooks.py`
- Simulates Razorpay webhook payloads with proper HMAC-SHA256 signatures
- Generates `payment.dispute.created`, `payment.dispute.action_required`, `payment.dispute.won`, `payment.dispute.lost`
- Uses test card numbers: `4718 6091 0820 4366` (Domestic Visa), `5104 0155 5555 5558` (International MC)
- Simulates `payment.authorized` → risk scoring → capture/void flow
- Simulates `payment.failed` bursts for BIN attack detection

#### [NEW] `src/razorpay/client.py`
- Razorpay API client wrapper for test mode (`rzp_test_*` keys)
- Two-step capture workflow: `capture=0` on order creation → AI risk score → `POST /v1/payments/:id/capture` or `POST /v1/payments/:id/refund`
- Webhook signature verification: `hmac.compare_digest(expected_sig, headers["X-Razorpay-Signature"])`
- Idempotency handling via `x-razorpay-event-id` deduplication

---

### Component 5: Merchant Dashboard (FastAPI + Jinja2)

#### [NEW] `src/api/main.py` — FastAPI backend
- `POST /webhook/payment` — Receive payment webhooks with HMAC verification, trigger risk scoring
- `POST /webhook/dispute` — Receive dispute webhooks, trigger evidence collection pipeline
- `GET /api/dashboard` — Dashboard metrics (risk scores, dispute stats, win rate)
- `GET /api/disputes` — List active disputes with status, evidence quality, and deadlines (`respond_by`)
- `GET /api/disputes/{id}/evidence` — Get compiled evidence for a dispute
- `POST /api/disputes/{id}/respond` — Submit auto-generated response via Razorpay contest API
- `GET /api/alerts` — Fraud spike alerts (CUSUM-triggered)
- `GET /api/metrics` — Honest metrics endpoint (PR-AUC, insult rate, FP cost, net economic value)

#### [NEW] `src/frontend/` — Clean, minimal dashboard
- **Risk Overview**: Real-time risk score distribution, fraud spike alerts
- **Dispute Manager**: Active disputes, evidence quality, win-rate predictions
- **Metrics Panel**: Precision/recall curves, confusion matrix, FP cost analysis
- **Failure Log**: Transparent log of what broke and how it was handled

---

### Component 5: Metrics & Honest Evaluation

> [!WARNING]
> The hackathon explicitly says: **"Honest metrics including false-positive cost."** This is where most teams will fumble. We go all-in on transparency.

#### [NEW] `src/evaluation/metrics.py`
- **Standard metrics** (with correct choices):
  - ❌ **NOT ROC-AUC** — misleading under extreme class imbalance (massive TN count hides FP surge)
  - ❌ **NOT Accuracy** — a model predicting 100% legitimate gets 99.9% accuracy
  - ✅ **PR-AUC (Average Precision)** — evaluates only on minority class, not diluted by TN
  - ✅ **Precision @ fixed Recall** (e.g., Precision @ 80% Recall)
  - ✅ **Recall @ fixed FPR** (e.g., Recall @ 0.1% FPR)
- **Business metrics** (the differentiator):
  - **Insult Rate**: FP/TP ratio — how many good customers blocked per fraudster caught (target: <5:1)
  - **False Positive Cost**: Each FP = legitimate transaction blocked = lost revenue (~₹2,500 avg) + customer churn
  - **False Negative Cost**: Each FN = chargeback + penalty fee (~₹5,000 avg)  
  - **Net Economic Value**: `Σ(TP × Fraud_Loss_Avoided) - Σ(FP × [Gross_Margin_Loss + LTV_Churn_Factor]) - Σ(Dispute_Fees)`
  - **Dispute Win Rate**: % of auto-responded disputes won vs industry average (~30%)
- **Validation methodology** (judges will love this):
  - **Temporal split** (NOT random k-fold — random splits leak future patterns)
  - Train on months 1–3 → Purge 14 days → Test on month 4
  - Report metrics on **mature cohorts** (>90 days old) to account for label settlement latency
  - Per-segment slicing: by payment method, ticket size, account age
- **Calibration plot**: Are our confidence scores well-calibrated?

#### [NEW] `src/evaluation/report_generator.py`
- Auto-generate a PDF evaluation report with charts
- Include confidence intervals on all metrics
- Show where the model fails (specific fraud types, edge cases)

---

### Component 6: Failure Recovery System

> [!CAUTION]
> This is a scored evaluation criterion. We build failure handling INTO the architecture, not as an afterthought.

#### [NEW] `src/resilience/failure_log.py`
- Structured failure logging with categories:
  - `DATA_QUALITY`: Missing fields, malformed inputs
  - `MODEL_FAILURE`: Low confidence predictions, model timeout
  - `API_FAILURE`: Razorpay API errors, rate limits, webhook delivery failures
  - `LLM_FAILURE`: LLM API down, hallucinated content detected, token limit exceeded
- Each failure logged with: timestamp, category, input, expected_output, actual_output, recovery_action

#### [NEW] `src/resilience/fallback.py`
- **LLM fallback**: If LLM API fails → use template-only response (no narrative)
- **Model fallback**: If ML model fails → use rule-based scoring (velocity + amount thresholds)
- **API fallback**: If Razorpay API fails → queue for retry with exponential backoff
- **Data fallback**: If evidence incomplete → partial response with confidence discount

---

## Tech Stack

| Layer | Technology | Why (AI Judgment) |
|-------|-----------|-------------------|
| Backend | **FastAPI** (Python) | Async, fast, typed — right tool for webhooks |
| ML | **XGBoost + Isolation Forest** | Interpretable, proven on tabular fraud data |
| Graph | **NetworkX** | Lightweight ring detection, no GPU needed |
| LLM | **Gemini API** | Evidence narrative generation only |
| Spike Detection | **SciPy (CUSUM)** | Statistical, not AI — deliberate choice |
| Data | **Pandas + Synthetic** | Realistic test data with known labels |
| Dashboard | **Jinja2 HTML + HTMX** | Minimal, fast, no React complexity needed |
| Metrics | **scikit-learn + matplotlib** | Standard, reproducible evaluation |
| Testing | **pytest** | Unit + integration tests on critical paths |

---

## Directory Structure

```
riskshield-ai/
├── README.md                    # Clear setup + architecture doc
├── requirements.txt
├── pyproject.toml
├── .env.example
├── src/
│   ├── __init__.py
│   ├── config.py                # Configuration management
│   ├── data/
│   │   ├── synthetic_generator.py   # Generate realistic fraud data
│   │   ├── chargeback_cases.py      # Generate dispute test cases
│   │   └── razorpay_schemas.py      # Razorpay API response schemas
│   ├── risk/
│   │   ├── scorer.py                # XGBoost + Isolation Forest ensemble
│   │   ├── features.py              # Feature engineering pipeline
│   │   ├── spike_detector.py        # CUSUM-based spike detection
│   │   └── ring_detector.py         # NetworkX graph analysis
│   ├── chargeback/
│   │   ├── evidence_collector.py    # Gather evidence from APIs
│   │   ├── narrative_generator.py   # LLM-powered narrative
│   │   ├── response_builder.py      # Compile dispute response
│   │   ├── visa_ce3.py              # Visa Compelling Evidence 3.0 engine
│   │   └── win_predictor.py         # Win-rate prediction model
│   ├── razorpay/
│   │   ├── client.py                # Razorpay API wrapper (test mode)
│   │   └── mock_webhooks.py         # Webhook simulator for testing
│   ├── api/
│   │   ├── main.py                  # FastAPI app
│   │   ├── routes.py                # API endpoints
│   │   └── webhooks.py              # Webhook handlers + HMAC verification
│   ├── frontend/
│   │   ├── templates/
│   │   │   ├── dashboard.html       # Main dashboard
│   │   │   ├── disputes.html        # Dispute manager
│   │   │   └── metrics.html         # Metrics panel
│   │   └── static/
│   ├── evaluation/
│   │   ├── metrics.py               # PR-AUC, insult rate, FP cost
│   │   └── report_generator.py      # Auto-generate eval report
│   └── resilience/
│       ├── failure_log.py           # Structured failure logging
│       └── fallback.py              # Graceful degradation
├── tests/
│   ├── test_scorer.py
│   ├── test_evidence.py
│   ├── test_narrative.py
│   ├── test_spike_detector.py
│   └── test_visa_ce3.py             # Test CE3.0 matching logic
├── data/
│   ├── synthetic_transactions.json  # Generated test data
│   ├── chargeback_cases.json        # Generated dispute cases
│   └── evaluation_results/          # Metrics output
├── docs/
│   ├── ARCHITECTURE.md              # System design document
│   ├── AI_JUDGMENT.md               # Where we used AI vs not + why
│   ├── FAILURE_LOG.md               # What broke and how we fixed it
│   └── METRICS.md                   # Evaluation methodology
└── scripts/
    ├── generate_data.py             # Run data generation
    ├── train_models.py              # Train risk scorer
    ├── evaluate.py                  # Run full evaluation
    └── demo.py                      # End-to-end demo script
```

---

## Competitive Edge Strategy

### Edge 1: "AI Judgment" Document
Create `docs/AI_JUDGMENT.md` that explicitly lists:

| Decision | Used AI? | Why / Why Not |
|----------|----------|---------------|
| Risk scoring | ✅ XGBoost | Tabular data, needs interpretability for financial decisions |
| Anomaly detection | ✅ Isolation Forest | Catches novel fraud without labels |
| Evidence narrative | ✅ Gemini LLM | Natural language generation is LLM's sweet spot |
| Spike detection | ❌ CUSUM | Statistical method is more reliable, less prone to false alerts |
| Velocity checks | ❌ Rule-based | Deterministic thresholds are more trustworthy for real-time blocking |
| Ring detection | ✅ Graph + heuristics | Graph algorithms + manual threshold, not GNN (overkill) |
| Evidence facts | ❌ Direct API data | Never let AI generate factual claims about transactions |
| Win prediction | ✅ Logistic Regression | Simple, interpretable, sufficient for binary classification |

### Edge 2: "What Broke" Document
Pre-document failures as we build:
- "LLM hallucinated a delivery date that didn't exist → Added fact-checking layer"
- "XGBoost overfit on synthetic data → Added stratified cross-validation"
- "Webhook handler crashed on malformed payloads → Added schema validation + fallback"

### Edge 3: Business Impact Metrics
Don't just show precision/recall. Show:
- **₹ saved per dispute** (avg chargeback amount × win rate improvement)
- **Time saved** (automated evidence < 30 seconds vs 2-3 hours manual)
- **FP cost transparency** (we'd rather miss 2% of fraud than block 10% of good customers)

### Edge 4: Defense-Only Architecture
The hackathon says: *"Strictly defense-only: anything offense-capable is disqualified."*
- No data about attack techniques
- No adversarial examples
- No tools that could be repurposed for fraud
- Document this explicitly in README

---

## Verification Plan

### Automated Tests
```bash
# Unit tests
pytest tests/ -v --cov=src --cov-report=html

# Integration test — full pipeline
python scripts/demo.py --full-pipeline

# Evaluation metrics
python scripts/evaluate.py --output data/evaluation_results/
```

### Manual Verification
- Run the dashboard locally and verify all views render
- Submit a test dispute and verify evidence package generation
- Trigger a fraud spike and verify alert generation
- Review the generated evaluation report for completeness

### Deliverables Checklist
- [ ] Public GitHub repo with clean README
- [ ] Working demo (run locally with one command)
- [ ] 5-min pitch video showing: problem → architecture → demo → metrics → failures
- [ ] Measured precision/recall on held-out test set
- [ ] AI Judgment document
- [ ] Failure recovery documentation

---

## Open Questions

> [!IMPORTANT]
> **Q1: LLM Provider** — Should we use Google Gemini API (free tier available) or OpenAI? Gemini gives us a Razorpay/Google alignment story. I recommend **Gemini**.

> [!IMPORTANT]  
> **Q2: Scope Confirmation** — The plan covers both a Chargeback Auto-Responder AND a Fraud Spike Detector. Should we focus on just one to go deeper, or keep both for breadth? I recommend **keeping both** — they're complementary and show range.

> [!IMPORTANT]
> **Q3: Frontend Complexity** — Should we use a simple Jinja2+HTMX dashboard or a full React frontend? I recommend **Jinja2+HTMX** — simpler, faster to build, shows AI judgment (don't over-engineer the UI when the ML is the star).

> [!IMPORTANT]
> **Q4: Video Strategy** — For the 5-min pitch video, I recommend this structure:
> - 0:00–0:30 → The problem (chargebacks cost ₹10K Cr/year)
> - 0:30–1:30 → Architecture + AI judgment decisions
> - 1:30–3:30 → Live demo (webhook → risk score → evidence → response)
> - 3:30–4:30 → Metrics (precision/recall + business impact ₹)
> - 4:30–5:00 → What broke and how we fixed it
> 
> Does this flow work for you?

---

## Timeline Estimate

| Phase | Time | Deliverable |
|-------|------|-------------|
| 1. Data Generation | 2 hours | Synthetic transactions + chargeback cases |
| 2. Risk Scorer | 3 hours | XGBoost + Isolation Forest + evaluation |
| 3. Chargeback Responder | 3 hours | Evidence collector + LLM narrative |
| 4. Dashboard | 2 hours | FastAPI + Jinja2 dashboard |
| 5. Spike Detector + Ring Detection | 2 hours | CUSUM + NetworkX |
| 6. Evaluation + Metrics | 1 hour | Full evaluation report |
| 7. Failure Log + AI Judgment Docs | 1 hour | Documentation |
| 8. Testing + Polish | 1 hour | Tests, README, cleanup |
| **Total** | **~15 hours** | **Complete submission** |
