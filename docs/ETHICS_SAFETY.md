# Ethics, Safety & Regulatory Architecture: ThaliTwin

## 1. Regulatory Context & DPDP Act Posture
ThaliTwin is developed in alignment with the **Digital Personal Data Protection Act (DPDP Act 2023, India)** and ethical guidelines for AI in healthcare formulated by ICMR:
1. **De-Identified Open Scientific Data Only:** The model was trained and evaluated exclusively on publicly accessible, de-identified research data from the PhysioNet CGMacros study (Advarra IRB Pro00049227). All dates are time-shifted by $\pm 365$–720 days per HIPAA regulations.
2. **Zero Indian Citizen Protected Health Information (PHI):** No identifiable personal or health data of Indian citizens was processed during model development.
3. **Clinical Decision Support Stance:** ThaliTwin is explicitly classified as an **Investigational Clinical Decision Support (CDS) System**, intended for licensed physicians and endocrinologists. It does **not** autonomously dispense insulin, alter medication dosages, or replace physician judgment.

---

## 2. Alarm Fatigue Mitigation Architecture
A major failure mode in digital health is clinical alarm fatigue. In competing systems, up to 81% of patients trigger alerts, leading physicians to ignore the system entirely.
- **Alert Budget Guarantee:** The decision threshold is tuned to cap false alarms at **$\le 1.0$ false alert per patient-day**.
- **10-Minute Confirmation Window:** Fleeting transient sensor spikes do not trigger alerts; a continuous 10-minute confirmation is required.
- **60-Minute Postprandial Snooze:** Once an alert fires after a meal, alerts are suppressed for 60 minutes to prevent alert storms while normal digestion unfolds.

---

## 3. Applicability Domain Guard & Abstention Policy
To protect patient safety, ThaliTwin enforces an automated **Abstention Policy**:
- **Outlier Meal Detection:** If a planned meal contains $> 140$ g of carbohydrates (exceeding physiological absorption assumptions), the twin flags: *"CAUTION: Unusually high carbohydrate intake. Exceeds reliable linear metabolic range."*
- **Stale Sensor Guard:** In Tier 2 (Frugal SMBG), if more than 300 minutes (5 hours) elapse without a fingerstick reading, the twin degrades confidence and prompts for an active fingerstick reading before forecasting.
- **Uncertainty Bandwidth Guard:** If the split-conformal 90% uncertainty ribbon exceeds 70 mg/dL, the twin abstains from point recommendations.

---

## 4. Monotonicity Guarantees for Counterfactual Safety
Hallucinations in health models can be fatal (e.g. recommending eating more sugar to lower glucose). ThaliTwin strictly enforces **physiological monotonicity constraints**:
$$\frac{\partial \hat{Y}_{\text{peak}}}{\partial \text{Carbs}} \ge 0, \quad \frac{\partial \hat{Y}_{\text{peak}}}{\partial \text{Fiber}} \le 0, \quad \frac{\partial \hat{Y}_{\text{peak}}}{\partial \text{Activity}} \le 0$$
These constraints are mathematically verified by automated unit tests ([`tests/test_monotonicity.py`](../tests/test_monotonicity.py)).
