"""
features.py
Leakage-Free Past-Only Feature Engineering Pipeline for ThaliTwin.
Supports Tier 1 (Rich CGM), Tier 2 (Frugal SMBG), and Tier 3 (Triage).
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    # Static EHR & Demographics
    "age",
    "bmi",
    "hba1c",
    "fasting_glucose",
    "fasting_insulin",
    "triglycerides",
    "cholesterol",
    "hdl",
    "is_male",
    "is_t2d",
    "is_prediabetes",
    
    # Meal Features at time t
    "carbs_g",
    "protein_g",
    "fat_g",
    "fiber_g",
    "net_carbs_g",
    "calories_kcal",
    "glycemic_load_est",
    "hour_of_day",
    "is_breakfast",
    "is_lunch",
    "is_dinner",
    
    # Wearable Features (Fitbit strictly past t)
    "hr_current",
    "hr_mean_30m",
    "hr_mean_60m",
    "mets_mean_30m",
    "cal_active_60m",
    "sedentary_bout_min",
    
    # Glucose Features (Tier-Dependent)
    "g_current",
    "g_slope_15m",
    "g_slope_30m",
    "g_std_2h",
    "minutes_since_last_reading",
    
    # Personal Calibration Priors
    "personal_carb_sensitivity",
    "observed_calibration_meals"
]

def extract_row_features(
    df: pd.DataFrame,
    idx: int,
    bio_row: pd.Series,
    tier: str = "T1_Rich",
    personal_priors: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Extracts features at timestamp index `idx` strictly using past rows (<= idx).
    Any access to idx+1 or greater is impossible by design.
    """
    row = df.iloc[idx]
    ts = pd.to_datetime(row["Timestamp"])
    
    # 1. Static EHR features
    is_male = 1.0 if str(bio_row.get("gender", "")).upper().startswith("M") else 0.0
    pheno = str(bio_row.get("phenotype", ""))
    is_t2d = 1.0 if pheno == "Type 2 Diabetes" else 0.0
    is_prediabetes = 1.0 if pheno == "Prediabetes" else 0.0
    
    age = float(bio_row.get("age", 45.0))
    bmi = float(bio_row.get("bmi", 27.0))
    hba1c = float(bio_row.get("hba1c", 5.8))
    fasting_glu = float(bio_row.get("fasting_glucose", 100.0))
    insulin = float(bio_row.get("fasting_insulin", 10.0))
    if pd.isna(insulin): insulin = 10.0
    triglycerides = float(bio_row.get("triglycerides", 150.0))
    if pd.isna(triglycerides): triglycerides = 150.0
    cholesterol = float(bio_row.get("cholesterol", 180.0))
    if pd.isna(cholesterol): cholesterol = 180.0
    hdl = float(bio_row.get("hdl", 45.0))
    if pd.isna(hdl): hdl = 45.0

    # 2. Meal features at time t
    carbs = float(row.get("Carbs", 0.0))
    if pd.isna(carbs): carbs = 0.0
    protein = float(row.get("Protein", 0.0))
    if pd.isna(protein): protein = 0.0
    fat = float(row.get("Fat", 0.0))
    if pd.isna(fat): fat = 0.0
    fiber = float(row.get("Fiber", 0.0))
    if pd.isna(fiber): fiber = 0.0
    calories = float(row.get("Calories", 0.0))
    if pd.isna(calories): calories = 0.0
    
    net_carbs = max(0.0, carbs - fiber)
    # Estimate Glycemic Load using average Indian diet GI ~65
    gl_est = (net_carbs * 65.0) / 100.0
    
    hour = ts.hour
    mtype = str(row.get("Meal Type", "")).lower()
    is_breakfast = 1.0 if ("breakfast" in mtype or (6 <= hour <= 10)) else 0.0
    is_lunch = 1.0 if ("lunch" in mtype or (12 <= hour <= 15)) else 0.0
    is_dinner = 1.0 if ("dinner" in mtype or (19 <= hour <= 22)) else 0.0

    # 3. Wearable past features (Fitbit)
    # Past 6 steps = 30 min, past 12 steps = 60 min
    past_30_idx = max(0, idx - 6)
    past_60_idx = max(0, idx - 12)
    past_120_idx = max(0, idx - 24)
    
    hr_series = df.loc[past_60_idx : idx, "HR"].dropna() if "HR" in df.columns else pd.Series(dtype=float)
    hr_current = float(hr_series.iloc[-1]) if len(hr_series) > 0 else 72.0
    hr_mean_30 = float(df.loc[past_30_idx : idx, "HR"].mean()) if ("HR" in df.columns and len(df.loc[past_30_idx : idx, "HR"].dropna()) > 0) else hr_current
    hr_mean_60 = float(df.loc[past_60_idx : idx, "HR"].mean()) if ("HR" in df.columns and len(df.loc[past_60_idx : idx, "HR"].dropna()) > 0) else hr_current
    
    mets_series = df.loc[past_30_idx : idx, "METs"].dropna() if "METs" in df.columns else pd.Series(dtype=float)
    mets_mean_30 = float(mets_series.mean()) if len(mets_series) > 0 else 10.0
    
    cal_series = df.loc[past_60_idx : idx, "Calories (Activity)"].dropna() if "Calories (Activity)" in df.columns else pd.Series(dtype=float)
    cal_active_60 = float(cal_series.sum()) if len(cal_series) > 0 else 10.0
    
    # Sedentary bout (consecutive steps before idx where METs <= 15)
    sedentary_steps = 0
    if "METs" in df.columns:
        for s in range(idx, max(-1, idx - 36), -1):
            m_val = df.loc[s, "METs"]
            if pd.notna(m_val) and m_val <= 15.0:
                sedentary_steps += 1
            else:
                break
    sedentary_bout_min = float(sedentary_steps * 5)

    # 4. Glucose features (Tier dependent)
    if tier == "T1_Rich":
        past_g = df.loc[past_120_idx : idx, "glucose"].dropna()
        g_current = float(past_g.iloc[-1]) if len(past_g) > 0 else fasting_glu
        
        # Slope over 15 min (3 steps) and 30 min (6 steps)
        g_15_ago = df.loc[max(0, idx - 3), "glucose"]
        g_30_ago = df.loc[max(0, idx - 6), "glucose"]
        
        g_slope_15 = (g_current - g_15_ago) / 15.0 if pd.notna(g_15_ago) else 0.0
        g_slope_30 = (g_current - g_30_ago) / 30.0 if pd.notna(g_30_ago) else 0.0
        
        g_std_2h = float(past_g.std()) if len(past_g) > 2 else 5.0
        if pd.isna(g_std_2h): g_std_2h = 5.0
        mins_since_reading = 0.0
        
    elif tier == "T2_Frugal":
        g_obs = row.get("last_glucose_observed", np.nan)
        if pd.isna(g_obs):
            g_obs = row.get("glucose_observed", np.nan)
        if pd.isna(g_obs):
            g_obs = fasting_glu
        g_current = float(g_obs)
        g_slope_15 = 0.0
        g_slope_30 = 0.0
        g_std_2h = 0.0
        mins_since_reading = float(row.get("minutes_since_last_reading", 0.0))
        
    else:  # T3_Triage
        g_current = fasting_glu
        g_slope_15 = 0.0
        g_slope_30 = 0.0
        g_std_2h = 0.0
        mins_since_reading = 9999.0

    # 5. Personal Calibration Priors
    if personal_priors is not None:
        personal_carb_sens = float(personal_priors.get("carb_sensitivity", 0.8))
        obs_meals = float(personal_priors.get("observed_meals", 0.0))
    else:
        # Default population prior
        personal_carb_sens = 0.8  # ~0.8 mg/dL rise per gram carb
        obs_meals = 0.0

    return {
        "age": age,
        "bmi": bmi,
        "hba1c": hba1c,
        "fasting_glucose": fasting_glu,
        "fasting_insulin": insulin,
        "triglycerides": triglycerides,
        "cholesterol": cholesterol,
        "hdl": hdl,
        "is_male": is_male,
        "is_t2d": is_t2d,
        "is_prediabetes": is_prediabetes,
        "carbs_g": carbs,
        "protein_g": protein,
        "fat_g": fat,
        "fiber_g": fiber,
        "net_carbs_g": net_carbs,
        "calories_kcal": calories,
        "glycemic_load_est": gl_est,
        "hour_of_day": float(hour),
        "is_breakfast": is_breakfast,
        "is_lunch": is_lunch,
        "is_dinner": is_dinner,
        "hr_current": hr_current,
        "hr_mean_30m": hr_mean_30,
        "hr_mean_60m": hr_mean_60,
        "mets_mean_30m": mets_mean_30,
        "cal_active_60m": cal_active_60,
        "sedentary_bout_min": sedentary_bout_min,
        "g_current": g_current,
        "g_slope_15m": g_slope_15,
        "g_slope_30m": g_slope_30,
        "g_std_2h": g_std_2h,
        "minutes_since_last_reading": mins_since_reading,
        "personal_carb_sensitivity": personal_carb_sens,
        "observed_calibration_meals": obs_meals
    }
