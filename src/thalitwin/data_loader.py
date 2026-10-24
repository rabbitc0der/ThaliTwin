"""
data_loader.py
Ingestion, Quality Control (QC), 5-Minute Grid Resampling, and Empirical Sensor Noise Floor Calculator
for the PhysioNet CGMacros Dataset (45 Study Participants).
"""

import os
import glob
import re
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "CGMacros")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")

def get_phenotype(hba1c: float) -> str:
    """Classify glycemic phenotype according to ADA / ICMR clinical guidelines."""
    if pd.isna(hba1c):
        return "Unknown"
    if hba1c < 5.7:
        return "Normoglycemic"
    elif hba1c <= 6.4:
        return "Prediabetes"
    else:
        return "Type 2 Diabetes"

def load_bio_metadata(raw_dir: str = RAW_DATA_DIR) -> pd.DataFrame:
    """
    Loads and standardizes participant baseline clinical metadata from bio.csv.
    """
    bio_path = os.path.join(raw_dir, "bio.csv")
    if not os.path.exists(bio_path):
        raise FileNotFoundError(f"bio.csv not found at {bio_path}")
    
    bio = pd.read_csv(bio_path)
    # Clean whitespace in column names
    bio.columns = [c.strip() for c in bio.columns]
    
    # Standardize column naming
    rename_map = {
        "subject": "subject_id",
        "Age": "age",
        "Gender": "gender",
        "BMI": "bmi",
        "Body weight": "weight_lbs",
        "Height": "height_in",
        "Self-identify": "ethnicity",
        "A1c PDL (Lab)": "hba1c",
        "Fasting GLU - PDL (Lab)": "fasting_glucose",
        "Insulin": "fasting_insulin",
        "Triglycerides": "triglycerides",
        "Cholesterol": "cholesterol",
        "HDL": "hdl",
        "Non HDL": "non_hdl",
        "LDL (Cal)": "ldl",
        "VLDL (Cal)": "vldl",
        "Cho/HDL Ratio": "cho_hdl_ratio",
        "#1 Contour Fingerstick GLU": "fingerstick_glu_1",
        "#2 Contour Fingerstick GLU": "fingerstick_glu_2",
        "#3 Contour Fingerstick GLU": "fingerstick_glu_3",
    }
    bio = bio.rename(columns={k: v for k, v in rename_map.items() if k in bio.columns})
    
    # Compute clinical phenotype
    bio["phenotype"] = bio["hba1c"].apply(get_phenotype)
    
    # Clean error codes (e.g. 800 in LDL or 400 in VLDL as described in DataDictionary)
    if "ldl" in bio.columns:
        bio.loc[bio["ldl"] >= 500, "ldl"] = np.nan
    if "vldl" in bio.columns:
        bio.loc[bio["vldl"] >= 300, "vldl"] = np.nan
        
    return bio

