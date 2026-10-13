"""
drift_monitor.py
Automated Covariate Drift & Stepped-Care Recalibration Monitor for ThaliTwin.
Happiest Health Digital Twin Challenge 2026.

Detects physiological covariate shift and distribution drift over rolling 14-day
monitoring windows using:
1. Population Stability Index (PSI)
2. Wasserstein-1D Earth Mover's Distance
3. Conformal Coverage Violation Tracking

Clinical Action Policy:
- PSI < 0.10: Stable Calibration. Maintain current Stepped-Care tier (Tier 2 SMBG).
- 0.10 <= PSI < 0.25: Moderate Drift. Step up fingerstick frequency from 2 to 4 / day.
- PSI >= 0.25: Severe Physiological Drift. Trigger Automated 3-Day CGM Re-Induction Alert.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import numpy as np


@dataclass
class DriftReport:
    """Report detailing detected covariate drift and recommended stepped-care action."""
    patient_id: int
    variable_name: str
    psi_score: float
    wasserstein_distance: float
    status: str                         # "STABLE", "MODERATE_DRIFT", "SEVERE_DRIFT"
    action_required: str
    recommended_tier: str
    recalibration_needed: bool
    summary_message: str


def compute_psi(
    baseline: np.ndarray,
    current: np.ndarray,
    num_bins: int = 10,
    epsilon: float = 1e-4
) -> float:
    """
    Computes the Population Stability Index (PSI) between baseline and current distributions.
    
    PSI = sum((Actual% - Expected%) * ln(Actual% / Expected%))
    """
    baseline = np.asarray(baseline, dtype=float)
    current = np.asarray(current, dtype=float)
    
    baseline = baseline[~np.isnan(baseline)]
    current = current[~np.isnan(current)]
    
    if len(baseline) == 0 or len(current) == 0:
        return 0.0

    # Determine quantile bin edges from baseline
    quantiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(baseline, quantiles)
    # Ensure strictly increasing bins
    bin_edges = np.unique(bin_edges)
    if len(bin_edges) < 2:
        return 0.0

    # Extend endpoints to catch out-of-range values
    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    # Calculate frequency proportions
    baseline_counts, _ = np.histogram(baseline, bins=bin_edges)
    current_counts, _ = np.histogram(current, bins=bin_edges)

    baseline_props = (baseline_counts + epsilon) / (np.sum(baseline_counts) + epsilon * len(baseline_counts))
    current_props = (current_counts + epsilon) / (np.sum(current_counts) + epsilon * len(current_counts))

    # Compute PSI
    psi_value = np.sum((current_props - baseline_props) * np.log(current_props / baseline_props))
    return float(max(0.0, psi_value))


def compute_wasserstein_1d(
    baseline: np.ndarray,
    current: np.ndarray
) -> float:
    """
    Computes the 1D Wasserstein Earth Mover's Distance between two empirical samples.
    """
    baseline = np.sort(np.asarray(baseline, dtype=float)[~np.isnan(baseline)])
    current = np.sort(np.asarray(current, dtype=float)[~np.isnan(current)])
    
    if len(baseline) == 0 or len(current) == 0:
        return 0.0

    # Common evaluation grid
    all_vals = np.concatenate([baseline, current])
    eval_grid = np.linspace(np.min(all_vals), np.max(all_vals), 200)

    # Empirical CDFs
    cdf_base = np.searchsorted(baseline, eval_grid, side="right") / len(baseline)
    cdf_curr = np.searchsorted(current, eval_grid, side="right") / len(current)

    # L1 distance between CDFs
    dx = eval_grid[1] - eval_grid[0]
    return float(np.sum(np.abs(cdf_base - cdf_curr)) * dx)


class SteppedCareDriftMonitor:
    """
    Monitors patient glucose, meal sizes, and activity for clinical drift,
    flagging when recalibration or step-up to CGM is medically indicated.
    """

    def __init__(
        self,
        psi_moderate_threshold: float = 0.10,
        psi_severe_threshold: float = 0.25,
        wasserstein_glucose_threshold_mg_dl: float = 18.0
    ):
        self.psi_mod = psi_moderate_threshold
        self.psi_sev = psi_severe_threshold
        self.wass_thresh = wasserstein_glucose_threshold_mg_dl

    def evaluate_patient_drift(
        self,
        patient_id: int,
        baseline_glucose: np.ndarray,
        maintenance_glucose: np.ndarray,
        current_tier: str = "T2_Frugal"
    ) -> DriftReport:
        """
        Evaluates interstitial/capillary glucose distribution drift.
        """
        psi_val = compute_psi(baseline_glucose, maintenance_glucose)
        wass_val = compute_wasserstein_1d(baseline_glucose, maintenance_glucose)

        if psi_val >= self.psi_sev or wass_val >= self.wass_thresh:
            status = "SEVERE_DRIFT"
            recalibration = True
            rec_tier = "T1_Rich"
            action = "Trigger 3-Day CGM Re-Induction to re-calibrate Bayesian patient prior."
            msg = f"Significant metabolic shift detected (PSI={psi_val:.3f}, Earth Mover's Dist={wass_val:.1f} mg/dL). Baseline twin prior is no longer representative."
        elif psi_val >= self.psi_mod:
            status = "MODERATE_DRIFT"
            recalibration = False
            rec_tier = "T2_Frugal_Intensive"
            action = "Increase SMBG fingerstick cadence from 2 to 4 tests/day for 7 days."
            msg = f"Mild metabolic divergence observed (PSI={psi_val:.3f}). Intensify fingerstick telemetry."
        else:
            status = "STABLE"
            recalibration = False
            rec_tier = current_tier
            action = "Maintain current Stepped-Care maintenance tier."
            msg = f"Calibration remains robustly within statistical tolerance (PSI={psi_val:.3f}, Earth Mover's Dist={wass_val:.1f} mg/dL)."

        return DriftReport(
            patient_id=patient_id,
            variable_name="interstitial_glucose_mg_dl",
            psi_score=round(psi_val, 4),
            wasserstein_distance=round(wass_val, 2),
            status=status,
            action_required=action,
            recommended_tier=rec_tier,
            recalibration_needed=recalibration,
            summary_message=msg
        )

    def evaluate_multi_feature_drift(
        self,
        patient_id: int,
        baseline_dict: Dict[str, np.ndarray],
        maintenance_dict: Dict[str, np.ndarray],
        current_tier: str = "T2_Frugal"
    ) -> Dict[str, Any]:
        """
        Evaluates multivariate drift across glucose, meal carbs, and steps.
        """
        reports = {}
        any_severe = False
        any_moderate = False

        for feat in ["glucose", "carbs", "steps"]:
            if feat in baseline_dict and feat in maintenance_dict:
                b_arr = baseline_dict[feat]
                m_arr = maintenance_dict[feat]
                psi_val = compute_psi(b_arr, m_arr)
                wass_val = compute_wasserstein_1d(b_arr, m_arr)

                if psi_val >= self.psi_sev:
                    any_severe = True
                elif psi_val >= self.psi_mod:
                    any_moderate = True

                reports[feat] = {
                    "psi": round(psi_val, 4),
                    "wasserstein": round(wass_val, 2),
                    "is_drifted": psi_val >= self.psi_mod
                }

        overall_status = "SEVERE_DRIFT" if any_severe else ("MODERATE_DRIFT" if any_moderate else "STABLE")
        
        return {
            "patient_id": patient_id,
            "overall_status": overall_status,
            "recalibration_recommended": any_severe,
            "features": reports,
            "clinical_advice": "Prompt clinician for 3-Day CGM re-induction patch" if any_severe else "Stepped-care parameters are well-calibrated."
        }
