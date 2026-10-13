"""
run_stress_test.py
Executes patient compliance and unlogged meal/snack dropout stress tests across 0% to 40%
dropout rates, benchmarking how Active Inquiry recovers clinical safety.
"""

import os
import sys
import json
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from thalitwin.stress_test import run_meal_dropout_stress_test

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def main():
    print("=" * 75)
    print("THALITWIN PATIENT COMPLIANCE & UNLOGGED MEAL STRESS TESTING")
    print("=" * 75)
    
    dropout_rates = [0.0, 0.10, 0.20, 0.30, 0.40]
    results = run_meal_dropout_stress_test(
        dropout_rates=dropout_rates,
        max_participants=45,
        random_seed=42
    )
    
    df = pd.DataFrame(results)
    
    print("\n" + "=" * 75)
    print("STRESS TEST RESULTS: IMPACT OF UNLOGGED MEALS ON TWIN ACCURACY")
    print("=" * 75)
    print(df.to_string(index=False))
    
    # Save CSV
    csv_path = os.path.join(RESULTS_DIR, "stress_test_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nSaved stress test results to {csv_path}")
    
    # Append to metrics.json
    metrics_path = os.path.join(RESULTS_DIR, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics_data = json.load(f)
            
        metrics_data["compliance_stress_testing"] = {
            "description": "Quantifies digital twin resilience when patients forget to log meals (0% to 40% dropout)",
            "dropout_rates_tested": [f"{int(r*100)}%" for r in dropout_rates],
            "results_table": results
        }
        
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, indent=2)
        print(f"Updated {metrics_path} with compliance stress test benchmarks.")

if __name__ == "__main__":
    main()
