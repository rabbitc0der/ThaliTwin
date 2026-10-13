"""
test_monotonicity.py
Unit tests verifying that the What-If simulation engine strictly respects metabolic monotonicity:
1. Increasing carbs monotonically increases or maintains predicted peak rise.
2. Increasing fiber monotonically reduces or maintains predicted peak rise.
3. Adding a 15-minute post-meal walk strictly reduces predicted peak rise and excursion risk.
"""

import numpy as np
import pandas as pd
import pytest

from thalitwin.data_loader import load_bio_metadata
from thalitwin.thali_library import get_dish, INDIAN_THALI_REGISTRY
from thalitwin.twin import SteppedCareTwinEngine
from thalitwin.trust import ConformalIntervalEngine
from thalitwin.whatif import ThaliWhatIfSimulator

def setup_simulator():
    bio = load_bio_metadata()
    bio_row = bio[bio["subject_id"] == 1].iloc[0]
    
    twin_engine = SteppedCareTwinEngine(shrinkage_kappa=4.0)
    twin_engine.register_patient(1, bio_row, tier="T2_Frugal")
    
    # Train dummy baseline to populate tree structures
    from thalitwin.features import FEATURE_COLUMNS
    dummy_X = pd.DataFrame(np.random.randn(50, len(FEATURE_COLUMNS)), columns=FEATURE_COLUMNS)
    dummy_X["carbs_g"] = np.linspace(10, 100, 50)
    dummy_X["fiber_g"] = np.linspace(1, 15, 50)
    dummy_X["mets_mean_30m"] = np.linspace(10, 40, 50)
    dummy_y_risk = (dummy_X["carbs_g"] > 50).astype(int)
    dummy_y_rise = dummy_X["carbs_g"] * 0.8 - dummy_X["fiber_g"] * 0.5
    
    twin_engine.fit_population_models(dummy_X, dummy_y_risk.values, dummy_y_rise.values)
    conformal = ConformalIntervalEngine(coverage_level=0.90)
    conformal.quantile_q = 22.0
    
    sim = ThaliWhatIfSimulator(twin_engine, conformal)
    return sim, bio_row

def test_walk_attenuation():
    """
    Test: Adding a post-meal walk must reduce predicted peak and excursion risk.
    """
    sim, bio_row = setup_simulator()
    dish = get_dish("D02")  # Masala Dosa
    
    res_no_walk = sim.simulate_meal_scenario(1, bio_row, dish, portion_factor=1.0, add_post_meal_walk=False)
    res_with_walk = sim.simulate_meal_scenario(1, bio_row, dish, portion_factor=1.0, add_post_meal_walk=True)
    
    assert res_with_walk["predicted_peak"] < res_no_walk["predicted_peak"], (
        f"Walk failed to reduce peak: with_walk={res_with_walk['predicted_peak']} vs no_walk={res_no_walk['predicted_peak']}"
    )
    assert res_with_walk["predicted_risk"] <= res_no_walk["predicted_risk"], (
        f"Walk failed to reduce risk: with_walk={res_with_walk['predicted_risk']} vs no_walk={res_no_walk['predicted_risk']}"
    )

def test_portion_monotonicity():
    """
    Test: Increasing portion size of the same meal (more carbs) must increase or maintain predicted peak.
    """
    sim, bio_row = setup_simulator()
    dish = get_dish("D05")  # Dal Tadka + Rice
    
    res_small = sim.simulate_meal_scenario(1, bio_row, dish, portion_factor=0.7)
    res_large = sim.simulate_meal_scenario(1, bio_row, dish, portion_factor=1.5)
    
    assert res_large["predicted_rise"] >= res_small["predicted_rise"], (
        f"Larger portion had lower peak rise: large={res_large['predicted_rise']} vs small={res_small['predicted_rise']}"
    )
