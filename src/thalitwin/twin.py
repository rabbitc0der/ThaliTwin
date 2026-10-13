"""
twin.py
Empirical-Bayes Personalization & Digital Twin State Engine.

Implements:
1. Hierarchical Shrinkage: Blends population EHR prior with individual calibration meals:
      w_i = n_i / (n_i + kappa)
      theta_i* = w_i * individual_mean + (1 - w_i) * pop_prior
2. Learning Curve Engine: Evaluates error reduction as calibration days increase (N = 0, 2, 4, 7).
3. Digital Twin State Manager: Maintains patient state, tier, and history.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from thalitwin.features import FEATURE_COLUMNS
from thalitwin.models import ExcursionClassifier, TrajectoryForecaster

class DigitalTwinState:
    """Represents a single patient's active digital twin instance."""
    def __init__(
        self,
        subject_id: int,
        bio_profile: pd.Series,
        initial_tier: str = "T2_Frugal",
        shrinkage_kappa: float = 4.0
    ):
        self.subject_id = subject_id
        self.bio_profile = bio_profile
        self.active_tier = initial_tier
        self.kappa = shrinkage_kappa
        
        # Calibration state
        self.observed_meals_count = 0
        self.observed_residuals: List[float] = []
        self.personal_carb_sensitivity: float = 0.8  # Default prior ~0.8 mg/dL per gram carb
        self.personal_offset: float = 0.0
        
        # Recent trajectory state
        self.last_glucose: float = float(bio_profile.get("fasting_glucose", 100.0))
        self.last_timestamp: Optional[pd.Timestamp] = None
        self.minutes_since_reading: float = 0.0
        
    def get_shrinkage_weight(self) -> float:
        """Computes empirical Bayes weight w = n / (n + kappa)."""
        n = self.observed_meals_count
        return float(n / (n + self.kappa))
        
    def update_with_calibration_meal(
        self,
        carbs_g: float,
        actual_peak_rise: float,
        predicted_population_rise: float
    ):
        """
        Updates the twin with a new observed meal response during calibration.
        Adjusts personal offset and carb sensitivity.
        """
        residual = actual_peak_rise - predicted_population_rise
        self.observed_residuals.append(residual)
        self.observed_meals_count += 1
        
        w = self.get_shrinkage_weight()
        # Shrunk residual offset
        self.personal_offset = w * float(np.mean(self.observed_residuals))
        
        # Refine personal carb sensitivity if carbs > 10g
        if carbs_g >= 10.0:
            observed_sens = max(0.1, min(2.5, actual_peak_rise / carbs_g))
            # Smooth exponential update
            self.personal_carb_sensitivity = (1.0 - w) * 0.8 + w * observed_sens

    def get_personal_priors(self) -> Dict[str, float]:
        """Returns personalized priors dictionary for feature injection."""
        return {
            "carb_sensitivity": self.personal_carb_sensitivity,
            "observed_meals": float(self.observed_meals_count),
            "personal_offset": self.personal_offset
        }

class SteppedCareTwinEngine:
    """
    Core engine managing population forecasters and patient-specific shrinkage twins.
    """
    def __init__(self, shrinkage_kappa: float = 4.0, random_state: int = 42):
        self.kappa = shrinkage_kappa
        self.pop_classifier = ExcursionClassifier(random_state=random_state)
        self.pop_forecaster = TrajectoryForecaster(target_name="peak_rise", enforce_monotonicity=True, random_state=random_state)
        self.patient_twins: Dict[int, DigitalTwinState] = {}
        
    def register_patient(self, subject_id: int, bio_profile: pd.Series, tier: str = "T2_Frugal") -> DigitalTwinState:
        twin = DigitalTwinState(subject_id, bio_profile, initial_tier=tier, shrinkage_kappa=self.kappa)
        self.patient_twins[subject_id] = twin
        return twin

    def fit_population_models(self, X_train: pd.DataFrame, y_excursion: np.ndarray, y_peak: np.ndarray):
        """Fits the base population models on training folds."""
        self.pop_classifier.fit(X_train, y_excursion)
        self.pop_forecaster.fit(X_train, y_peak)

    def predict_personalized_peak(self, X_features: pd.DataFrame, subject_id: int) -> float:
        """
        Predicts postprandial peak rise with empirical-Bayes shrinkage offset.
        """
        pop_pred = float(self.pop_forecaster.predict(X_features)[0])
        twin = self.patient_twins.get(subject_id)
        if twin is None:
            return pop_pred
        return pop_pred + twin.personal_offset

    def predict_personalized_risk(self, X_features: pd.DataFrame, subject_id: int) -> float:
        """
        Predicts excursion probability, adjusted for personal offset.
        """
        pop_prob = float(self.pop_classifier.predict_proba(X_features)[0])
        twin = self.patient_twins.get(subject_id)
        if twin is None or twin.observed_meals_count == 0:
            return pop_prob
            
        # Logit adjustment for personal metabolic offset
        # A positive personal offset indicates a more brittle metabolic profile
        offset_shift = twin.personal_offset / 40.0  # Normalized shift
        adjusted_logit = np.log(max(1e-4, pop_prob / (1.0 - min(0.9999, pop_prob)))) + offset_shift
        adjusted_prob = float(1.0 / (1.0 + np.exp(-adjusted_logit)))
        return np.clip(adjusted_prob, 0.01, 0.99)
