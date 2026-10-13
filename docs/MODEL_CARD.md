# Model Card: ThaliTwin Personalization & Excursion Forecaster

## 1. Model Overview
- **Model Name:** ThaliTwin (Stepped-Care Digital Twin Engine)
- **Version:** 1.0.0
- **Authors:** Team ThaliTwin
- **Event:** Happiest Health Digital Twin Challenge 2026 (Reimagining & Reforming Healthcare in India Summit)
- **Primary Objective:** Forecast postprandial glycemic excursions ($\ge 180$ mg/dL for T2D, $\ge 140$ mg/dL for normoglycemic) within 120 minutes of meal intake, predict postprandial peak rise ($\Delta G$), and enable dietary/lifestyle counterfactual simulations under a **frugal stepped-care sensor protocol**.

---

## 2. Architecture & Algorithms
ThaliTwin integrates three symbiotic modeling tiers:
1. **Population Base Models:**
   - **Excursion Risk Classifier:** LightGBM gradient-boosted decision trees (`n_estimators=120`, `max_depth=4`, `num_leaves=14`, `subsample=0.8`).
   - **Peak Rise & Trajectory Forecaster:** LightGBM regressor with **physiological monotonic constraints** (`carbs_g: +1`, `fiber_g: -1`, `post_meal_activity: -1`).
2. **Empirical-Bayes Shrinkage Personalization:**
   - Computes individual metabolic offsets $\theta_i^* = w_i \cdot \bar{Y}_i + (1 - w_i) \cdot \mu_{\text{pop}}$, where shrinkage weight $w_i = \frac{n_i}{n_i + \kappa}$ ($\kappa = 4.0$).
   - As observed meals accumulate during early calibration days ($N=0, 2, 4, 7$), the twin smoothly transitions from population EHR prior to individual metabolic sensitivity.
3. **Trust & Uncertainty Layer:**
   - **Split-Conformal Prediction:** Delivers finite-sample $90\%$ prediction intervals $[\hat{Y} - \hat{q}, \hat{Y} + \hat{q}]$ calibrated on held-out participants.
   - **Isotonic Calibration:** Mitigates risk overconfidence to maintain reliable clinical probability estimates.
   - **Alert Budget Optimization:** Sweeps decision thresholds to enforce $\le 1.0$ false alert per patient-day.

---

## 3. Data & Training Scheme
- **Training Dataset:** PhysioNet CGMacros open dataset ($n=45$ adults, 468 total patient-days, 1,210 debounced meal windows).
- **Cross-Validation:** 5-Fold Stratified GroupKFold (grouping strictly by `subject_id`). Zero participant overlap between train and validation splits.
- **Leakage Prevention:** 
  - Strictly past-only features at time $t$. 
  - Verified by unit tests ([`tests/test_leakage.py`](../tests/test_leakage.py)) with future data corruption and truncation invariance checks.
  - Evaluation windows only included when baseline glucose $G(t) < \text{threshold}$.

---

## 4. Empirical Performance Across Stepped-Care Tiers

| Metric | Tier 1 (Rich CGM) | Tier 2 (Frugal SMBG) | Tier 3 (Triage Fitbit) | Persistence Baseline | Sensor Noise Floor |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Monthly Patient Cost (INR)** | ₹10,000 | ₹1,200 | ₹0 | - | - |
| **Excursion AUROC** | **0.755** | **0.743** | **0.688** | 0.500 | - |
| **Excursion AUPRC** | **0.804** | **0.800** | **0.752** | 0.520 | - |
| **Excursion Sensitivity** | **0.824** | **0.826** | **0.825** | - | - |
| **Peak Rise RMSE (mg/dL)** | **34.03** | **34.67** | **34.74** | 67.59 | **38.71** |
| **Conformal 90% Band** | $\pm 55.48$ mg/dL | $\pm 56.48$ mg/dL | $\pm 55.98$ mg/dL | - | - |
| **Relative AUROC Retained** | 100.0% | **98.4%** | 91.1% | - | - |
| **Monthly Cost Savings** | 0% | **88.0%** | 99.0% | - | - |

---

## 5. Personalization Learning Curve
Held-out peak rise RMSE drops monotonically as calibration meals accumulate:
- **Day 0 (Population Prior):** $44.01 \pm 22.77$ mg/dL
- **Day 2 (Early Calibration):** $35.61 \pm 13.45$ mg/dL
- **Day 4 (Shrinkage Adaptation):** $32.05 \pm 14.19$ mg/dL
- **Day 7 (Full Personalization):** $30.51 \pm 12.11$ mg/dL

---

## 6. Limitations & Clinical Safety Bounds
1. **Decision Support Only:** ThaliTwin is an investigational research prototype for clinician decision support; it is not an autonomous medical device or closed-loop insulin controller.
2. **Associational What-If Simulations:** Counterfactual meal forecasts are associational, guarded by monotonicity constraints and domain bounds.
3. **Abstention Policy:** The twin abstains from predictions if meal carbohydrates exceed $140$ g or if last fingerstick staleness exceeds $300$ minutes.
