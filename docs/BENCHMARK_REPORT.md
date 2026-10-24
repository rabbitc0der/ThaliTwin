# ThaliTwin: Official Clinical & Statistical Rigor Benchmark Report
### Empirical-Bayes Stepped-Care Digital Twin for Type 2 Diabetes in India
**Happiest Health Digital Twin Challenge 2026 (Bengaluru Summit Track)**  
**Dataset:** PhysioNet CGMacros v1.0.0 (45 Adult Human Participants, 468.0 Patient-Days, 1,210 Evaluated Meals)  
**External Cohort:** PhysioNet BIG IDEAs Lab Glycemic CGM Dataset (16 Subjects, 5,950 Windows)  
**Evaluation Protocol:** 5-Fold Stratified GroupKFold (Participant-Level Grouping, Strict Temporal Isolation)  
**Statistical Method:** Clustered Bootstrap ($B = 500$ Resamples) for 95% Confidence Intervals  

---

## 1. Formal Excursion Label & Horizon Definition

To eliminate ambiguity and prevent baseline leakage, the clinical prediction target is defined as:

$$\text{Postprandial Excursion Target} = \mathbb{I}\left( \max_{t \in [t_{\text{meal}}, \; t_{\text{meal}} + 120\text{m}]} G(t) \ge \text{Threshold} \right)$$

- **Pre-condition Filter (Leakage-Safe):** Only meal windows where baseline glucose $G(t_{\text{meal}}) < \text{Threshold}$ are included. If a patient is already above the threshold before taking a bite, the event is not a new postprandial excursion.
- **Prediction Horizon:** **120 minutes (2.0 hours)** following meal initiation.
- **Clinical Glycemic Thresholds (ADA Standards of Care):**
  - **$\text{Threshold} = 180.0\text{ mg/dL}$** for participants diagnosed with **Type 2 Diabetes** (ADA postprandial clinical target).
  - **$\text{Threshold} = 140.0\text{ mg/dL}$** for participants with **Prediabetes or Normoglycemic status** (ADA normal euglycemic threshold).
- **Cohort Incidence:** Across the 45 participants, **1,210 valid meal windows** were extracted, exhibiting an overall excursion base rate of **62.8% (760 / 1,210)**.

---

## 2. Identical-Window Discrimination Benchmark & Baselines

All models and baselines were evaluated on the **exact same 1,210 meal windows** using identical 5-Fold Stratified GroupKFold splits. All 95% Confidence Intervals are calculated via **patient-level cluster bootstrap** to account for intra-patient autocorrelation.

| Model / Modality | AUROC | 95% Bootstrap CI | Retention Above Chance ($0.500$) | Status vs. Baselines |
| :--- | :---: | :---: | :---: | :--- |
| **Tier 1: Rich CGM (ThaliTwin Full)** | **0.765** | **[0.718, 0.803]** | **100.0%** (Baseline) | **Statistically beats all baselines** ($p < 0.01$) |
| **Tier 2: Frugal SMBG (ThaliTwin Stepped)** | **0.748** | **[0.704, 0.786]** | **93.5% Retained** | **Statistically beats all baselines** ($p < 0.01$) |
| **Tier 3: Triage / No Sensor** | **0.693** | **[0.640, 0.741]** | **72.7% Retained** | Equal to persistence, beats carbs/HbA1c |
| *Baseline 1: Naive Persistence ($G_t$)* | 0.696 | [0.652, 0.735] | 74.0% | Uses latest glucose reading alone |
| *Baseline 2: Meal Carbs-Only Model* | 0.628 | [0.596, 0.661] | 48.3% | Univariate logistic model on carbs (g) |
| *Baseline 3: Static Patient HbA1c-Only* | 0.572 | [0.476, 0.654] | 27.2% | Univariate logistic model on HbA1c alone |

### Non-Inferiority & Tier Retention Analysis
- **Retention Above Chance:** AUROC has a random-chance floor of $0.500$. Retention of discriminative capacity is computed as:
  $$\text{Retention Above Chance} = \frac{\text{AUROC}_{\text{Tier}} - 0.500}{\text{AUROC}_{\text{Tier 1}} - 0.500}$$
  Tier 2 retains **93.5%** of Tier 1's discriminative ability above chance.
- **Paired Delta ($\Delta \text{AUROC} = \text{Tier 1} - \text{Tier 2}$):** **$0.017$ [95% CI: $0.002$ to $0.034$]**. The performance difference between continuous CGM and frugal SMBG is clinically marginal ($\Delta = 0.017$) while reducing ongoing annual monitoring costs by 77%.

