"""
metrics.py
Clinical Endocrinology Metrics, Statistical ML Evaluators, and Stepped-Care Performance-per-Rupee Economic Frontier.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, mean_squared_error, mean_absolute_error

def compute_agp_clinical_metrics(glucose_series: pd.Series) -> Dict[str, float]:
    """
    Computes international consensus Ambulatory Glucose Profile (AGP) metrics.
    """
    g = glucose_series.dropna()
    if len(g) == 0:
        return {"tir_pct": 0.0, "tar_pct": 0.0, "tbr_pct": 0.0, "mean_glucose": 0.0, "gmi_pct": 0.0, "cv_pct": 0.0}
        
    n = len(g)
    tir = float((g.between(70.0, 180.0)).sum() / n * 100.0)
    tar = float((g > 180.0).sum() / n * 100.0)
    tbr = float((g < 70.0).sum() / n * 100.0)
    mean_g = float(g.mean())
    sd_g = float(g.std()) if n > 1 else 0.0
    cv = float((sd_g / mean_g * 100.0) if mean_g > 0 else 0.0)
    # GMI = 3.31 + 0.02392 * mean_glucose
    gmi = float(3.31 + 0.02392 * mean_g)
    
    return {
        "tir_pct": round(tir, 1),
        "tar_pct": round(tar, 1),
        "tbr_pct": round(tbr, 1),
        "mean_glucose": round(mean_g, 1),
        "gmi_pct": round(gmi, 2),
        "cv_pct": round(cv, 1)
    }

def evaluate_classification_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> Dict[str, float]:
    """
    Computes AUROC, AUPRC, Brier Score, Sensitivity, and Specificity.
    """
    y_pred = (y_prob >= threshold).astype(int)
    
    try:
        auroc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        auroc = 0.50
        
    try:
        auprc = float(average_precision_score(y_true, y_prob))
    except Exception:
        auprc = float(np.mean(y_true))
        
    brier = float(brier_score_loss(y_true, y_prob))
    
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    
    sens = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    
    return {
        "auroc": round(auroc, 3),
        "auprc": round(auprc, 3),
        "brier_score": round(brier, 4),
        "sensitivity": round(sens, 3),
        "specificity": round(spec, 3)
    }

def evaluate_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Computes RMSE, MAE, and MARD (%).
    """
    valid = (~np.isnan(y_true)) & (~np.isnan(y_pred))
    yt = y_true[valid]
    yp = y_pred[valid]
    
    if len(yt) == 0:
        return {"rmse": 0.0, "mae": 0.0, "mard": 0.0}
        
    rmse = float(np.sqrt(mean_squared_error(yt, yp)))
    mae = float(mean_absolute_error(yt, yp))
    mard = float(np.mean(np.abs(yt - yp) / np.maximum(40.0, yt)) * 100.0)
    
    return {
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "mard_pct": round(mard, 2)
    }

def compute_performance_per_rupee(
    tier_sensitivities: Dict[str, float],
    monthly_costs: Optional[Dict[str, float]] = None
) -> List[Dict[str, any]]:
    """
    Computes economic cost-effectiveness frontier across the 3 stepped-care tiers.
    """
    if monthly_costs is None:
        monthly_costs = {
            "T1_Rich": 10000.0,   # Continuous CGM: ~2 sensors @ ₹5,000 each
            "T2_Frugal": 1200.0,  # SMBG strips: 60-90 strips/mo @ ₹15-20/strip
            "T3_Triage": 100.0    # No consumables; negligible amortized cost
        }
        
    rows = []
    for tier, sens in tier_sensitivities.items():
        cost = monthly_costs.get(tier, 1000.0)
        # Sensitivity retained relative to T1
        t1_sens = tier_sensitivities.get("T1_Rich", 0.85)
        rel_retained = round((sens / t1_sens) * 100.0, 1) if t1_sens > 0 else 0.0
        cost_savings_pct = round(((monthly_costs["T1_Rich"] - cost) / monthly_costs["T1_Rich"]) * 100.0, 1)
        eff_index = round((sens / cost) * 10000.0, 2)
        
        rows.append({
            "tier": tier,
            "monthly_cost_inr": cost,
            "sensitivity": sens,
            "relative_accuracy_retained_pct": rel_retained,
            "cost_savings_vs_cgm_pct": cost_savings_pct,
            "efficiency_score": eff_index
        })
        
    return rows
