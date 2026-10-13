"""
fetch_cgmacros.py
Automated extractor for CGMacros PhysioNet dataset.
Streams ONLY tabular CSV files from the public AWS S3 mirror, bypassing the 600MB+ photo archive.
"""

import os
import sys
from remotezip import RemoteZip

S3_ZIP_URL = "https://physionet-open.s3.amazonaws.com/cgmacros/1.0.0/CGMacros_dateshifted365.zip"
TARGET_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

def fetch_cgmacros():
    os.makedirs(TARGET_DIR, exist_ok=True)
    print(f"Connecting to PhysioNet AWS S3 mirror: {S3_ZIP_URL}")
    
    with RemoteZip(S3_ZIP_URL) as z:
        all_files = z.namelist()
        csv_files = [f for f in all_files if f.endswith(".csv")]
        print(f"Found {len(csv_files)} tabular CSV files. Total archive has {len(all_files)} files (mostly images).")
        print(f"Extracting CSV files to {os.path.abspath(TARGET_DIR)}...")
        
        extracted_count = 0
        for i, csv_path in enumerate(csv_files, 1):
            filename = os.path.basename(csv_path)
            out_path = os.path.join(TARGET_DIR, csv_path)
            if os.path.exists(out_path):
                print(f"[{i}/{len(csv_files)}] Skipping {filename} (already exists)")
                continue
            z.extract(csv_path, TARGET_DIR)
            extracted_count += 1
            if i % 5 == 0 or i == len(csv_files):
                print(f"[{i}/{len(csv_files)}] Extracted {filename}")
                
        print(f"Extraction complete! Successfully extracted {extracted_count} new CSV files.")

if __name__ == "__main__":
    fetch_cgmacros()