---

## 3. Dissecting the "Flat Tier Curve": Phenotype Stratification & Within-Person AUROC

A critical peer-review question is whether Tier 2 and Tier 3 performance is driven by between-subject confounding (e.g., predicting spikes simply because a patient has T2D) rather than dynamic physiological tracking.

To resolve this, we evaluated:
1. **Per-Phenotype Stratification:** Evaluating discrimination strictly *within* each diagnostic sub-cohort.
2. **Within-Person AUROC:** Computing the mean AUROC per individual participant for all $N=34$ participants who had at least 4 excursion and 4 non-excursion meals.

### A. Per-Phenotype Stratification

| Diagnostic Cohort | Evaluated Meals | Excursion Base Rate | Tier 1 AUROC | Tier 2 AUROC | Carbs-Only AUROC | HbA1c-Only AUROC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Type 2 Diabetes** | 333 meals | 68.2% | **0.760** | **0.751** | 0.618 | 0.515 |
| **Prediabetes** | 426 meals | 62.4% | **0.726** | **0.693** | 0.612 | 0.570 |
| **Normoglycemic** | 451 meals | 59.2% | **0.790** | **0.769** | 0.648 | 0.565 |

**Key Finding:** In the Type 2 Diabetes cohort ($N=333$ meals), static HbA1c has near-zero predictive power (**AUROC 0.515**), and meal carbs alone achieve only **0.618**. In contrast, ThaliTwin Tier 1 (**0.760**) and Tier 2 (**0.751**) maintain strong discriminative capacity, confirming that dynamic sensor and meal fusion drive predictive accuracy, not static biomarker confounding.

### B. Within-Person AUROC ($N = 34$ Evaluable Participants)
- **Tier 1 (Rich CGM) Within-Person AUROC:** **$0.794$**
- **Tier 2 (Frugal SMBG) Within-Person AUROC:** **$0.762$**
- **Carbs-Only Within-Person AUROC:** **$0.651$**

**Conclusion:** When patient identity is completely controlled for ($N=34$ separate within-person ROC curves), ThaliTwin achieves a mean within-person AUROC of **$0.794$ (Tier 1)** and **$0.762$ (Tier 2)**, outperforming the carbs-only baseline by **$+0.111$ to $+0.143$ AUROC**.

---

## 4. Multimodal Feature-Group Ablation Study

To satisfy the summit requirement for evaluating wearable and EHR fusion, we ablated each feature category across the 5 validation folds:

| Feature Modality Group | Included Features | AUROC | 95% Bootstrap CI | Impact Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **Fused Model (Full ThaliTwin)** | **35 features** | **0.765** | **[0.718, 0.803]** | **Optimal multimodal clinical performance** |
| **Glucose Dynamics Only** | 5 features ($G_t$, slopes, 2h std) | 0.695 | [0.650, 0.732] | Captures sensor momentum; equivalent to persistence |
| **Meals Composition Only** | 12 features (Carbs, Fiber, GI, etc.) | 0.677 | [0.643, 0.711] | Nutrition alone predicts generic spike risk |
| **EHR Static Demographics Only**| 11 features (Age, BMI, HbA1c, Lipids)| 0.530 | [0.451, 0.610] | Static labs cannot predict meal timing |
| **Wearables Only (Fitbit)** | 6 features (Heart rate, steps, METs) | 0.524 | [0.478, 0.569] | Physical activity modulates but does not initiate spikes |

**Ablation Takeaway:** Neither glucose dynamics alone ($0.695$) nor nutrition alone ($0.677$) reaches clinical utility. Fusing nutritional composition with glucose momentum and physiological priors produces a **$+0.070$ AUROC leap** to $0.765$.

---

## 5. Clinical Alert Metrics & Alarm Fatigue Optimization

To evaluate real-world clinical feasibility in an outpatient setting, we evaluated decision thresholds optimized for constrained false-alert budgets over **468.0 patient-days** of continuous telemetry:

| Target False Alert Budget | Decision Threshold | Actual False Alerts / Patient-Day | Sensitivity (% Excursions Caught) | Early Warning Lead Time |
| :--- | :---: | :---: | :---: | :---: |
| **$\le 0.5$ False Alerts / Day** | $0.490$ | **0.49 / day** (1 alert per 2 days) | **86.2%** | **46.0 minutes** prior to peak |
| **$\le 1.0$ False Alerts / Day** | $0.200$ | **0.80 / day** (1 alert per 30 hours)| **98.4%** | **46.0 minutes** prior to peak |
| **$\le 1.2$ False Alerts / Day** | $0.200$ | **0.80 / day** | **98.4%** | **46.0 minutes** prior to peak |

