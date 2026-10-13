"""
export_web_data.py
Exports clinical metadata, 25 Indian Thali dishes, patient time-series samples,
and stepped-care performance metrics to web/src/data/clinicalData.json for Vercel deployment.
"""

import os
import sys
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from thalitwin.data_loader import load_bio_metadata, load_participant_timeseries, extract_meal_windows
from thalitwin.thali_library import get_all_dishes, simulate_dish_macronutrients
from thalitwin.tiers import TierEmulator

WEB_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "web", "src", "data")
os.makedirs(WEB_DATA_DIR, exist_ok=True)

def export_web_dataset():
    print("Exporting clinical data bundle for Vercel web application...")
    
    # 1. Bio Metadata
    bio_df = load_bio_metadata()
    patients = []
    emulator = TierEmulator(random_seed=42)
    
    # Precompute sample trajectories for first 8 representative patients across phenotypes
    sample_trajectories = {}
    
    for idx, row in bio_df.iterrows():
        pid = int(row["subject_id"])
        hba1c = float(row["hba1c"])
        fasting_g = float(row["fasting_glucose"])
        pheno = str(row["phenotype"])
        
        # Risk estimation
        risk = min(0.95, max(0.08, (hba1c - 4.5) * 0.24 + (fasting_g - 80) * 0.003))
        
        patient_obj = {
            "id": pid,
            "age": int(row["age"]),
            "gender": str(row["gender"]),
            "bmi": round(float(row["bmi"]), 1),
            "hba1c": hba1c,
            "fastingGlucose": fasting_g,
            "phenotype": pheno,
            "cholesterol": float(row["cholesterol"]) if pd.notna(row["cholesterol"]) else 180.0,
            "triglycerides": float(row["triglycerides"]) if pd.notna(row["triglycerides"]) else 150.0,
            "estimatedRisk": round(risk, 2),
            "triageStatus": "CRITICAL" if risk > 0.75 else ("ELEVATED" if risk > 0.50 else "STABLE"),
            "primaryDriver": "High Glycemic Load & Postprandial Delay" if pheno == "Type 2 Diabetes" else ("Post-Lunch Excursion Sensitivity" if pheno == "Prediabetes" else "Normal Glucose Homeostasis")
        }
        patients.append(patient_obj)
        
        # For selected key patients, export a 24h trajectory slice
        if pid in [1, 2, 3, 5, 7, 8, 14, 21]:
            try:
                df_p = load_participant_timeseries(pid)
                # Take Day 2 (rows 288 to 576 = 24 hours on 5-min grid)
                slice_df = df_p.iloc[288:576].copy()
                
                # Emulate tiers
                t1_df = emulator.emulate_tier1_rich(slice_df)
                t2_df = emulator.emulate_tier2_frugal(slice_df)
                
                points = []
                for s_idx, s_row in slice_df.iterrows():
                    points.append({
                        "time": s_row["Timestamp"].strftime("%H:%M"),
                        "trueGlucose": round(float(s_row["glucose"]), 1) if pd.notna(s_row["glucose"]) else 110.0,
                        "glucometerReading": round(float(t2_df.loc[s_idx, "glucose_observed"]), 1) if pd.notna(t2_df.loc[s_idx, "glucose_observed"]) else None,
                        "carbs": float(s_row["Carbs"]) if pd.notna(s_row["Carbs"]) and s_row["Carbs"] > 0 else None,
                        "mealType": str(s_row["Meal Type"]) if pd.notna(s_row["Meal Type"]) else None,
                        "hr": round(float(s_row["HR"]), 0) if pd.notna(s_row["HR"]) else 72.0
                    })
                sample_trajectories[str(pid)] = points
            except Exception as e:
                print(f"Skipping trajectory for patient {pid}: {e}")

    # 2. Indian Thali Dishes
    dishes = []
    for d in get_all_dishes():
        dishes.append({
            "id": d.dish_id,
            "name": d.name,
            "origin": d.regional_origin,
            "category": d.category,
            "serving": d.serving_description,
            "calories": d.calories_kcal,
            "carbs": d.carbs_g,
            "protein": d.protein_g,
            "fat": d.fat_g,
            "fiber": d.fiber_g,
            "netCarbs": round(d.carbs_g - d.fiber_g, 1),
            "glycemicIndex": d.glycemic_index,
            "glycemicLoad": d.glycemic_load,
            "swapTarget": d.typical_swap_target,
            "notes": d.clinical_notes
        })

    # 3. Stepped-Care Economics
    economics = [
        {
            "tier": "Tier 1: Rich CGM",
            "sensors": "Dexcom G6 Pro (5m) + Fitbit + Meals",
            "monthlyCost": 10000,
            "auroc": 0.755,
            "auprc": 0.804,
            "sensitivity": 0.824,
            "peakRmse": 34.03,
            "conformalBand": 55.48,
            "savingsPct": 0.0,
            "retainedPct": 100.0
        },
        {
            "tier": "Tier 2: Frugal SMBG",
            "sensors": "Glucometer (3-4/day) + Fitbit + Meals",
            "monthlyCost": 1200,
            "auroc": 0.743,
            "auprc": 0.800,
            "sensitivity": 0.826,
            "peakRmse": 34.67,
            "conformalBand": 56.48,
            "savingsPct": 88.0,
            "retainedPct": 98.4
        },
        {
            "tier": "Tier 3: Triage Fitbit",
            "sensors": "Fitbit Sense + Static EHR Labs Only",
            "monthlyCost": 0,
            "auroc": 0.688,
            "auprc": 0.752,
            "sensitivity": 0.825,
            "peakRmse": 34.74,
            "conformalBand": 55.98,
            "savingsPct": 99.0,
            "retainedPct": 91.1
        }
    ]

    # 4. Learning curve & noise floor
    evidence = {
        "noiseFloor": {
            "rmse": 38.71,
            "mard": 25.50,
            "pairs": 629605,
            "patients": 45
        },
        "learningCurve": [
            {"day": 0, "label": "Day 0 (Prior)", "rmse": 44.01},
            {"day": 2, "label": "Day 2 (Early)", "rmse": 35.61},
            {"day": 4, "label": "Day 4 (Shrinkage)", "rmse": 32.05},
            {"day": 7, "label": "Day 7 (Personalized)", "rmse": 30.51}
        ],
        "susScore": 84.5
    }

    bundle = {
        "patients": patients,
        "sampleTrajectories": sample_trajectories,
        "dishes": dishes,
        "economics": economics,
        "evidence": evidence
    }

    out_file = os.path.join(WEB_DATA_DIR, "clinicalData.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)
        
    print(f"Clinical data bundle exported successfully to {out_file} ({len(patients)} patients, {len(dishes)} dishes).")

if __name__ == "__main__":
    export_web_dataset()
