"""
test_report_generator.py
Unit tests verifying the Clinical PDF Transition Report Generator.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from thalitwin.report_generator import ClinicalReportGenerator

def test_generate_patient_transition_report(tmp_path):
    """Tests generating a 2-page AGP & Stepped-Care Transition Report."""
    generator = ClinicalReportGenerator(output_dir=str(tmp_path))
    pdf_path = generator.generate_patient_transition_report(subject_id=1)
    
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 20000  # Multi-page high-DPI PDF
    assert pdf_path.endswith("ThaliTwin_Clinical_Report_Patient_001.pdf")