def load_participant_timeseries(
    participant_id: int,
    raw_dir: str = RAW_DATA_DIR,
    warmup_hours: float = 12.0
) -> pd.DataFrame:
    """
    Loads, cleans, and resamples 1-minute participant time-series to a standard 5-minute grid.
    Drops the initial sensor warm-up period and interpolates gaps <= 15 minutes.
    """
    # Participant IDs formatted as CGMacros-001 or CGMacros-012
    pid_str = f"{participant_id:03d}"
    folder_name = f"CGMacros-{pid_str}"
    file_path = os.path.join(raw_dir, folder_name, f"{folder_name}.csv")
    
    if not os.path.exists(file_path):
        # Check alternate format
        pattern = os.path.join(raw_dir, f"*{participant_id}*", f"*{participant_id}*.csv")
        matches = glob.glob(pattern)
        if matches:
            file_path = matches[0]
        else:
            raise FileNotFoundError(f"No CSV file found for participant {participant_id}")
            
    df = pd.read_csv(file_path)
    # Normalize column names
    df.columns = [c.strip() for c in df.columns]
    
    # Parse timestamp
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.sort_values("Timestamp").reset_index(drop=True)
    
    # Drop sensor warm-up (first 12 hours)
    start_time = df["Timestamp"].min()
    df = df[df["Timestamp"] >= start_time + pd.Timedelta(hours=warmup_hours)].copy()
    
    # Physiological clipping for glucose
    for cgm_col in ["Dexcom GL", "Libre GL"]:
        if cgm_col in df.columns:
            df[cgm_col] = df[cgm_col].clip(lower=40.0, upper=400.0)
            
    # Normalize activity column variants
    if "Steps" in df.columns and "Calories (Activity)" not in df.columns:
        df["Calories (Activity)"] = df["Steps"] * 0.04
        
    for c in ["Dexcom GL", "Libre GL", "HR", "Calories (Activity)", "METs"]:
        if c not in df.columns:
            df[c] = np.nan
    for c in ["Calories", "Carbs", "Protein", "Fat", "Fiber", "Amount Consumed"]:
        if c not in df.columns:
            df[c] = 0.0
            
    # Set index for 5-minute resampling
    df = df.set_index("Timestamp")
    
    # Continuous signals: 5-minute mean
    cgm_and_wearable_cols = ["Dexcom GL", "Libre GL", "HR", "Calories (Activity)", "METs"]
    meal_cols = ["Calories", "Carbs", "Protein", "Fat", "Fiber", "Amount Consumed"]
    
    df_continuous = df[cgm_and_wearable_cols].resample("5min").mean()
    
    # Interpolate short sensor dropouts (<= 15 minutes, which is 3 steps on 5-min grid)
    df_continuous = df_continuous.interpolate(method="time", limit=3)
    
    # Meal events: 5-minute sum
    df_meals = df[meal_cols].resample("5min").sum()
    
    # Meal type: take first non-null
    if "Meal Type" in df.columns:
        df_meal_type = df[["Meal Type"]].resample("5min").first()
    else:
        df_meal_type = pd.DataFrame(index=df_continuous.index)
        df_meal_type["Meal Type"] = np.nan
        
    # Combine back
    df_5min = pd.concat([df_continuous, df_meals, df_meal_type], axis=1)
    df_5min["subject_id"] = participant_id
    
    # Create unified primary glucose column: prioritize Dexcom G6 Pro (5-min native), fall back to Libre Pro
    df_5min["glucose"] = df_5min["Dexcom GL"].fillna(df_5min["Libre GL"])
    
    return df_5min.reset_index()

def compute_sensor_noise_floor(raw_dir: str = RAW_DATA_DIR) -> Dict[str, float]:
    """
    Computes empirical sensor disagreement between simultaneously worn Dexcom G6 Pro and Libre Pro.
    Returns MARD (Mean Absolute Relative Difference %) and RMSE (mg/dL).
    """
    files = glob.glob(os.path.join(raw_dir, "*", "*.csv"))
    mards, rmses, sample_counts = [], [], []
    
    for f in files:
        if "bio.csv" in f:
            continue
        try:
            df = pd.read_csv(f)
            df.columns = [c.strip() for c in df.columns]
            if "Dexcom GL" in df.columns and "Libre GL" in df.columns:
                valid = df["Dexcom GL"].notna() & df["Libre GL"].notna()
                if valid.sum() >= 50:
                    dex = df.loc[valid, "Dexcom GL"].values
                    lib = df.loc[valid, "Libre GL"].values
                    # MARD with Dexcom as reference
                    mard = np.mean(np.abs(dex - lib) / dex) * 100.0
                    rmse = np.sqrt(np.mean((dex - lib) ** 2))
                    mards.append(mard)
                    rmses.append(rmse)
                    sample_counts.append(valid.sum())
        except Exception:
            continue
            
    return {
        "cohort_mard_mean": float(np.mean(mards)),
        "cohort_mard_std": float(np.std(mards)),
        "cohort_rmse_mean": float(np.mean(rmses)),
        "cohort_rmse_std": float(np.std(rmses)),
        "total_overlapping_samples": int(sum(sample_counts)),
        "patients_evaluated": len(mards)
    }

