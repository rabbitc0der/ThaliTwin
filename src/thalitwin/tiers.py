"""
tiers.py
Three-Tier Stepped-Care Sensor Emulator & Stress Testing Engine.

Tiers:
- Tier 1 (Rich): Full continuous CGM stream (5-min Dexcom/Libre) + Smartwatch + Meal log. (~₹10,000/mo)
- Tier 2 (Frugal): Sparse fingersticks (3-5/day) with 7% ISO-15197 glucometer noise + Smartwatch + Meal log. (~₹1,200/mo)
- Tier 3 (Minimal / Triage): Smartwatch + Static EHR labs only (Zero glucose sensors). (~₹0 incremental cost)

Also supports:
- Active inquiry ("Take fingerstick now") query generator.
- Compliance stress tests (e.g., dropping 20%-40% of meal logs to mimic real-world unlogged snacks).
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

class TierEmulator:
    def __init__(self, random_seed: int = 42):
        self.rng = np.random.RandomState(random_seed)
        
    def emulate_tier1_rich(self, df_5min: pd.DataFrame) -> pd.DataFrame:
        """
        Tier 1: Full CGM stream preserved.
        """
        df = df_5min.copy()
        df["tier"] = "T1_Rich"
        df["glucose_observed"] = df["glucose"]
        df["reading_type"] = "CGM_5min"
        df["minutes_since_last_reading"] = 0.0
        return df

    def emulate_tier2_frugal(
        self,
        df_5min: pd.DataFrame,
        schedule_type: str = "clinical_standard",  # "clinical_standard" (fasting + 3 pre-meals), "sparse_2" (fasting + lunch), "meal_anchored"
        noise_std: float = 0.07,  # 7% multiplicative meter noise (ISO 15197 compliant)
        meal_unlogged_dropout_prob: float = 0.0  # Stress testing parameter
    ) -> pd.DataFrame:
        """
        Tier 2: Discards continuous CGM stream; retains only scheduled fingerstick readings with glucometer noise.
        Computes 'glucose_observed' (sparse with NaN in between) and 'minutes_since_last_reading'.
        """
        df = df_5min.copy()
        df["tier"] = "T2_Frugal"
        df["glucose_observed"] = np.nan
        df["reading_type"] = "Unobserved"
        
        timestamps = pd.to_datetime(df["Timestamp"])
        hours = timestamps.dt.hour
        minutes = timestamps.dt.minute
        
        # Schedule 1: Fasting morning check (between 07:00 and 07:30)
        fasting_mask = (hours == 7) & (minutes <= 15)
        # Keep only the first reading per day for fasting
        days = timestamps.dt.date
        fasting_indices = []
        for d in days.unique():
            day_mask = (days == d) & fasting_mask
            if day_mask.any():
                fasting_indices.append(df.index[day_mask][0])
                
        # Schedule 2: Pre-meal fingerstick (at meal start or up to 15 min prior)
        meal_starts = df.index[(df["Carbs"] > 0) | (df["Meal Type"].notna())].tolist()
        
        # Apply meal log dropout stress test if enabled
        if meal_unlogged_dropout_prob > 0.0:
            kept_meals = [m for m in meal_starts if self.rng.rand() > meal_unlogged_dropout_prob]
            # Zero out unlogged meal carbs in the feature observation
            dropped_meals = set(meal_starts) - set(kept_meals)
            for dm in dropped_meals:
                df.loc[dm, "Carbs"] = 0.0
                df.loc[dm, "Calories"] = 0.0
            meal_starts = kept_meals

        # Selected fingerstick measurement points
        selected_indices = set(fasting_indices)
        if schedule_type in ["clinical_standard", "meal_anchored"]:
            for m_idx in meal_starts:
                # Pre-meal reading
                selected_indices.add(m_idx)
                if schedule_type == "clinical_standard":
                    # Also 2-hour post-meal check (+24 steps)
                    post_idx = m_idx + 24
                    if post_idx < len(df):
                        selected_indices.add(post_idx)
        elif schedule_type == "sparse_2":
            # Only fasting + first meal
            if meal_starts:
                selected_indices.add(meal_starts[0])
                
        # Populate glucometer readings with noise
        for idx in sorted(selected_indices):
            true_g = df.loc[idx, "glucose"]
            if pd.notna(true_g):
                # ISO 15197 multiplicative noise: G * (1 + N(0, 0.07^2))
                noise = self.rng.normal(0.0, noise_std)
                meter_g = float(np.clip(true_g * (1.0 + noise), 40.0, 400.0))
                df.loc[idx, "glucose_observed"] = round(meter_g, 1)
                df.loc[idx, "reading_type"] = "Glucometer_SMBG"
                
        # Forward fill the last observed reading and compute minutes since last reading
        last_observed = df["glucose_observed"].ffill()
        df["last_glucose_observed"] = last_observed
        
        # Calculate time elapsed since last reading
        minutes_since_last = []
        last_time = None
        for idx, row in df.iterrows():
            if pd.notna(row["glucose_observed"]):
                last_time = row["Timestamp"]
                minutes_since_last.append(0.0)
            elif last_time is not None:
                delta = (row["Timestamp"] - last_time).total_seconds() / 60.0
                minutes_since_last.append(delta)
            else:
                minutes_since_last.append(999.0)  # No reading yet today
                
        df["minutes_since_last_reading"] = minutes_since_last
        return df

    def emulate_tier3_triage(self, df_5min: pd.DataFrame) -> pd.DataFrame:
        """
        Tier 3: Completely zeroes out all glucose streams.
        Operates purely on Fitbit activity and static demographics/labs.
        """
        df = df_5min.copy()
        df["tier"] = "T3_Triage"
        df["glucose_observed"] = np.nan
        df["last_glucose_observed"] = np.nan
        df["reading_type"] = "None"
        df["minutes_since_last_reading"] = 9999.0
        return df
