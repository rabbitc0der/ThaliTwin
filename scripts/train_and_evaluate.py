"""
train_and_evaluate.py
End-to-End Leakage-Free Training, Calibration, GroupKFold Cross-Validation,
and Stepped-Care Experiment Runner for ThaliTwin.

Saves authoritative metrics to results/metrics.json and results/stepped_care_comparison.csv.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from thalitwin.data_loader import load_bio_metadata, load_participant_timeseries, extract_meal_windows, compute_sensor_noise_floor
from thalitwin.tiers import TierEmulator
from thalitwin.features import extract_row_features, FEATURE_COLUMNS
from thalitwin.models import ExcursionClassifier, TrajectoryForecaster, BaselinePersistence, BaselineCarbsLinear
from thalitwin.twin import SteppedCareTwinEngine
from thalitwin.trust import ConformalIntervalEngine, IsotonicRiskCalibrator, compute_expected_calibration_error, AlertBudgetOptimizer
from thalitwin.metrics import evaluate_classification_metrics, evaluate_regression_metrics, compute_performance_per_rupee

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")

def build_cohort_dataset(max_participants: int = 45):
    """
    Extracts all meal windows and features across T1, T2, and T3 for all participants.
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)
    bio = load_bio_metadata()
    emulator = TierEmulator(random_seed=42)
    
    print(f"Building cohort dataset for up to {max_participants} participants...")
    
    all_meals = []
    t1_features = []
    t2_features = []
    t3_features = []
    
    subjects_processed = 0
    total_days = 0.0
    
    for idx, bio_row in bio.iterrows():
        pid = int(bio_row["subject_id"])
        try:
            df_5min = load_participant_timeseries(pid)
        except Exception as e:
            continue
            
        # Emulate tiers
        df_t1 = emulator.emulate_tier1_rich(df_5min)
        df_t2 = emulator.emulate_tier2_frugal(df_5min, schedule_type="clinical_standard", noise_std=0.07)
        df_t3 = emulator.emulate_tier3_triage(df_5min)
        
        # Calculate days monitored
        n_days = (df_5min["Timestamp"].max() - df_5min["Timestamp"].min()).total_seconds() / 86400.0
        total_days += n_days
        
        # Extract meal windows on primary stream
        meals = extract_meal_windows(df_t1, bio_row["phenotype"])
        if not meals:
            continue
            
        for m in meals:
            m_idx = m["row_index"]
            # Extract features for each tier strictly at time m_idx
            f1 = extract_row_features(df_t1, m_idx, bio_row, tier="T1_Rich")
            f2 = extract_row_features(df_t2, m_idx, bio_row, tier="T2_Frugal")
            f3 = extract_row_features(df_t3, m_idx, bio_row, tier="T3_Triage")
            
            all_meals.append(m)
            t1_features.append(f1)
            t2_features.append(f2)
            t3_features.append(f3)
            
        subjects_processed += 1
        if subjects_processed >= max_participants:
            break
            
    df_meals = pd.DataFrame(all_meals)
    df_t1 = pd.DataFrame(t1_features)
    df_t2 = pd.DataFrame(t2_features)
    df_t3 = pd.DataFrame(t3_features)
    
    print(f"Successfully processed {subjects_processed} participants.")
    print(f"Total valid meal windows extracted: {len(df_meals)}")
    print(f"Total patient-days evaluated: {total_days:.1f}")
    
    return df_meals, df_t1, df_t2, df_t3, total_days

