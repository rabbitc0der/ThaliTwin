"""
fetch_big_ideas.py
Streams the 16-participant PhysioNet BIG IDEAs Glycemic Wearable Cohort
(https://physionet.org/content/big-ideas-glycemic-wearable/1.0.0/)
directly from the public PhysioNet AWS S3 mirror (zero sign-in required).

Downloads:
1. Demographics table (ID, Gender, HbA1c)
2. Continuous Dexcom G6 glucose time-series (001 to 016)
Total download size is ~2.5 MB (skips multi-gigabyte raw accelerometer / BVP files).
"""

import os
import sys
import io
import urllib.request
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "BIG_IDEAs")
os.makedirs(RAW_DIR, exist_ok=True)

S3_BASE_URL = "https://physionet-open.s3.amazonaws.com/big-ideas-glycemic-wearable/1.0.0"

def fetch_demographics() -> pd.DataFrame:
    print("Fetching BIG IDEAs Demographics from S3 mirror...")
    url = f"{S3_BASE_URL}/Demographics.csv"
    data = urllib.request.urlopen(url).read()
    
    # PhysioNet hosts Demographics.csv as an XLSX zip archive
    try:
        df_demo = pd.read_excel(io.BytesIO(data))
    except Exception:
        df_demo = pd.read_csv(io.BytesIO(data), encoding="latin-1")
        
    out_demo_csv = os.path.join(RAW_DIR, "Demographics.csv")
    df_demo.to_csv(out_demo_csv, index=False)
    print(f"Saved {out_demo_csv} ({len(df_demo)} participants)")
    return df_demo

def fetch_dexcom_files(participant_ids=range(1, 17)):
    print(f"Streaming Dexcom G6 continuous recordings for {len(participant_ids)} participants...")
    downloaded = 0
    
    for pid in participant_ids:
        pid_str = f"{pid:03d}"
        target_dir = os.path.join(RAW_DIR, pid_str)
        os.makedirs(target_dir, exist_ok=True)
        target_file = os.path.join(target_dir, f"Dexcom_{pid_str}.csv")
        
        if os.path.exists(target_file) and os.path.getsize(target_file) > 1000:
            downloaded += 1
            continue
            
        url = f"{S3_BASE_URL}/{pid_str}/Dexcom_{pid_str}.csv"
        try:
            req = urllib.request.urlopen(url)
            content = req.read()
            with open(target_file, "wb") as f:
                f.write(content)
            downloaded += 1
            print(f"  [OK] Participant {pid_str}: {len(content) / 1024:.1f} KB -> {target_file}")
        except Exception as e:
            print(f"  [WARN] Failed fetching {pid_str}: {e}")
            
    print(f"Downloaded {downloaded}/{len(participant_ids)} participant Dexcom files.")

def main():
    print("=" * 75)
    print("PHYSIONET BIG IDEAs COHORT INGESTION")
    print("=" * 75)
    fetch_demographics()
    fetch_dexcom_files()
    print("\nIngestion complete. Dataset stored at data/raw/BIG_IDEAs/")

if __name__ == "__main__":
    main()
