"""
run_external_validation.py
Executes out-of-distribution external cohort validation on the 16-participant
PhysioNet BIG IDEAs Glycemic Wearable Cohort.
Saves metrics to results/external_validation_big_ideas.csv and updates results/metrics.json.
"""

import os
import sys
import json
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from thalitwin.external_validation import evaluate_external_cohort

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def main():
    print("=" * 75)
    print("THALITWIN EXTERNAL COHORT VALIDATION (PHYSIONET BIG IDEAs)")
    print("=" * 75)
    
    # Conformal q90 from Tier 1 training is 55.48 mg/dL
    results = evaluate_external_cohort(conformal_q90=55.48)
    
    print("\n[COHORT SUMMARY]")
    print(f"  Dataset: {results['dataset']}")
    print(f"  Hardware: {results['hardware']}")
    print(f"  Participants Evaluated: {results['cohort_agp']['total_participants']}")
    print(f"  Total Continuous CGM Readings: {results['cohort_agp']['total_cgm_readings']:,}")
    print(f"  Cohort Mean Glucose: {results['cohort_agp']['cohort_mean_glucose']} mg/dL")
    print(f"  Time in Range (70-180 mg/dL): {results['cohort_agp']['cohort_tir_pct']}%")
    print(f"  Time Above Range (>180 mg/dL): {results['cohort_agp']['cohort_tar_pct']}%")
    print(f"  Time Below Range (<70 mg/dL): {results['cohort_agp']['cohort_tbr_pct']}%")
    print(f"  Estimated GMI: {results['cohort_agp']['cohort_gmi']}%")
    
    print("\n[ZERO-SHOT GENERALIZATION PERFORMANCE]")
    print(f"  Excursion Detection AUROC: {results['zero_shot_auroc']:.3f}")
    print(f"  Excursion Detection AUPRC: {results['zero_shot_auprc']:.3f}")
    print(f"  Peak Glucose Forecast RMSE: {results['zero_shot_peak_rmse_mg_dl']:.2f} mg/dL")
    print(f"  Conformal Nominal Coverage: {results['conformal_nominal_coverage_pct']}%")
    print(f"  Conformal Empirical Coverage: {results['conformal_empirical_coverage_pct']}% (Target >= 90%)")
    
    # Save per-participant CSV
    df_p = pd.DataFrame(results["participants"])
    csv_path = os.path.join(RESULTS_DIR, "external_validation_big_ideas.csv")
    df_p.to_csv(csv_path, index=False)
    print(f"\nSaved participant breakdown table to {csv_path}")
    
    # Update metrics.json
    metrics_path = os.path.join(RESULTS_DIR, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics_data = json.load(f)
            
        metrics_data["external_validation_big_ideas"] = {
            "dataset": results["dataset"],
            "hardware": results["hardware"],
            "participants_count": results["cohort_agp"]["total_participants"],
            "total_cgm_readings": results["cohort_agp"]["total_cgm_readings"],
            "zero_shot_auroc": results["zero_shot_auroc"],
            "zero_shot_auprc": results["zero_shot_auprc"],
            "zero_shot_peak_rmse_mg_dl": results["zero_shot_peak_rmse_mg_dl"],
            "conformal_empirical_coverage_pct": results["conformal_empirical_coverage_pct"],
            "cohort_agp": results["cohort_agp"]
        }
        
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, indent=2)
        print(f"Updated {metrics_path} with external cohort validation benchmarks.")

if __name__ == "__main__":
    main()
