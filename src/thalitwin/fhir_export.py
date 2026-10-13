"""
fhir_export.py
Ayushman Bharat Digital Mission (ABDM) HL7 FHIR R4 Clinical Resource Generator.

Generates ABDM-compliant FHIR R4 resources:
- Patient: Anonymized ABHA profile.
- Observation: Blood glucose readings mapped to LOINC 15074-8 and SNOMED-CT.
- Device: Glucometer SMBG or CGM device metadata.
- CarePlan: Stepped-Care calibration and lifestyle management protocol.
"""

from typing import Dict, List, Optional
import json
import datetime
import uuid

def generate_abdm_patient_resource(subject_id: int, age: int, gender: str) -> Dict:
    """Generates an ABDM FHIR R4 Patient resource."""
    return {
        "resourceType": "Patient",
        "id": f"thalitwin-pat-{subject_id:03d}",
        "identifier": [
            {
                "system": "https://healthid.ndhm.gov.in",
                "value": f"91-9999-{subject_id:04d}-0000"
            }
        ],
        "active": True,
        "gender": "male" if gender.upper().startswith("M") else "female",
        "birthDate": (datetime.date.today() - datetime.timedelta(days=int(age * 365.25))).isoformat(),
        "meta": {
            "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Patient"]
        }
    }

def generate_glucose_observation(
    subject_id: int,
    glucose_mg_dl: float,
    timestamp: str,
    tier: str = "T2_Frugal",
    is_excursion: bool = False
) -> Dict:
    """
    Generates an ABDM FHIR R4 Observation resource mapped to LOINC 15074-8 (Glucose in Blood).
    """
    obs_id = str(uuid.uuid4())
    interpretation_code = "H" if is_excursion or glucose_mg_dl > 180.0 else ("L" if glucose_mg_dl < 70.0 else "N")
    interpretation_text = "High" if interpretation_code == "H" else ("Low" if interpretation_code == "L" else "Normal")
    
    device_text = "Continuous Glucose Monitor (Dexcom G6)" if tier == "T1_Rich" else "Capillary Blood Glucose Meter (SMBG)"
    
    return {
        "resourceType": "Observation",
        "id": f"obs-glu-{obs_id[:8]}",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory",
                        "display": "Laboratory"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "15074-8",
                    "display": "Glucose [Mass/volume] in Blood"
                },
                {
                    "system": "http://snomed.info/sct",
                    "code": "434912009",
                    "display": "Blood glucose concentration"
                }
            ],
            "text": "Blood Glucose Reading"
        },
        "subject": {
            "reference": f"Patient/thalitwin-pat-{subject_id:03d}"
        },
        "effectiveDateTime": timestamp,
        "valueQuantity": {
            "value": round(float(glucose_mg_dl), 1),
            "unit": "mg/dL",
            "system": "http://unitsofmeasure.org",
            "code": "mg/dL"
        },
        "interpretation": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": interpretation_code,
                        "display": interpretation_text
                    }
                ]
            }
        ],
        "device": {
            "display": device_text
        },
        "referenceRange": [
            {
                "low": {"value": 70.0, "unit": "mg/dL"},
                "high": {"value": 180.0, "unit": "mg/dL"},
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/referencerange-meaning",
                            "code": "normal",
                            "display": "Normal Range"
                        }
                    ]
                }
            }
        ],
        "meta": {
            "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Observation"]
        }
    }

def generate_stepped_care_careplan(
    subject_id: int,
    phenotype: str,
    target_tier: str = "T2_Frugal"
) -> Dict:
    """
    Generates an ABDM FHIR R4 CarePlan resource outlining the stepped-care digital twin management plan.
    """
    return {
        "resourceType": "CarePlan",
        "id": f"careplan-{subject_id:03d}",
        "status": "active",
        "intent": "plan",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "73761001",
                        "display": "Colon management (disorder)"
                    }
                ],
                "text": "Stepped-Care Type 2 Diabetes Glycemic Management"
            }
        ],
        "title": "ThaliTwin Calibrate-Then-Step-Down Care Plan",
        "description": f"Initial 7-day CGM calibration followed by stepped maintenance on Tier 2 SMBG glucometer for {phenotype}.",
        "subject": {
            "reference": f"Patient/thalitwin-pat-{subject_id:03d}"
        },
        "period": {
            "start": datetime.date.today().isoformat(),
            "end": (datetime.date.today() + datetime.timedelta(days=90)).isoformat()
        },
        "goal": [
            {
                "display": "Maintain Time In Range (70-180 mg/dL) > 70% with <= 1 false alert per patient-day"
            }
        ],
        "activity": [
            {
                "detail": {
                    "kind": "ServiceRequest",
                    "code": {
                        "text": "Self-Monitoring Blood Glucose (SMBG) 3-4 times daily with Active Inquiry Prompts"
                    },
                    "status": "in-progress",
                    "doNotPerform": False
                }
            },
            {
                "detail": {
                    "kind": "NutritionOrder",
                    "code": {
                        "text": "Indian Thali Macro Optimization (ICMR-NIN IFCT 2017) with post-meal 15m walk counterfactuals"
                    },
                    "status": "in-progress",
                    "doNotPerform": False
                }
            }
        ],
        "meta": {
            "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/CarePlan"]
        }
    }

def export_abdm_bundle(subject_id: int, age: int, gender: str, phenotype: str, glucose_readings: List[Dict]) -> Dict:
    """Exports a unified ABDM FHIR R4 Transaction/Collection Bundle."""
    entries = []
    
    # 1. Patient
    pat = generate_abdm_patient_resource(subject_id, age, gender)
    entries.append({"resource": pat})
    
    # 2. CarePlan
    cp = generate_stepped_care_careplan(subject_id, phenotype)
    entries.append({"resource": cp})
    
    # 3. Observations
    for r in glucose_readings:
        obs = generate_glucose_observation(
            subject_id=subject_id,
            glucose_mg_dl=r["glucose"],
            timestamp=r.get("timestamp", datetime.datetime.now().isoformat()),
            tier=r.get("tier", "T2_Frugal"),
            is_excursion=r.get("is_excursion", False)
        )
        entries.append({"resource": obs})
        
    return {
        "resourceType": "Bundle",
        "id": f"abdm-bundle-{subject_id:03d}",
        "type": "collection",
        "timestamp": datetime.datetime.now().isoformat(),
        "meta": {
            "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Bundle"]
        },
        "entry": entries
    }