def extract_meal_windows(
    df_5min: pd.DataFrame,
    phenotype: str,
    pre_window_steps: int = 3,   # 15 minutes before meal
    post_window_steps: int = 24, # 120 minutes after meal
    threshold: Optional[float] = None
) -> List[Dict]:
    """
    Extracts 2-hour postprandial evaluation windows for every logged meal.
    Guarantees strict leakage prevention: only includes windows where baseline glucose < threshold.
    Default threshold: 180.0 mg/dL for T2D, 140.0 mg/dL for Normal/Prediabetes.
    """
    meals = []
    if threshold is None:
        threshold = 180.0 if phenotype == "Type 2 Diabetes" else 140.0
    
    # Identify meal starts: rows where Carbs > 0 or Meal Type is specified
    is_meal = (df_5min["Carbs"] > 0) | (df_5min["Meal Type"].notna())
    meal_indices = df_5min.index[is_meal].tolist()
    
    # Debounce meals within 90 minutes of each other
    debounced_indices = []
    last_idx = -999
    for idx in meal_indices:
        if idx - last_idx >= 18:  # 18 * 5min = 90 min
            debounced_indices.append(idx)
            last_idx = idx
            
    for idx in debounced_indices:
        # Check window boundaries
        if idx < pre_window_steps or idx + post_window_steps >= len(df_5min):
            continue
            
        g_series = df_5min.loc[idx : idx + post_window_steps, "glucose"].values
        # Baseline glucose (mean of pre-meal steps)
        pre_g = df_5min.loc[idx - pre_window_steps : idx, "glucose"].dropna()
        if len(pre_g) == 0:
            continue
        g_baseline = pre_g.iloc[-1]
        
        # Valid window requires at least 70% glucose non-null
        if np.isnan(g_series).mean() > 0.3:
            continue
            
        # LEAKAGE-SAFE FILTER: Baseline must be below threshold for an excursion to be a genuine event
        if g_baseline >= threshold:
            continue
            
        # Calculate excursion metrics
        g_clean = pd.Series(g_series).interpolate().bfill().ffill().values
        peak_glucose = float(np.max(g_clean))
        peak_rise = float(peak_glucose - g_baseline)
        time_to_peak_min = int(np.argmax(g_clean) * 5)
        
        # Incremental AUC above baseline (mg/dL * min) using trapezoidal rule
        delta_above_base = np.maximum(0.0, g_clean - g_baseline)
        if hasattr(np, "trapezoid"):
            iauc = float(np.trapezoid(delta_above_base, dx=5.0))
        else:
            iauc = float(np.trapz(delta_above_base, dx=5.0))
        
        # Binary excursion target (>= threshold within 120 min)
        is_excursion = int(peak_glucose >= threshold)
        
        # Step forecasts at +30m (6 steps), +60m (12 steps), +120m (24 steps)
        g_30 = float(g_clean[min(6, len(g_clean)-1)])
        g_60 = float(g_clean[min(12, len(g_clean)-1)])
        g_120 = float(g_clean[min(24, len(g_clean)-1)])
        
        meal_row = df_5min.iloc[idx]
        meal_info = {
            "subject_id": int(meal_row["subject_id"]),
            "timestamp": meal_row["Timestamp"],
            "meal_type": str(meal_row.get("Meal Type", "Meal")),
            "carbs_g": float(meal_row.get("Carbs", 0.0)),
            "protein_g": float(meal_row.get("Protein", 0.0)),
            "fat_g": float(meal_row.get("Fat", 0.0)),
            "fiber_g": float(meal_row.get("Fiber", 0.0)),
            "calories_kcal": float(meal_row.get("Calories", 0.0)),
            "g_baseline": float(g_baseline),
            "peak_glucose": peak_glucose,
            "peak_rise": peak_rise,
            "time_to_peak_min": time_to_peak_min,
            "iauc": iauc,
            "is_excursion": is_excursion,
            "g_30m": g_30,
            "g_60m": g_60,
            "g_120m": g_120,
            "threshold_used": threshold,
            "row_index": idx
        }
        meals.append(meal_info)
        
    return meals
