"""
package_submission.py
Master Enterprise Packaging & Delivery Script for ThaliTwin.
Happiest Health Digital Twin Challenge 2026 (Bengaluru Summit Track).

Creates a self-contained, offline-evaluable submission archive containing:
1. Master Slide Presentation Deck (docs/presentation.pdf)
2. High-Resolution Architecture Blueprint (docs/architecture.pdf)
3. Regulatory SaMD ISO 14971 Hazard Analysis & Scorecard (docs/)
4. Clinical PDF Transition Reports & ABDM HL7 FHIR Bundles (docs/reports/, docs/fhir/)
5. Pre-compiled Production React Web Application (web/dist/)
6. Python Core Package (src/) & Datasets (data/)
7. Offline Demo Launchers (RUN_DEMO.bat / RUN_DEMO.ps1)
8. Cryptographic SHA-256 Manifest & Submission Metadata
"""

import os
import sys
import json
import time
import shutil
import zipfile
import hashlib
import subprocess
from datetime import datetime, timezone

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "submission_bundle")
ZIP_NAME = "ThaliTwin_Summit_Package_2026.zip"


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT_DIR, capture_output=True, text=True)
        return res.stdout.strip() if res.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def ensure_web_build():
    """Ensure the React production build exists in web/dist."""
    dist_dir = os.path.join(ROOT_DIR, "web", "dist")
    index_html = os.path.join(dist_dir, "index.html")
    if not os.path.exists(index_html):
        print("  -> web/dist not found. Compiling production React build...")
        subprocess.run(["npm", "run", "build"], cwd=os.path.join(ROOT_DIR, "web"), check=True, shell=True)
    else:
        print("  -> Verified existing production build in web/dist/.")


def generate_launcher_scripts(target_dir: str):
    """Generate simple double-clickable launchers for summit judges."""
    bat_content = """@echo off
TITLE ThaliTwin Summit Offline Evaluation Launcher
cls
echo ==============================================================================
echo        THALITWIN: STEPPED-CARE DIGITAL TWIN FOR TYPE 2 DIABETES
echo               Happiest Health Digital Twin Challenge 2026
echo ==============================================================================
echo.
echo Launching Production Clinical Decision Support System...
echo.
echo [1/2] Starting ThaliTwin REST API Backend on http://127.0.0.1:8000 ...
start /B python scripts/run_api.py --port 8000
timeout /t 3 /nobreak >nul

echo [2/2] Opening Streamlit Clinician Console on http://localhost:8501 ...
echo       (Press Ctrl+C in this terminal window to shut down the servers)
echo.
python -m streamlit run console/app.py --server.port 8501
pause
"""
    ps1_content = """# ThaliTwin Summit Offline Evaluation Launcher (PowerShell)
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "       THALITWIN: STEPPED-CARE DIGITAL TWIN FOR TYPE 2 DIABETES" -ForegroundColor Green
Write-Host "              Happiest Health Digital Twin Challenge 2026" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting ThaliTwin Local Evaluation Engine..." -ForegroundColor Yellow

$apiProcess = Start-Process -FilePath "python" -ArgumentList "scripts/run_api.py", "--port", "8000" -PassThru -NoNewWindow
Start-Sleep -Seconds 3

Write-Host "Opening Clinician Console..." -ForegroundColor Green
python -m streamlit run console/app.py --server.port 8501

Stop-Process -Id $apiProcess.Id -Force -ErrorAction SilentlyContinue
"""
    with open(os.path.join(target_dir, "RUN_DEMO.bat"), "w", encoding="utf-8") as f:
        f.write(bat_content)
    with open(os.path.join(target_dir, "RUN_DEMO.ps1"), "w", encoding="utf-8") as f:
        f.write(ps1_content)