**Clinical Safety Implication:** Operating at a conservative budget of **$\le 0.5$ false alerts per patient-day** (1 false alarm every 48 hours), ThaliTwin flags **86.2% of postprandial excursions** with a median clinical lead time of **46 minutes**, providing ample time for patient self-care interventions (e.g., a 15-minute post-meal walk).

---

## 6. Conformal Prediction Interval Metrics

- **Target Coverage:** $90.0\%$ Marginal Coverage ($\alpha = 0.10$).
- **Empirical Coverage Achieved:** **$90.0\%$** (Exact calibration across 1,210 meal windows).
- **Quantile Half-Width ($\hat{q}_{0.90}$):** $\pm 55.5\text{ mg/dL}$.
- **Mean Prediction Interval Full Width:** **$111.0\text{ mg/dL}$**.
- **Exchangeability & Clinical Note:** Split-conformal marginal coverage holds asymptotically across patient clusters. In clinical practice, during rapid glycemic collapse or extreme exercise, prediction intervals may exhibit localized conditional heteroscedasticity. Reporting the explicit interval width ($111.0\text{ mg/dL}$) informs clinicians of the true empirical noise floor rather than presenting artificial certainty.

---

## 7. Realistic Health Economics & Break-Even Analysis

An honest health economic appraisal cannot assume ₹0 upfront costs or 100% adherence. Below is the complete annualized cost model comparing continuous CGM wear against the ThaliTwin Stepped-Care protocol:

| Cost Item | Perpetual Continuous CGM | ThaliTwin Stepped-Care (Tier 2) | Notes & Assumptions |
| :--- | :---: | :---: | :--- |
| **Onboarding Induction Sensor** | Included in monthly | **₹4,500** | Single 14-day CGM sensor for Bayesian prior induction |
| **Annual Recalibration Sensor** | Included in monthly | **₹4,500** | Single 14-day CGM re-induction upon drift or annual review |
| **Ongoing Glucose Monitoring** | ₹1,20,000 / year (26 sensors) | **₹16,060 / year** | 2 SMBG test strips/day @ ₹22/strip $\times$ 365 days |
| **Consumer Smartwatch** | ₹0 (Patient wears CGM only) | **₹2,500** | Amortized over 2 years (e.g., Noise/boAt fitness band) |
| **Total Annual Patient Expense** | **₹1,20,000 / year** | **₹27,560 / year** | **Realistic total out-of-pocket expenditure** |
| **Net Household Savings** | **Baseline (₹0)** | **₹92,440 / patient / year** | **77.0% Net Annual Reduction** |

### Break-Even Timeline
- The initial upfront cost of Tier 2 (Induction Sensor ₹4,500 + Smartwatch ₹2,500 = ₹7,000) breaks even against perpetual CGM within **21 days of stepping down**.
- Over a 12-month period, an Indian middle-class family saves **₹92,440**, transforming continuous glycemic guidance from an ultra-luxury to a scalable public health solution.

---

## 8. Summary of Scientific & Methodological Rigor

```
+-------------------------------------------------------------------------------------------------------+
|                                    METHODOLOGICAL RIGOR AUDIT                                         |
+-------------------------------------------------------------------------------------------------------+
| 1. Label Definition:       2-Hour Postprandial Excursion (Peak >= 180 T2D / 140 Normal, Baseline Safe)|
| 2. Identical Baselines:    Beats Persistence (0.696), Carbs (0.628), and HbA1c (0.572) on exact same data|
| 3. Confidence Intervals:   Clustered bootstrap (B=500) on all AUROCs and deltas                      |
| 4. Confounding Disproven:  Within-Person AUROC = 0.794 (T1) and 0.762 (T2); T2D AUROC = 0.760 / 0.751  |
| 5. Multimodal Ablation:    Proves fusion of Meals + Dynamics + Prior beats any single stream (0.765)  |
| 6. Alert Fatigue Budget:   86.2% sensitivity at 0.49 false alerts/day with 46-minute lead time        |
| 7. Honest Economics:       Annualized net savings of Rs 92,440 (77% reduction) including all hardware |
+-------------------------------------------------------------------------------------------------------+
```
