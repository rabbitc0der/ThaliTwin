"""
test_mechanistic_and_drift.py
Unit tests for the mechanistic gut absorption engine and automated covariate drift monitor.
Happiest Health Digital Twin Challenge 2026.
"""

import numpy as np
import pytest
from thalitwin.mechanistic import GutAbsorptionEngine
from thalitwin.drift_monitor import (
    compute_psi,
    compute_wasserstein_1d,
    SteppedCareDriftMonitor,
)


def test_mechanistic_gut_absorption_dynamics():
    """
    Validates that the biophysical ODE gut absorption simulation correctly models
    fiber attenuation and glycemic index dynamics.
    """
    engine = GutAbsorptionEngine()

    # 1. High-GI Refined Meal (White Rice / Sugar Syrup)
    sim_refined = engine.simulate(
        carbs_g=50.0,
        fiber_g=0.5,
        fat_g=2.0,
        glycemic_index=85.0,
        duration_minutes=180
    )

    # 2. High-Fiber Complex Indian Thali (Ragi Mudde / Sprouted Moong / Greens)
    sim_fibrous = engine.simulate(
        carbs_g=50.0,
        fiber_g=9.0,
        fat_g=6.0,
        glycemic_index=40.0,
        duration_minutes=180
    )

    # Biophysical Assertion 1: High fiber + low GI must attenuate peak absorption rate
    assert sim_fibrous.peak_ra_value < sim_refined.peak_ra_value, (
        f"Expected fibrous peak ({sim_fibrous.peak_ra_value}) < refined peak ({sim_refined.peak_ra_value})"
    )

    # Biophysical Assertion 2: High fiber must delay time-to-peak (t_max)
    assert sim_fibrous.peak_ra_time_min >= sim_refined.peak_ra_time_min, (
        f"Expected fibrous t_max ({sim_fibrous.peak_ra_time_min}) >= refined t_max ({sim_refined.peak_ra_time_min})"
    )

    # Biophysical Assertion 3: High fiber must prolong gastric half-life
    assert sim_fibrous.absorption_half_life_min > sim_refined.absorption_half_life_min

    # Biophysical Assertion 4: Conservation of mass - total absorbed glucose must be positive and bounded by meal carbs
    assert 0.0 < sim_fibrous.total_glucose_absorbed_g <= 50.0


def test_mechanistic_thali_comparison():
    """Validates the head-to-head thali comparative calculation."""
    engine = GutAbsorptionEngine()
    comparison = engine.compare_thalis(
        thali_a_name="Refined Maida Paratha",
        thali_a_macros={"carbs": 60.0, "fiber": 1.0, "fat": 12.0, "glycemic_index": 80.0},
        thali_b_name="High-Fiber Bajra Thali",
        thali_b_macros={"carbs": 60.0, "fiber": 8.0, "fat": 8.0, "glycemic_index": 45.0}
    )

    assert "clinical_impact" in comparison
    assert comparison["clinical_impact"]["flattening_beneficial"] is True
    assert comparison["clinical_impact"]["peak_absorption_reduction_percent"] > 0


def test_drift_monitor_stable_distribution():
    """Verifies that statistically identical distributions produce low PSI and stable status."""
    np.random.seed(42)
    baseline = np.random.normal(loc=130.0, scale=25.0, size=500)
    maintenance = np.random.normal(loc=131.0, scale=24.5, size=500)

    monitor = SteppedCareDriftMonitor()
    report = monitor.evaluate_patient_drift(
        patient_id=1,
        baseline_glucose=baseline,
        maintenance_glucose=maintenance
    )

    assert report.psi_score < 0.10
    assert report.status == "STABLE"
    assert report.recalibration_needed is False


def test_drift_monitor_severe_decompensation():
    """Verifies that severe clinical shift triggers recalibration flag."""
    np.random.seed(42)
    # Baseline: well controlled around 125 mg/dL
    baseline = np.random.normal(loc=125.0, scale=20.0, size=500)
    # Decompensation (e.g. infection / steroid medication): shifted to 185 mg/dL with high variance
    maintenance = np.random.normal(loc=185.0, scale=45.0, size=500)

    monitor = SteppedCareDriftMonitor()
    report = monitor.evaluate_patient_drift(
        patient_id=1,
        baseline_glucose=baseline,
        maintenance_glucose=maintenance
    )

    assert report.psi_score >= 0.25
    assert report.status == "SEVERE_DRIFT"
    assert report.recalibration_needed is True
    assert "CGM Re-Induction" in report.action_required


def test_multivariate_drift_reporting():
    """Verifies multivariate feature drift calculation across glucose, carbs, and steps."""
    np.random.seed(42)
    base_data = {
        "glucose": np.random.normal(120, 20, 600),
        "carbs": np.random.normal(55, 15, 600),
        "steps": np.random.normal(6000, 1500, 600)
    }
    # Steady state maintenance with minor measurement variance
    maint_data = {
        "glucose": base_data["glucose"] + np.random.normal(0, 2, 600),
        "carbs": base_data["carbs"] + np.random.normal(0, 1, 600),
        "steps": base_data["steps"] + np.random.normal(0, 100, 600)
    }

    monitor = SteppedCareDriftMonitor()
    res = monitor.evaluate_multi_feature_drift(
        patient_id=7,
        baseline_dict=base_data,
        maintenance_dict=maint_data
    )

    assert res["patient_id"] == 7
    assert res["overall_status"] == "STABLE"
    assert res["recalibration_recommended"] is False
    assert "glucose" in res["features"]

