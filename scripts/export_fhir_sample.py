"""
export_fhir_sample.py
Generates official ABDM HL7 FHIR R4 clinical bundles in docs/fhir/
for demonstration of national digital health interoperability.
"""

import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from thalitwin.fhir_export import export_abdm_bundle
from thalitwin.data_loader import load_bio_metadata, load_participant_timeseries

FHIR_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "fhir")
os.makedirs(FHIR_DIR, exist_ok=True)

def main():
    print(f"Generating ABDM FHIR R4 clinical records in {FHIR_DIR}...")
    bio = load_bio_metadata()
    
    # Export for Patient 1 (T2D profile) and Patient 2 (Prediabetes)
    for pid in [1, 2, 5]:
        p_row = bio[bio["subject_id"] == pid].iloc[0]
        df = load_participant_timeseries(pid)
        
        # Sample 5 readings from trial
        sample_readings = []
        for _, r in df.head(10).iterrows():
            if pd.notna(r["glucose"]):
                sample_readings.append({
                    "glucose": float(r["glucose"]),
                    "timestamp": r["Timestamp"].isoformat(),
                    "tier": "T2_Frugal",
                    "is_excursion": bool(r["glucose"] > 180.0)
                })
                if len(sample_readings) >= 5:
                    break
                    
        bundle = export_abdm_bundle(
            subject_id=pid,
            age=int(p_row["age"]),
            gender=str(p_row["gender"]),
            phenotype=str(p_row["phenotype"]),
            glucose_readings=sample_readings
        )
        
        out_file = os.path.join(FHIR_DIR, f"ABDM_Bundle_Patient_{pid:03d}.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bundle, f, indent=2)
            
        print(f"Exported {out_file} with {len(bundle['entry'])} FHIR R4 resources.")

if __name__ == "__main__":
    import pandas as pd
    main()
