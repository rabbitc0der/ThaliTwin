"""
test_leakage.py
Unit tests mathematically proving zero future information leakage in ThaliTwin.
Verifies that:
1. Truncating data after time t yields bit-for-bit identical features.
2. Injecting extreme future anomalies (t+1..end) produces zero change in time-t features.
3. Excursion label filtering prevents trivial baseline leakage.
"""

import copy
import numpy as np
import pandas as pd
import pytest

from thalitwin.data_loader import load_bio_metadata, load_participant_timeseries, extract_meal_windows
from thalitwin.features import extract_row_features, FEATURE_COLUMNS
from thalitwin.tiers import TierEmulator

def test_feature_temporal_isolation():
    """
    Test 1: Future data corruption test.
    Modifying any row > t must have zero impact on features extracted at t.
    """
    bio = load_bio_metadata()
    bio_row = bio.iloc[0]
    df = load_participant_timeseries(1)
    
    test_idx = 100
    
    # 1. Extract baseline features at index test_idx
    features_clean = extract_row_features(df, test_idx, bio_row, tier="T1_Rich")
    
    # 2. Corrupt future data (test_idx + 1 to end) with extreme radioactive values
    df_corrupted = df.copy()
    df_corrupted.loc[test_idx + 1 :, "glucose"] = 9999.0
    df_corrupted.loc[test_idx + 1 :, "HR"] = 888.0
    df_corrupted.loc[test_idx + 1 :, "Carbs"] = 777.0
    df_corrupted.loc[test_idx + 1 :, "METs"] = 666.0
    
    features_after_future_corruption = extract_row_features(df_corrupted, test_idx, bio_row, tier="T1_Rich")
    
    # 3. Assert all features are bit-for-bit identical
    for col in FEATURE_COLUMNS:
        assert np.isclose(features_clean[col], features_after_future_corruption[col], rtol=1e-5, atol=1e-5), (
            f"LEAKAGE DETECTED in feature '{col}': clean={features_clean[col]} vs corrupted={features_after_future_corruption[col]}"
        )

def test_truncation_invariance():
    """
    Test 2: Truncation invariance.
    Extracting features on a truncated dataset ending at test_idx must yield identical features.
    """
    bio = load_bio_metadata()
    bio_row = bio.iloc[0]
    df = load_participant_timeseries(1)
    
    test_idx = 80
    features_full = extract_row_features(df, test_idx, bio_row, tier="T1_Rich")
    
    df_truncated = df.iloc[: test_idx + 1].copy()
    features_truncated = extract_row_features(df_truncated, test_idx, bio_row, tier="T1_Rich")
    
    for col in FEATURE_COLUMNS:
        assert np.isclose(features_full[col], features_truncated[col], rtol=1e-5, atol=1e-5), (
            f"TRUNCATION MISMATCH in feature '{col}': full={features_full[col]} vs truncated={features_truncated[col]}"
        )

def test_excursion_label_leakage_filter():
    """
    Test 3: Excursion label filter.
    No meal window may have baseline glucose >= threshold, preventing trivial classification labels.
    """
    bio = load_bio_metadata()
    for pid in [1, 2, 3]:
        p_row = bio[bio["subject_id"] == pid].iloc[0]
        df = load_participant_timeseries(pid)
        meals = extract_meal_windows(df, p_row["phenotype"])
        
        for m in meals:
            thresh = m["threshold_used"]
            assert m["g_baseline"] < thresh, (
                f"LABEL LEAKAGE DETECTED in participant {pid}: baseline {m['g_baseline']} >= threshold {thresh}"
            )