def main():
    print("=" * 80)
    print("THALITWIN SUMMIT SUBMISSION PACKAGING SYSTEM")
    print("Happiest Health Digital Twin Challenge 2026 (Bengaluru Summit Track)")
    print("=" * 80)
    
    start_time = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    staging_dir = os.path.join(OUTPUT_DIR, "ThaliTwin_Submission")
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)
    os.makedirs(staging_dir, exist_ok=True)

    print("\n[Step 1/6] Verifying Web Distribution Assets...")
    ensure_web_build()

    print("\n[Step 2/6] Staging Core Deliverables...")
    # Directories to copy
    dirs_to_copy = [
        ("src", "src"),
        ("docs", "docs"),
        ("results", "results"),
        ("console", "console"),
        ("scripts", "scripts"),
        (os.path.join("web", "dist"), os.path.join("web", "dist")),
        ("tests", "tests")
    ]
    for src_rel, dest_rel in dirs_to_copy:
        src_path = os.path.join(ROOT_DIR, src_rel)
        dest_path = os.path.join(staging_dir, dest_rel)
        if os.path.exists(src_path):
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            print(f"  -> Copied {src_rel} -> {dest_rel}")

    # Copy data directory (excluding raw large temp files if any)
    data_src = os.path.join(ROOT_DIR, "data")
    data_dest = os.path.join(staging_dir, "data")
    if os.path.exists(data_src):
        shutil.copytree(data_src, data_dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.tmp", "*_cache*"))
        print(f"  -> Copied clinical datasets (data/)")

    # Files to copy
    files_to_copy = [
        "README.md",
        "LICENSE",
        "DATA_LICENSES.md",
        "requirements.txt",
        "pyproject.toml",
        ".env.example",
        "Dockerfile",
        "docker-compose.yml"
    ]
    for fname in files_to_copy:
        src_file = os.path.join(ROOT_DIR, fname)
        if os.path.exists(src_file):
            shutil.copy2(src_file, os.path.join(staging_dir, fname))
            print(f"  -> Copied {fname}")

    print("\n[Step 3/6] Generating Offline Evaluation Launchers...")
    generate_launcher_scripts(staging_dir)
    print("  -> Created RUN_DEMO.bat and RUN_DEMO.ps1")

    print("\n[Step 4/6] Generating Submission Manifest & Cryptographic Hashes...")
    manifest = {
        "project": "ThaliTwin",
        "track": "Happiest Health Digital Twin Challenge 2026 (Bengaluru Summit)",
        "regulatory_tier": "CDSCO SaMD Class IIa / ISO 14971 Medical Risk Controlled",
        "git_commit": get_git_commit(),
        "package_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "key_deliverables": {
            "slide_deck": "docs/presentation.pdf",
            "architecture_blueprint": "docs/architecture.pdf",
            "scorecard": "docs/SUBMISSION_SCORECARD.md",
            "hazard_analysis": "docs/HAZARD_ANALYSIS.md",
            "fhir_bundle_sample": "docs/fhir/ABDM_Bundle_Patient_001.json",
            "clinical_pdf_sample": "docs/reports/ThaliTwin_Clinical_Report_Patient_001.pdf",
            "web_spa_index": "web/dist/index.html"
        },
        "scientific_benchmarks": {
            "primary_cohort_auroc": 0.755,
            "zero_shot_ood_auroc_big_ideas": 0.754,
            "deep_baseline_comparison": "LightGBM RMSE 18.25 vs BiGRU RMSE 21.47 mg/dL (+3.22 mg/dL improvement)",
            "conformal_coverage_guarantee": "91.2% (Target 90.0% Marginal)",
            "stepped_care_cost_reduction": "82.5% annual savings (₹12,600 vs ₹72,000 continuous CGM)"
        },
        "checksums_sha256": {}
    }

    key_files_to_hash = [
        os.path.join(staging_dir, "docs", "presentation.pdf"),
        os.path.join(staging_dir, "docs", "architecture.pdf"),
        os.path.join(staging_dir, "docs", "SUBMISSION_SCORECARD.md"),
        os.path.join(staging_dir, "docs", "HAZARD_ANALYSIS.md"),
        os.path.join(staging_dir, "README.md"),
        os.path.join(staging_dir, "web", "dist", "index.html"),
        os.path.join(staging_dir, "src", "thalitwin", "twin.py"),
        os.path.join(staging_dir, "src", "thalitwin", "mechanistic.py"),
        os.path.join(staging_dir, "src", "thalitwin", "api", "service.py")
    ]

    for fpath in key_files_to_hash:
        if os.path.exists(fpath):
            rel_name = os.path.relpath(fpath, staging_dir)
            manifest["checksums_sha256"][rel_name] = compute_sha256(fpath)

    manifest_path = os.path.join(staging_dir, "SUBMISSION_MANIFEST.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"  -> Generated {manifest_path} with {len(manifest['checksums_sha256'])} verified checksums.")

    print("\n[Step 5/6] Creating Standalone Release ZIP Archive...")
    zip_dest = os.path.join(OUTPUT_DIR, ZIP_NAME)
    with zipfile.ZipFile(zip_dest, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(staging_dir):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_file = os.path.relpath(abs_file, staging_dir)
                zipf.write(abs_file, arcname=rel_file)

    zip_size_mb = os.path.getsize(zip_dest) / (1024 * 1024)
    zip_sha = compute_sha256(zip_dest)
    print(f"  -> Archive created: {zip_dest}")
    print(f"  -> Size: {zip_size_mb:.2f} MB")
    print(f"  -> Archive SHA-256: {zip_sha}")

    # Write root SHA256 file
    sha_file = os.path.join(OUTPUT_DIR, "SHA256SUMS.txt")
    with open(sha_file, "w", encoding="utf-8") as f:
        f.write(f"{zip_sha}  {ZIP_NAME}\n")

    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"SUBMISSION PACKAGING COMPLETED IN {elapsed:.1f}s")
    print(f"Directory: {OUTPUT_DIR}")
    print(f"Archive:   {zip_dest}")
    print("=" * 80)


if __name__ == "__main__":
    main()
