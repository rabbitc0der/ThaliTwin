"""
schemas.py
Pydantic v2 Strong Clinical & Machine Learning Schemas for ThaliTwin API.

Enforces physiological guardrails, LOINC/SNOMED coding, and type safety for
clinical decision support under Software as a Medical Device (SaMD) standards.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class PatientProfileResponse(BaseModel):
    """Patient clinical metadata and stepped-care onboarding state."""
    subject_id: int = Field(..., ge=1, le=100, description="Unique subject identifier")
    abha_id: str = Field(..., description="Ayushman Bharat Health Account ID (ABDM)")
    age: int = Field(..., ge=18, le=120, description="Age in years")
    gender: str = Field(..., description="Biological sex (male/female)")
    phenotype: str = Field(..., description="Metabolic phenotype (Normoglycemic, Prediabetes, Type 2 Diabetes)")
    baseline_hba1c: float = Field(..., ge=3.5, le=18.0, description="Baseline HbA1c percentage")
    fasting_glucose: float = Field(..., ge=40.0, le=400.0, description="Baseline fasting blood glucose in mg/dL")
    bmi: float = Field(..., ge=14.0, le=60.0, description="Body Mass Index in kg/m^2")
    active_tier: str = Field("T2_Frugal", description="Current stepped-care sensor tier")
    observed_calibration_meals: int = Field(..., ge=0, description="Number of observed calibration meals")
    shrinkage_weight_w: float = Field(..., ge=0.0, le=1.0, description="Empirical-Bayes shrinkage weight w = n/(n+4)")
    calibrated_carb_sensitivity: float = Field(..., description="Personalized carb sensitivity (mg/dL per gram carb)")
    personal_offset: float = Field(..., description="Personal residual glycemic offset in mg/dL")

class PredictExcursionRequest(BaseModel):
    """Input payload to evaluate postprandial glycemic excursion risk."""
    current_glucose: float = Field(..., ge=40.0, le=400.0, description="Current glucose in mg/dL at decision point")
    glucose_slope_15m: float = Field(0.0, ge=-10.0, le=10.0, description="Rate of change over last 15 min (mg/dL/min)")
    carbs_g: float = Field(..., ge=0.0, le=250.0, description="Carbohydrates in grams for planned meal")
    fiber_g: float = Field(0.0, ge=0.0, le=50.0, description="Dietary fiber in grams")
    protein_g: float = Field(15.0, ge=0.0, le=150.0, description="Protein in grams")
    fat_g: float = Field(10.0, ge=0.0, le=100.0, description="Fat in grams")
    glycemic_load: float = Field(15.0, ge=0.0, le=100.0, description="Estimated glycemic load of the meal")
    tier: str = Field("T2_Frugal", description="Sensor tier (T1_Rich, T2_Frugal, T3_Triage)")
    hour_of_day: float = Field(13.0, ge=0.0, le=23.99, description="Hour of meal consumption (0 to 24)")

class PredictExcursionResponse(BaseModel):
    """Output risk prediction, peak rise forecast, and conformal uncertainty ribbon."""
    predicted_risk: float = Field(..., ge=0.0, le=1.0, description="Calibrated probability of 2h glycemic excursion")
    optimal_alert_threshold: float = Field(..., description="Threshold calibrated under <= 1.0 false alert/patient-day")
    alert_active: bool = Field(..., description="Whether a clinical alert is triggered")
    predicted_peak_rise: float = Field(..., description="Predicted rise above baseline in mg/dL")
    predicted_peak_glucose: float = Field(..., description="Predicted absolute peak glucose in mg/dL")
    conformal_lower_bound: float = Field(..., description="90% Conformal finite-sample lower bound (mg/dL)")
    conformal_upper_bound: float = Field(..., description="90% Conformal finite-sample upper bound (mg/dL)")
    band_width_mg_dl: float = Field(..., description="Total uncertainty interval width in mg/dL")
    alert_budget_enforced: bool = Field(True, description="Enforces alert budget capping to prevent alarm fatigue")
    domain_guard_passed: bool = Field(True, description="Applicability domain bounds satisfied")

class WhatIfSimulateRequest(BaseModel):
    """Input payload for counterfactual diet and lifestyle intervention simulations."""
    dish_id_or_name: str = Field(..., description="Dish identifier (e.g. 'D01') or name from Thali Library")
    portion_factor: float = Field(1.0, ge=0.25, le=3.0, description="Portion multiplier (e.g. 1.0 = standard thali)")
    post_meal_walk_minutes: int = Field(0, ge=0, le=60, description="Brisk postprandial walk duration in minutes")
    current_glucose: Optional[float] = Field(None, ge=40.0, le=400.0, description="Current baseline glucose")
    compare_with_swap: bool = Field(True, description="Include recommended clinical swap counterfactual")
    tier: str = Field("T2_Frugal", description="Sensor tier for uncertainty ribbon scaling")

class ScenarioTrajectory(BaseModel):
    """Trajectory curve and uncertainty ribbon for a specific scenario."""
    dish_name: str
    calories_kcal: float
    net_carbs_g: float
    glycemic_load: float
    walk_minutes: int
    predicted_rise_mg_dl: float
    predicted_peak_mg_dl: float
    time_grid_minutes: List[float]
    glucose_curve: List[float]
    ribbon_lower: List[float]
    ribbon_upper: List[float]

class WhatIfSimulateResponse(BaseModel):
    """Comparative counterfactual simulation results."""
    primary_scenario: ScenarioTrajectory
    counterfactual_swap: Optional[ScenarioTrajectory] = None
    predicted_glycemic_attenuation_mg_dl: float = Field(0.0, description="Peak reduction achieved by swap/walk")
    clinical_recommendation: str

class ActiveInquiryRequest(BaseModel):
    """Checks for unexpected postprandial glucose velocity drift from unlogged meals."""
    last_glucose: float = Field(..., ge=40.0, le=400.0, description="Glucose reading at t0")
    current_glucose: float = Field(..., ge=40.0, le=400.0, description="Glucose reading at t1")
    elapsed_minutes: float = Field(..., ge=1.0, le=300.0, description="Minutes between readings")
    recent_activity_steps: int = Field(0, ge=0, description="Steps detected by wearable during window")

class ActiveInquiryResponse(BaseModel):
    """Response triggering Active Inquiry prompt when anomalous rise velocity is detected."""
    velocity_mg_dl_per_min: float = Field(..., description="Calculated rate of glucose rise")
    anomaly_detected: bool = Field(..., description="True if velocity exceeds threshold without logged meal")
    prompt_message: Optional[str] = Field(None, description="Conversational prompt for the patient")
    recommended_action: str

class AuditLogEntry(BaseModel):
    """Cryptographically tamper-evident audit record for medical AI governance."""
    audit_id: str
    timestamp_utc: str
    patient_id: int
    endpoint: str
    request_hash_sha256: str
    model_version: str
    latency_ms: float
    alert_triggered: bool
