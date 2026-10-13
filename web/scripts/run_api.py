"""
run_api.py (Wrapper for web/ directory)
Allows running the FastAPI service even when the shell's working directory is web/.
"""

import os
import sys

# Forward to root scripts/run_api.py
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

if __name__ == "__main__":
    import uvicorn
    from thalitwin.api.service import app
    
    port = 8000
    for idx, arg in enumerate(sys.argv):
        if arg == "--port" and idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])
            
    print("=" * 75)
    print("THALITWIN PRODUCTION CLINICAL DECISION SUPPORT API (FASTAPI)")
    print("=" * 75)
    print(f"Server URL:         http://127.0.0.1:{port}")
    print(f"Swagger API Docs:   http://127.0.0.1:{port}/docs")
    print(f"ReDoc Architecture: http://127.0.0.1:{port}/redoc")
    print(f"Health Probe:       http://127.0.0.1:{port}/health")
    print("=" * 75)
    
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
