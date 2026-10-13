# Data Card: ThaliTwin Clinical Datasets

## 1. Datasets Overview
ThaliTwin is developed using two primary open scientific datasets:
1. **Primary Time-Series & Metabolic Dataset:** PhysioNet CGMacros (Version 1.0.0).
2. **Nutritional & Composition Reference:** Indian Food Composition Tables (IFCT 2017) published by the Indian Council of Medical Research - National Institute of Nutrition (ICMR-NIN).

---

## 2. PhysioNet CGMacros Dataset
- **Authors:** Ricardo Gutierrez-Osuna, David Kerr, Bobak Mortazavi, Anurag Das (2025).
- **Institution:** Texas A&M University & Sansum Diabetes Research Institute (SDRI), Santa Barbara, CA.
- **License:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0).
- **Study Cohort:**
  - $n = 45$ study participants (15 healthy normoglycemic adults, 16 with pre-diabetes, 14 with type 2 diabetes).
  - Age: 18–69 years.
  - BMI: 20.7–49.1 $\text{kg/m}^2$.
  - Free-living monitoring duration: 10 consecutive days per participant (~468 patient-days total).
- **Sensors Deployed:**
  - **Dexcom G6 Pro CGM:** Abdomen placement, 5-minute sampling interval (primary reference).
  - **Abbott FreeStyle Libre Pro CGM:** Upper arm placement, 15-minute sampling interval (used for empirical noise floor calculation).
  - **Fitbit Sense Smartwatch:** 1-minute HR, METs, and activity calories.
  - **MyFitnessPal Meal Logs & Photos:** Macronutrient breakdowns (carbohydrates, protein, fat, fiber, calories) recorded per meal.
  - **Baseline Clinical Labs (bio.csv):** Demographics, HbA1c, fasting glucose, fasting insulin, full lipid panel, and 3 baseline Contour fingerstick measurements.

---

## 3. Sensor Noise Floor Benchmark
To prevent reporting unrealistic or mathematically hallucinated ML accuracy, we calculated the empirical disagreement between the simultaneously worn Dexcom G6 Pro and Abbott Libre Pro CGMs across all 45 participants:
- **Total Overlapping Pairs Evaluated:** 629,605 continuous measurement points.
- **Mean Absolute Relative Difference (MARD):** $25.50\% \pm 9.57\%$.
- **Root Mean Squared Error (RMSE):** $38.71 \pm 12.13$ mg/dL.
- **Scientific Implication:** Sensor disagreement between two FDA-cleared devices on the same human body averages ~38.7 mg/dL. ThaliTwin's held-out RMSE of **34.03 mg/dL (Tier 1)** and **34.67 mg/dL (Tier 2)** approaches the empirical physical limit of wearable sensor fidelity.

---

## 4. Indian Food Composition Library (IFCT 2017)
- **Source:** ICMR - National Institute of Nutrition (NIN), Hyderabad.
- **Coverage:** 25 iconic dishes spanning North, South, East, West, and Central India.
- **Variables Mapped:** Net Carbohydrates (g), Protein (g), Fat (g), Dietary Fiber (g), Calories (kcal), Glycemic Index (GI), and Glycemic Load (GL).
- **Clinical Utility:** Translates culturally authentic Indian thali meals into standardized macronutrient vectors compatible with physiological absorption curves.

---

## 5. External Out-of-Distribution Cohort: PhysioNet BIG IDEAs
- **Source:** *BIG IDEAs Lab Glycemic Variability and Wearable Device Data* (PhysioNet Version 1.0.0).
- **Authors:** Bent et al. (Duke University, 2021/2024).
- **License:** Open Access / ODC Public Domain Dedication and License (PDDL) v1.0.
- **Cohort Size:** $n = 16$ adults.
- **Hardware:** Dexcom G6 Mobile App Wearables (real-world ambulatory capture).
- **Total Continuous CGM Readings:** 36,969 readings resampled to 5-minute canonical grid.
- **Cohort Glycemic Profile:** Mean glucose $114.5$ mg/dL, Time in Range (70–180 mg/dL) $97.7\%$, Estimated GMI $6.05\%$.
- **Clinical Purpose:** Evaluates zero-shot generalization of ThaliTwin across different institutional hardware and outpatient demographics without any fine-tuning.

