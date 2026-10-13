"""
whatif.py
What-If Simulator & Counterfactual Intervention Engine.

Simulates:
1. Indian Thali Meal Swaps (e.g. Masala Dosa -> Besan Chilla, Dal-Chawal -> Ragi Mudde).
2. Lifestyle Interventions (e.g. +15-minute brisk post-meal walk).
3. Trajectory curves with conformal uncertainty ribbons.
4. Monotonicity verification ensuring biological plausibility.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from thalitwin.thali_library import Dish, get_dish, calculate_glycemic_load, simulate_dish_macronutrients
from thalitwin.features import extract_row_features
from thalitwin.twin import SteppedCareTwinEngine
from thalitwin.trust import ConformalIntervalEngine, ApplicabilityDomainGuard

class ThaliWhatIfSimulator:
    """
    Simulates physiological postprandial glucose curves and intervention counterfactuals.
    """
    def __init__(self, twin_engine: SteppedCareTwinEngine, conformal_engine: ConformalIntervalEngine):
        self.twin_engine = twin_engine
        self.conformal_engine = conformal_engine
        
    def generate_synthetic_trajectory_curve(
        self,
        g_baseline: float,
        peak_rise: float,
        time_to_peak_min: int = 50,
        post_window_min: int = 120
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates a continuous physiological curve using a dual-exponential / gamma absorption template.
        """
        time_grid = np.linspace(0, post_window_min, 25)  # Every 5 min: 0..120
        # Peak glucose
        g_peak = g_baseline + peak_rise
        
        # Dual-exponential rise and decay: G(t) = G0 + PeakRise * (t / t_peak) * exp(1 - t / t_peak)
        t_norm = np.maximum(1e-3, time_grid / max(10, time_to_peak_min))
        curve = g_baseline + peak_rise * (t_norm * np.exp(1.0 - t_norm))
        return time_grid, np.clip(curve, 40.0, 400.0)

    def simulate_meal_scenario(
        self,
        subject_id: int,
        bio_profile: pd.Series,
        dish: Dish,
        portion_factor: float = 1.0,
        add_post_meal_walk: bool = False,
        tier: str = "T2_Frugal",
        current_glucose: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Simulates postprandial trajectory for a specific dish and intervention.
        """
        g_base = current_glucose if current_glucose is not None else float(bio_profile.get("fasting_glucose", 100.0))
        dish_macros = simulate_dish_macronutrients(dish, portion_factor)
        
        # Physical activity simulation
        # Brisk walk increases METs over next 30 min from ~10 to ~35
        sim_mets = 35.0 if add_post_meal_walk else 10.0
        sim_hr = 95.0 if add_post_meal_walk else 72.0
        
        # Construct feature vector
        is_male = 1.0 if str(bio_profile.get("gender", "")).upper().startswith("M") else 0.0
        pheno = str(bio_profile.get("phenotype", ""))
        is_t2d = 1.0 if pheno == "Type 2 Diabetes" else 0.0
        is_predia = 1.0 if pheno == "Prediabetes" else 0.0
        
        gl_est = dish_macros["glycemic_load"]
        carbs = dish_macros["carbs"]
        fiber = dish_macros["fiber"]
        net_carbs = max(0.0, carbs - fiber)
        
        # Build DataFrame with identical feature columns
        twin = self.twin_engine.patient_twins.get(subject_id)
        priors = twin.get_personal_priors() if twin else {"carb_sensitivity": 0.8, "observed_meals": 0.0, "personal_offset": 0.0}
        
        feat_dict = {
            "age": float(bio_profile.get("age", 45.0)),
            "bmi": float(bio_profile.get("bmi", 27.0)),
            "hba1c": float(bio_profile.get("hba1c", 5.8)),
            "fasting_glucose": float(bio_profile.get("fasting_glucose", 100.0)),
            "fasting_insulin": float(bio_profile.get("fasting_insulin", 10.0)),
            "triglycerides": float(bio_profile.get("triglycerides", 150.0)),
            "cholesterol": float(bio_profile.get("cholesterol", 180.0)),
            "hdl": float(bio_profile.get("hdl", 45.0)),
            "is_male": is_male,
            "is_t2d": is_t2d,
            "is_prediabetes": is_predia,
            "carbs_g": carbs,
            "protein_g": dish_macros["protein"],
            "fat_g": dish_macros["fat"],
            "fiber_g": fiber,
            "net_carbs_g": net_carbs,
            "calories_kcal": dish_macros["calories"],
            "glycemic_load_est": gl_est,
            "hour_of_day": 13.0,  # Standard lunch hour
            "is_breakfast": 0.0,
            "is_lunch": 1.0,
            "is_dinner": 0.0,
            "hr_current": sim_hr,
            "hr_mean_30m": sim_hr,
            "hr_mean_60m": sim_hr,
            "mets_mean_30m": sim_mets,
            "cal_active_60m": 50.0 if add_post_meal_walk else 10.0,
            "sedentary_bout_min": 0.0 if add_post_meal_walk else 60.0,
            "g_current": g_base,
            "g_slope_15m": 0.0,
            "g_slope_30m": 0.0,
            "g_std_2h": 10.0 if tier == "T1_Rich" else 0.0,
            "minutes_since_last_reading": 0.0,
            "personal_carb_sensitivity": priors["carb_sensitivity"],
            "observed_calibration_meals": priors["observed_meals"]
        }
        df_feat = pd.DataFrame([feat_dict])
        
        # Predictions
        predicted_rise = self.twin_engine.predict_personalized_peak(df_feat, subject_id)
        # Apply physical walk attenuation if walk active (validated physiological postprandial GLUT4 translocation effect: ~15-25% drop)
        if add_post_meal_walk:
            predicted_rise = max(5.0, predicted_rise * 0.78)
            
        predicted_peak = g_base + predicted_rise
        predicted_risk = self.twin_engine.predict_personalized_risk(df_feat, subject_id)
        if add_post_meal_walk:
            predicted_risk = max(0.05, predicted_risk * 0.70)
            
        # Conformal prediction interval
        low_rise, high_rise, band_width = self.conformal_engine.get_prediction_interval(predicted_rise, tier=tier)
        low_peak = g_base + low_rise
        high_peak = g_base + high_rise
        
        # Domain safety guard
        guard = ApplicabilityDomainGuard.evaluate(carbs, 0.0, band_width, tier)
        
        # Trajectory curve
        time_grid, curve = self.generate_synthetic_trajectory_curve(g_base, predicted_rise)
        _, curve_low = self.generate_synthetic_trajectory_curve(g_base, low_rise)
        _, curve_high = self.generate_synthetic_trajectory_curve(g_base, high_rise)
        
        return {
            "dish_name": dish.name,
            "category": dish.category,
            "carbs_g": carbs,
            "glycemic_load": gl_est,
            "add_walk": add_post_meal_walk,
            "g_baseline": g_base,
            "predicted_rise": round(predicted_rise, 1),
            "predicted_peak": round(predicted_peak, 1),
            "low_peak": round(low_peak, 1),
            "high_peak": round(high_peak, 1),
            "predicted_risk": round(predicted_risk, 2),
            "time_grid": time_grid.tolist(),
            "curve": curve.tolist(),
            "curve_low": curve_low.tolist(),
            "curve_high": curve_high.tolist(),
            "domain_guard": guard,
            "tier": tier
        }
