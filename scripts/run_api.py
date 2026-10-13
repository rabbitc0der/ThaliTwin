"""
run_api.py
Launcher script for the ThaliTwin Production FastAPI Clinical Service.

Usage:
    python scripts/run_api.py --port 8000
"""

import os
import sys
import argparse
import uvicorn

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

def main():
    parser = argparse.ArgumentParser(description="Run ThaliTwin Clinical FastAPI Service")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable hot reloading for development")
    args = parser.parse_args()
    
    print("=" * 75)
    print("THALITWIN PRODUCTION CLINICAL DECISION SUPPORT API (FASTAPI)")
    print("=" * 75)
    print(f"Server URL:         http://{args.host}:{args.port}")
    print(f"Swagger API Docs:   http://{args.host}:{args.port}/docs")
    print(f"ReDoc Architecture: http://{args.host}:{args.port}/redoc")
    print(f"Health Probe:       http://{args.host}:{args.port}/health")
    print("=" * 75)
    
    uvicorn.run(
        "thalitwin.api.service:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
