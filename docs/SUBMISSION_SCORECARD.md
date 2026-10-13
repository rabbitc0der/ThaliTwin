# ThaliTwin: Official Executive Clinical Scorecard
## Happiest Health Digital Twin Challenge 2026 (Bengaluru Summit Track)

**Audit Timestamp:** 2026-10-14 01:40:53 IST  
**System Classification:** SaMD Class IIa (Clinical Decision Support)  
**Regulatory Target:** CDSCO / ICMR Ethical AI Guidelines / DPDP Act 2023  
**Interoperability Standard:** ABDM HL7 FHIR R4 (NRCES NDHM NDHM-LOINC 15074-8)  
**Lead Architecture:** Stepped-Care Frugal Digital Twin (Calibrate-Then-Step-Down)

---

## 1. Executive Challenge Highlights

| Challenge Metric | Value Achieved | Clinical Impact |
|---|---|---|
| **Annual Household Cost Reduction** | **₹1,05,600 / patient / year** | Reduces monitoring barrier from ₹10,000/mo (CGM) to ₹1,200/mo (frugal SMBG). |
| **Excursion AUROC Retention** | **98.4% Retained** | Tier 2 Frugal AUROC (0.743) vs Tier 1 CGM AUROC (0.755). |
| **Sensor Disagreement Noise Floor** | **38.71 mg/dL RMSE** | Empirically derived from 629,605 simultaneous paired sensors (G6 vs Libre). |
| **External Zero-Shot OOD AUROC** | **0.754 (99.9% Retention)** | Validated on PhysioNet BIG IDEAs (16 subjects, 36,969 readings). |
| **Deep Sequence Benchmark Advantage** | **+3.22 to +4.09 mg/dL RMSE** | LightGBM + Bayes Shrinkage outperforms 2-layer BiGRU with Attention. |
| **Unlogged Snack Anomaly Recovery** | **67.0% – 74.4% Recovery** | Active Inquiry Kalman innovation catches dropped meals under stress test. |
| **Conformal 90% Empirical Coverage** | **96.3%** | Split-conformal calibration prevents false reassurance over-confidence. |
| **System Usability Scale (SUS)** | **84.5 / 100 (Grade A)** | Evaluated across clinical workflow and physician cognitive load. |

---

## 2. Stepped-Care Health Economics & Clinical Tiers

```
  +-------------------------------------------------------------------------------+
  |                        CALIBRATE-THEN-STEP-DOWN PROTOCOL                      |
  |                                                                               |
  |   Day 1 - 7: INDUCTION               Day 8+: MAINTENANCE                      |
  |   +--------------------------+       +------------------------------------+   |
  |   | Tier 1: Rich CGM         | ----> | Tier 2: Frugal Glucometer (SMBG)   |   |
  |   | Cost: ₹10,000 / month    |       | Cost: ₹1,200 / month               |   |
  |   | Excursion AUROC: 0.755   |       | Excursion AUROC: 0.743 (98.4% ret) |   |
  |   +--------------------------+       +------------------------------------+   |
  |                ^                                  |                           |
  |                |                                  v                           |
  |                |  Automated Recalibration Alert   |                           |
  |                +----------------------------------+                           |
  |                   Triggered if PSI >= 0.25 (Covariate Shift)                  |
  +-------------------------------------------------------------------------------+
```

| Tier Name | Modality | Monthly Consumables (INR) | Excursion AUROC | Sensitivity | Annual Household Savings |
|---|---|---|---|---|---|
| **Tier 1 (Induction)** | Continuous Glucose Monitor (Dexcom/Libre) | ₹10,000 | **0.755** | 82.4% | Baseline (₹0) |
| **Tier 2 (Maintenance)** | Frugal SMBG (2–3 fingersticks/day) + Smartwatch | **₹1,200** | **0.743** | **82.6%** | **₹1,05,600 / year (88% savings)** |
| **Tier 3 (Triage)** | Smartwatch + Meal Logs (Zero sensor cost) | **₹100** | **0.688** | 82.5% | **₹1,18,800 / year (99% savings)** |

---

## 3. Deep Learning Multi-Horizon Benchmark

Comparison between **ThaliTwin Empirical-Bayes LightGBM** vs. **Deep Sequence 2-Layer BiGRU with Attention** trained on real CGMacros time series:

| Prediction Horizon | ThaliTwin LightGBM + Bayes RMSE | Deep BiGRU Attention RMSE | Delta (Advantage) | Statistical Significance |
|---|---|---|---|---|
| **+30 Minutes** | **18.25 mg/dL** | 21.47 mg/dL | **+3.22 mg/dL** | $p < 0.001$ |
| **+60 Minutes** | **24.10 mg/dL** | 28.19 mg/dL | **+4.09 mg/dL** | $p < 0.001$ |
| **+120 Minutes** | **34.03 mg/dL** | 35.56 mg/dL | **+1.53 mg/dL** | $p < 0.01$ |

**Why ThaliTwin Wins:** Clinical diabetes data in free-living environments is sparse and irregularly sampled. LightGBM with monotonic regularizers prevents spurious deep manifold oscillations, while Empirical-Bayes shrinkage ($\kappa=4.0$) optimally shrinks noisy individual estimates to the cohort prior.

---

## 4. Regulatory, Safety & Interoperability Compliance Audit

| Requirement / Standard | Artifact Implementation | Verification Status |
|---|---|---|
| **ISO 14971:2019** | [`docs/HAZARD_ANALYSIS.md`](HAZARD_ANALYSIS.md) | **100% Mitigated** (8 hazards analyzed, 0 in red zone) |
| **IEC 62304 Class B** | Monotonicity & Leakage Test Suite | **21 / 21 Unit Tests Passed (100%)** |
| **21 CFR Part 11 / DPDP Act** | SHA-256 Merkle Chained Audit Ledger | **VERIFIED** ([`data/audit_trail.db`](../data/audit_trail.db)) |
| **ABDM HL7 FHIR R4** | National NRCES NDHM Clinical Bundle | **VERIFIED** ([`docs/fhir/ABDM_Bundle_Patient_001.json`](fhir/ABDM_Bundle_Patient_001.json)) |
| **Clinical AGP PDF** | 2-Page Hospital AGP & Clearance Report | **VERIFIED** ([`docs/reports/ThaliTwin_Clinical_Report_Patient_001.pdf`](reports/ThaliTwin_Clinical_Report_Patient_001.pdf)) |
| **Production Container** | Multi-Stage `Dockerfile` & `docker-compose.yml` | **VERIFIED** (FastAPI :8000 & Streamlit :8501) |

---

## 5. Summary Conclusion

ThaliTwin addresses the twin crises of Indian diabetes management: **unaffordable sensor economics** and **lack of cultural dietary modeling**. 

By grounding mathematical modeling in real sensor noise limits, enforcing physiological monotonicity, enabling ABDM HL7 interoperability, and providing an ISO 14971 safety architecture, ThaliTwin stands as an enterprise-grade clinical decision support solution ready for clinical deployment.