def run_group_kfold_evaluation(df_meals, df_features, tier_name: str, total_days: float):
    """
    Performs 5-Fold Stratified GroupKFold (grouped by subject_id).
    Guarantees no patient appears in both train and validation folds.
    """
    sgkf = StratifiedGroupKFold(n_splits=5)
    groups = df_meals["subject_id"].values
    y_excursion = df_meals["is_excursion"].values
    y_peak_rise = df_meals["peak_rise"].values
    
    oof_probs = np.zeros(len(df_meals))
    oof_peak_preds = np.zeros(len(df_meals))
    
    conformal_residuals = []
    
    for fold, (train_idx, val_idx) in enumerate(sgkf.split(df_features, y_excursion, groups=groups)):
        X_tr, y_exc_tr, y_peak_tr = df_features.iloc[train_idx], y_excursion[train_idx], y_peak_rise[train_idx]
        X_val, y_exc_val, y_peak_val = df_features.iloc[val_idx], y_excursion[val_idx], y_peak_rise[val_idx]
        
        # Fit classifier
        clf = ExcursionClassifier(random_state=42 + fold)
        clf.fit(X_tr, y_exc_tr)
        val_probs = clf.predict_proba(X_val)
        
        # Calibrate with isotonic regression
        iso = IsotonicRiskCalibrator()
        iso.fit(clf.predict_proba(X_tr), y_exc_tr)
        oof_probs[val_idx] = iso.calibrate(val_probs)
        
        # Fit regressor
        reg = TrajectoryForecaster(target_name="peak_rise", enforce_monotonicity=True, random_state=42 + fold)
        reg.fit(X_tr, y_peak_tr)
        val_peak_pred = reg.predict(X_val)
        oof_peak_preds[val_idx] = val_peak_pred
        
        # Conformal residuals
        conformal_residuals.extend(np.abs(y_peak_val - val_peak_pred))
        
    # Classification metrics
    clf_metrics = evaluate_classification_metrics(y_excursion, oof_probs, threshold=0.5)
    ece = compute_expected_calibration_error(y_excursion, oof_probs, n_bins=10)
    clf_metrics["ece"] = round(ece, 4)
    
    # Alert budget optimization (target <= 1 false alert per patient-day)
    alert_opt = AlertBudgetOptimizer(target_max_false_alerts_per_day=1.0)
    alert_res = alert_opt.optimize(y_excursion, oof_probs, total_patient_days=total_days)
    
    # Regression metrics
    reg_metrics = evaluate_regression_metrics(y_peak_rise, oof_peak_preds)
    
    # Conformal 90% quantile
    q90 = float(np.quantile(conformal_residuals, 0.90))
    
    return {
        "tier": tier_name,
        "classification": clf_metrics,
        "optimal_alert_threshold": alert_res["optimal_threshold"],
        "regression": reg_metrics,
        "conformal_q90": round(q90, 2),
        "oof_probs": oof_probs.tolist(),
        "oof_peak_preds": oof_peak_preds.tolist()
    }

def evaluate_empirical_learning_curve(df_meals, df_t1, df_t2):
    """
    Evaluates empirical-Bayes shrinkage learning curve as calibration days increase (N = 0, 2, 4, 7).
    """
    print("Evaluating empirical learning curve (Days 1..N calibration vs subsequent days)...")
    # Group by subject and calculate timestamps
    days_grid = [0, 2, 4, 7]
    curve_results = []
    
    for n_days in days_grid:
        errors = []
        for pid in df_meals["subject_id"].unique():
            p_mask = df_meals["subject_id"] == pid
            p_meals = df_meals[p_mask].copy().sort_values("timestamp")
            if len(p_meals) < 5:
                continue
                
            first_ts = p_meals["timestamp"].min()
            split_ts = first_ts + pd.Timedelta(days=n_days)
            
            calib_meals = p_meals[p_meals["timestamp"] < split_ts]
            eval_meals = p_meals[p_meals["timestamp"] >= split_ts]
            
            if len(eval_meals) == 0:
                continue
                
            # Compute empirical shrinkage
            n_obs = len(calib_meals)
            w = n_obs / (n_obs + 4.0)  # kappa = 4.0
            
            # Simple prior vs observed offset
            calib_mean_rise = calib_meals["peak_rise"].mean() if n_obs > 0 else 35.0
            pop_prior_rise = 35.0  # Population prior
            personalized_rise = w * calib_mean_rise + (1.0 - w) * pop_prior_rise
            
            # Evaluation error on held-out post-calibration meals
            eval_actual = eval_meals["peak_rise"].values
            eval_error = np.sqrt(np.mean((eval_actual - personalized_rise) ** 2))
            errors.append(eval_error)
            
        curve_results.append({
            "calibration_days": n_days,
            "mean_rmse_mg_dl": round(float(np.mean(errors)), 2),
            "std_rmse_mg_dl": round(float(np.std(errors)), 2)
        })
        
    return curve_results

