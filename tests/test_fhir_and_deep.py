"""
test_fhir_and_deep.py
Tests ABDM FHIR R4 clinical compliance and deep baseline tensor shapes.
"""

import os
import sys
import pytest
import numpy as np
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from thalitwin.fhir_export import export_abdm_bundle
from thalitwin.deep_models import BiGRUMetabolicForecaster, MetabolicSequenceDataset

def test_abdm_fhir_bundle_structure():
    """Validates ABDM FHIR R4 Bundle resource types, LOINC codes, and structure."""
    glucose_samples = [
        {"glucose": 134.5, "timestamp": "2026-10-14T08:30:00", "tier": "T2_Frugal", "is_excursion": False},
        {"glucose": 195.0, "timestamp": "2026-10-14T12:45:00", "tier": "T2_Frugal", "is_excursion": True}
    ]
    bundle = export_abdm_bundle(
        subject_id=42,
        age=52,
        gender="female",
        phenotype="Type 2 Diabetes",
        glucose_readings=glucose_samples
    )
    
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert len(bundle["entry"]) == 4  # Patient, CarePlan, and 2 Observations
    
    # Check patient resource
    pat_entry = bundle["entry"][0]["resource"]
    assert pat_entry["resourceType"] == "Patient"
    assert pat_entry["gender"] == "female"
    assert pat_entry["identifier"][0]["system"] == "https://healthid.ndhm.gov.in"
    
    # Check CarePlan resource
    care_entry = bundle["entry"][1]["resource"]
    assert care_entry["resourceType"] == "CarePlan"
    assert care_entry["status"] == "active"
    
    # Check Observations with LOINC 15074-8
    obs1 = bundle["entry"][2]["resource"]
    assert obs1["resourceType"] == "Observation"
    assert obs1["code"]["coding"][0]["code"] == "15074-8"
    assert obs1["valueQuantity"]["value"] == 134.5
    assert obs1["valueQuantity"]["unit"] == "mg/dL"

def test_bigru_tensor_forward_shape():
    """Validates that BiGRU metabolic forecaster outputs 3 horizon targets."""
    model = BiGRUMetabolicForecaster(input_dim=4, hidden_dim=16)
    model.eval()
    
    batch_size = 8
    seq_len = 24  # 2 hours at 5-min intervals
    dummy_input = torch.randn(batch_size, seq_len, 4)
    
    with torch.no_grad():
        output = model(dummy_input)
        
    assert output.shape == (batch_size, 3)
    assert not torch.isnan(output).any()
