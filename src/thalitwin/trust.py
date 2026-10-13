"""
trust.py
Trust, Uncertainty, Calibration, and Active Inquiry Engine for ThaliTwin.

Modules:
1. Split-Conformal Prediction Intervals (finite-sample coverage guarantees).
2. Isotonic Calibration of Excursion Probabilities (ECE, Brier score).
3. Clinician Alert Budget Optimizer (false alerts per patient-day vs sensitivity).
4. Applicability Domain Guard & Abstention Policy.
5. Active Inquiry ('When to measure next') Advisory Engine.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

class ConformalIntervalEngine:
    """
    Split-conformal prediction engine providing coverage guarantees on unseen patients.
    """
    def __init__(self, coverage_level: float = 0.90):
        self.coverage_level = coverage_level
        self.quantile_q: float = 25.0  # Default reasonable residual in mg/dL
        self.is_calibrated: bool = False
        
    def calibrate_on_held_out(self, y_true: np.ndarray, y_pred: np.ndarray):
        """
        Calibrates conformal quantile using nonconformity scores R = |y_true - y_pred|.
        """
        residuals = np.abs(y_true - y_pred)
        n = len(residuals)
        if n == 0:
            return
            
        # Standard finite-sample conformal quantile index
        alpha = 1.0 - self.coverage_level
        q_level = min(1.0, np.ceil((n + 1) * (1.0 - alpha)) / n)
        self.quantile_q = float(np.quantile(residuals, q_level))
        self.is_calibrated = True

    def get_prediction_interval(
        self,
        point_prediction: float,
        tier: str = "T1_Rich",
        minutes_since_reading: float = 0.0
    ) -> Tuple[float, float, float]:
        """
        Returns (lower_bound, upper_bound, band_width).
        Band dynamically expands in Tier 2 / Tier 3 as time elapsed since last reading increases.
        """
        base_q = self.quantile_q
        
        # In Tier 2, uncertainty widens as time since last fingerstick increases
        if tier == "T2_Frugal":
            staleness_factor = min(2.5, 1.0 + 0.35 * (minutes_since_reading / 120.0))
            adjusted_q = base_q * staleness_factor
        elif tier == "T3_Triage":
            adjusted_q = base_q * 2.2  # High baseline uncertainty with zero glucose sensors
        else:  # T1_Rich
            adjusted_q = base_q
            
        lower = max(40.0, point_prediction - adjusted_q)
        upper = min(400.0, point_prediction + adjusted_q)
        return float(lower), float(upper), float(upper - lower)

class IsotonicRiskCalibrator:
    """
    Calibrates predicted probabilities using isotonic regression to eliminate overconfidence.
    """
    def __init__(self):
        self.iso = IsotonicRegression(out_of_bounds="clip", y_min=0.01, y_max=0.99)
        self.is_fitted = False
        
    def fit(self, raw_probs: np.ndarray, y_true: np.ndarray):
        self.iso.fit(raw_probs, y_true)
        self.is_fitted = True
        return self
        
    def calibrate(self, raw_probs: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            return raw_probs
        return self.iso.predict(raw_probs)

def compute_expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """
    Computes Expected Calibration Error (ECE) across n_bins.
    """
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    
    for i in range(n_bins):
        bin_mask = (y_prob >= bins[i]) & (y_prob < bins[i+1])
        bin_count = bin_mask.sum()
        if bin_count > 0:
            bin_acc = y_true[bin_mask].mean()
            bin_conf = y_prob[bin_mask].mean()
            ece += (bin_count / n) * np.abs(bin_acc - bin_conf)
            
    return float(ece)

class AlertBudgetOptimizer:
    """
    Optimizes alert threshold for clinical workflow to prevent alarm fatigue.
    Aims for <= 1 false alert per patient-day.
    """
    def __init__(self, target_max_false_alerts_per_day: float = 1.0):
        self.target_budget = target_max_false_alerts_per_day
        self.selected_threshold: float = 0.65
        
    def optimize(
        self,
        y_true: np.ndarray,
        y_probs: np.ndarray,
        total_patient_days: float
    ) -> Dict[str, float]:
        """
        Sweeps decision thresholds and selects the one satisfying the alert budget.
        """
        thresholds = np.linspace(0.20, 0.90, 71)
        best_thresh = 0.65
        best_diff = 999.0
        
        results_curve = []
        for th in thresholds:
            preds = (y_probs >= th).astype(int)
            fps = np.sum((preds == 1) & (y_true == 0))
            tps = np.sum((preds == 1) & (y_true == 1))
            total_positives = max(1, np.sum(y_true == 1))
            
            false_alerts_per_day = fps / max(1.0, total_patient_days)
            sensitivity = tps / total_positives
            
            diff = abs(false_alerts_per_day - self.target_budget)
            if false_alerts_per_day <= self.target_budget and diff < best_diff:
                best_diff = diff
                best_thresh = th
                
            results_curve.append({
                "threshold": float(th),
                "false_alerts_per_day": float(false_alerts_per_day),
                "sensitivity": float(sensitivity)
            })
            
        self.selected_threshold = float(best_thresh)
        return {
            "optimal_threshold": self.selected_threshold,
            "target_budget": self.target_budget,
            "curve": results_curve
        }

class ApplicabilityDomainGuard:
    """
    Abstains or raises clinical warnings when input vectors fall outside the reliable training domain.
    """
    @staticmethod
    def evaluate(
        carbs_g: float,
        minutes_since_reading: float,
        interval_width: float,
        tier: str
    ) -> Dict[str, any]:
        """
        Checks domain safety constraints.
        """
        reasons = []
        abstain = False
        
        # 1. Extreme meal carb overload
        if carbs_g > 130.0:
            reasons.append(f"Unusually high carb intake ({carbs_g}g > 130g). Beyond reliable linear absorption range.")
            
        # 2. Excessively stale fingerstick reading in Tier 2
        if tier == "T2_Frugal" and minutes_since_reading > 300.0:
            reasons.append(f"Last fingerstick is stale ({int(minutes_since_reading)} min old > 5 hours). Active state degraded.")
            
        # 3. High predictive uncertainty band
        if interval_width > 65.0:
            reasons.append(f"Prediction uncertainty band is wide ({interval_width:.1f} mg/dL). High metabolic variance.")
            
        if len(reasons) >= 2 or carbs_g > 160.0:
            abstain = True
            
        status = "ABSTAIN" if abstain else ("CAUTION" if len(reasons) > 0 else "VALID")
        return {
            "status": status,
            "abstain": abstain,
            "warnings": reasons
        }

class ActiveInquiryAdvisor:
    """
    Active Inquiry ('Next Best Reading'): Prompts the patient when a fingerstick
    reading would provide maximum information gain and reduce uncertainty.
    """
    @staticmethod
    def evaluate_measurement_prompt(
        tier: str,
        minutes_since_reading: float,
        upcoming_carbs_g: float,
        current_risk: float
    ) -> Dict[str, any]:
        if tier == "T1_Rich":
            return {"prompt_active": False, "reason": "Continuous CGM active. No fingerstick required."}
            
        # In Tier 2: Check active inquiry triggers
        prompt = False
        reasons = []
        urgency = "LOW"
        
        # Trigger 1: High carb meal imminent without recent pre-meal check
        if upcoming_carbs_g >= 35.0 and minutes_since_reading > 60.0:
            prompt = True
            urgency = "HIGH"
            reasons.append(f"High-carb meal imminent ({upcoming_carbs_g}g). Take pre-meal fingerstick to anchor twin baseline.")
            
        # Trigger 2: Postprandial 90-120 min evaluation window
        elif 90.0 <= minutes_since_reading <= 150.0 and current_risk >= 0.50:
            prompt = True
            urgency = "HIGH"
            reasons.append("Peak postprandial window active with elevated risk. Take post-meal reading to confirm peak.")
            
        # Trigger 3: General reading staleness (> 4 hours)
        elif minutes_since_reading > 240.0:
            prompt = True
            urgency = "MEDIUM"
            reasons.append("Over 4 hours since last reading. Take routine check to prevent uncertainty drift.")
            
        return {
            "prompt_active": prompt,
            "urgency": urgency,
            "recommendation": " ; ".join(reasons) if prompt else "Monitoring schedule optimal."
        }