def main():
    print("=" * 70)
    print("THALITWIN: END-TO-END STEPPED-CARE TRAINING & EVALUATION PIPELINE")
    print("=" * 70)
    
    # 1. Noise Floor Benchmark
    noise_floor = compute_sensor_noise_floor()
    print(f"Empirical Sensor Noise Floor: MARD={noise_floor['cohort_mard_mean']:.2f}%, RMSE={noise_floor['cohort_rmse_mean']:.2f} mg/dL")
    
    # 2. Build Cohort Datasets
    df_meals, df_t1, df_t2, df_t3, total_days = build_cohort_dataset(max_participants=45)
    
    # 3. Baselines
    # Persistence baseline for peak
    rmse_persist = np.sqrt(np.mean((df_meals["peak_glucose"].values - df_meals["g_baseline"].values) ** 2))
    # Carbs linear baseline
    carbs_model = BaselineCarbsLinear()
    carbs_model.fit(df_meals["carbs_g"].values, df_meals["peak_rise"].values)
    carbs_preds = carbs_model.predict(df_meals["carbs_g"].values)
    rmse_carbs = np.sqrt(np.mean((df_meals["peak_rise"].values - carbs_preds) ** 2))
    
    baselines = {
        "persistence_rmse": round(float(rmse_persist), 2),
        "carbs_linear_rmse": round(float(rmse_carbs), 2),
        "sensor_noise_floor_rmse": round(noise_floor["cohort_rmse_mean"], 2),
        "sensor_noise_floor_mard": round(noise_floor["cohort_mard_mean"], 2)
    }
    
    # 4. GroupKFold Cross-Validation across T1, T2, T3
    print("\nRunning Stratified GroupKFold (5 Folds) on Tier 1 (Rich CGM)...")
    res_t1 = run_group_kfold_evaluation(df_meals, df_t1, "T1_Rich", total_days)
    
    print("Running Stratified GroupKFold (5 Folds) on Tier 2 (Frugal SMBG)...")
    res_t2 = run_group_kfold_evaluation(df_meals, df_t2, "T2_Frugal", total_days)
    
    print("Running Stratified GroupKFold (5 Folds) on Tier 3 (Triage)...")
    res_t3 = run_group_kfold_evaluation(df_meals, df_t3, "T3_Triage", total_days)
    
    # 5. Stepped-Care Economics (Performance per Rupee)
    sens_dict = {
        "T1_Rich": res_t1["classification"]["sensitivity"],
        "T2_Frugal": res_t2["classification"]["sensitivity"],
        "T3_Triage": res_t3["classification"]["sensitivity"]
    }
    econ_table = compute_performance_per_rupee(sens_dict)
    
    # 6. Empirical Learning Curve
    learning_curve = evaluate_empirical_learning_curve(df_meals, df_t1, df_t2)
    
    # 7. Summary Export
    final_output = {
        "meta": {
            "title": "ThaliTwin Stepped-Care Clinical Results",
            "participants_count": int(df_meals["subject_id"].nunique()),
            "meal_windows_count": len(df_meals),
            "total_patient_days": round(total_days, 1),
            "noise_floor": noise_floor
        },
        "baselines": baselines,
        "tiers": {
            "T1_Rich": res_t1,
            "T2_Frugal": res_t2,
            "T3_Triage": res_t3
        },
        "performance_per_rupee": econ_table,
        "learning_curve": learning_curve
    }
    
    out_json = os.path.join(RESULTS_DIR, "metrics.json")
    with open(out_json, "w") as f:
        json.dump(final_output, f, indent=2)
    print(f"\nAuthoritative metrics saved to {out_json}")
    
    # Generate CSV comparison table
    summary_rows = [
        {
            "Tier": "Tier 1 (Rich CGM)",
            "Sensors": "Dexcom G6 Pro (5m) + Fitbit + Meals",
            "Monthly Cost (INR)": "INR 10,000",
            "AUROC": res_t1["classification"]["auroc"],
            "AUPRC": res_t1["classification"]["auprc"],
            "Sensitivity": res_t1["classification"]["sensitivity"],
            "Peak Rise RMSE (mg/dL)": res_t1["regression"]["rmse"],
            "Conformal 90% Band": f"+/- {res_t1['conformal_q90']} mg/dL"
        },
        {
            "Tier": "Tier 2 (Frugal SMBG)",
            "Sensors": "Glucometer (3-4/day) + Fitbit + Meals",
            "Monthly Cost (INR)": "INR 1,200",
            "AUROC": res_t2["classification"]["auroc"],
            "AUPRC": res_t2["classification"]["auprc"],
            "Sensitivity": res_t2["classification"]["sensitivity"],
            "Peak Rise RMSE (mg/dL)": res_t2["regression"]["rmse"],
            "Conformal 90% Band": f"+/- {res_t2['conformal_q90']} mg/dL"
        },
        {
            "Tier": "Tier 3 (Triage)",
            "Sensors": "Fitbit + Static EHR Labs Only",
            "Monthly Cost (INR)": "INR 0",
            "AUROC": res_t3["classification"]["auroc"],
            "AUPRC": res_t3["classification"]["auprc"],
            "Sensitivity": res_t3["classification"]["sensitivity"],
            "Peak Rise RMSE (mg/dL)": res_t3["regression"]["rmse"],
            "Conformal 90% Band": f"+/- {res_t3['conformal_q90']} mg/dL"
        }
    ]
    df_summary = pd.DataFrame(summary_rows)
    out_csv = os.path.join(RESULTS_DIR, "stepped_care_comparison.csv")
    df_summary.to_csv(out_csv, index=False)
    print(f"Comparison table saved to {out_csv}")
    print("\n" + df_summary.to_string(index=False))

if __name__ == "__main__":
    main()
