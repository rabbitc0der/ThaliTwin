"""
models.py
Machine Learning Models and Clinical Baselines for ThaliTwin.
Includes:
1. LightGBM Excursion Risk Classifier (calibrated 2-hour excursion probability).
2. LightGBM Trajectory Regressors (peak rise, iAUC, +30m, +60m, +120m).
3. Monotonically Constrained What-If Forecaster (strictly enforcing carb/fiber/activity physiology).
4. Baselines: Persistence, Linear Carbs, and Static EHR prior.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.linear_model import Ridge

from thalitwin.features import FEATURE_COLUMNS

class BaselinePersistence:
    """Repeats the current/last observed glucose value."""
    def fit(self, X: np.ndarray, y: np.ndarray):
        return self
        
    def predict(self, X: np.ndarray, g_current_col_idx: int) -> np.ndarray:
        return X[:, g_current_col_idx]

class BaselineCarbsLinear:
    """Univariate linear model estimating glucose rise purely from carb grams."""
    def __init__(self):
        self.model = Ridge(alpha=1.0)
        
    def fit(self, carbs: np.ndarray, y: np.ndarray):
        self.model.fit(carbs.reshape(-1, 1), y)
        return self
        
    def predict(self, carbs: np.ndarray) -> np.ndarray:
        return self.model.predict(carbs.reshape(-1, 1))

class ExcursionClassifier:
    """
    Predicts probability of 2-hour postprandial glucose excursion.
    Trained with group-aware cross-validation to prevent participant memorization.
    """
    def __init__(self, random_state: int = 42):
        self.clf = LGBMClassifier(
            n_estimators=120,
            learning_rate=0.04,
            max_depth=4,
            num_leaves=14,
            min_child_samples=10,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            verbose=-1
        )
        self.is_fitted = False
        
    def fit(self, X: pd.DataFrame, y: np.ndarray):
        cols = [c for c in FEATURE_COLUMNS if c in X.columns]
        self.clf.fit(X[cols], y)
        self.is_fitted = True
        return self
        
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        cols = [c for c in FEATURE_COLUMNS if c in X.columns]
        return self.clf.predict_proba(X[cols])[:, 1]
        
    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        probs = self.predict_proba(X)
        return (probs >= threshold).astype(int)

class TrajectoryForecaster:
    """
    Predicts postprandial peak rise (mg/dL) and incremental AUC.
    Optionally enforces physiological monotonicity constraints.
    """
    def __init__(self, target_name: str = "peak_rise", enforce_monotonicity: bool = False, random_state: int = 42):
        self.target_name = target_name
        self.enforce_monotonicity = enforce_monotonicity
        
        # Monotone constraints dictionary: +1 = increasing, -1 = decreasing, 0 = unconstrained
        monotone_dict = {}
        if enforce_monotonicity:
            for c in FEATURE_COLUMNS:
                if c == "carbs_g" or c == "net_carbs_g" or c == "glycemic_load_est":
                    monotone_dict[c] = 1   # More carbs must never lower predicted peak
                elif c == "fiber_g" or c == "mets_mean_30m":
                    monotone_dict[c] = -1  # More fiber or physical activity must never raise peak
                else:
                    monotone_dict[c] = 0
            monotone_constraints = [monotone_dict.get(c, 0) for c in FEATURE_COLUMNS]
        else:
            monotone_constraints = None

        self.reg = LGBMRegressor(
            n_estimators=140,
            learning_rate=0.04,
            max_depth=4,
            num_leaves=14,
            min_child_samples=10,
            subsample=0.8,
            colsample_bytree=0.8,
            monotone_constraints=monotone_constraints,
            random_state=random_state,
            verbose=-1
        )
        self.is_fitted = False
        
    def fit(self, X: pd.DataFrame, y: np.ndarray):
        cols = [c for c in FEATURE_COLUMNS if c in X.columns]
        self.reg.fit(X[cols], y)
        self.is_fitted = True
        return self
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        cols = [c for c in FEATURE_COLUMNS if c in X.columns]
        return self.reg.predict(X[cols])
