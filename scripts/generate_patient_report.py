"""
generate_patient_report.py
CLI tool to generate hospital-ready 2-page AGP & Stepped-Care Transition Certificates
for patients completing their 7-day CGM induction.

Usage:
    python scripts/generate_patient_report.py --subject-id 1
    python scripts/generate_patient_report.py --all-samples
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from thalitwin.report_generator import ClinicalReportGenerator

def main():
    parser = argparse.ArgumentParser(description="Generate ThaliTwin Clinical Transition PDF Reports")
    parser.add_argument("--subject-id", type=int, default=1, help="Participant subject ID (1 to 45)")
    parser.add_argument("--all-samples", action="store_true", help="Generate reports for representative cohort patients (1, 2, 5)")
    args = parser.parse_args()
    
    print("=" * 75)
    print("THALITWIN CLINICAL TRANSITION REPORT GENERATOR")
    print("=" * 75)
    
    generator = ClinicalReportGenerator()
    
    targets = [args.subject_id] if not args.all_samples else [1, 2, 5]
    
    for pid in targets:
        print(f"\nGenerating Clinical Report for Patient TT-IND-{pid:03d}...")
        try:
            pdf_path = generator.generate_patient_transition_report(pid)
            size_kb = os.path.getsize(pdf_path) / 1024
            print(f"  [SUCCESS] Created {pdf_path} ({size_kb:.1f} KB)")
        except Exception as e:
            print(f"  [ERROR] Failed for patient {pid}: {e}")
            
    print("\n" + "=" * 75)
    print("REPORTS GENERATION COMPLETE: Check docs/reports/ for output PDFs")
    print("=" * 75)

if __name__ == "__main__":
    main()
