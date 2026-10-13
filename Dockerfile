# ==============================================================================
# ThaliTwin Enterprise Container Image
# Happiest Health Digital Twin Challenge 2026
# SaMD Class IIa Clinical Decision Support System
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    LOKY_MAX_CPU_COUNT=4

WORKDIR /app

# Install system dependencies (OpenMP for LightGBM, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU first to avoid heavy CUDA wheels
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install python packages
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code, models, and data
COPY src /app/src
COPY data /app/data
COPY results /app/results
COPY console /app/console
COPY scripts /app/scripts
COPY tests /app/tests
COPY pyproject.toml /app/pyproject.toml

# Expose API port 8000 and Streamlit Doctor Console port 8501
EXPOSE 8000 8501

# Healthcheck targeting FastAPI probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default: Run the FastAPI production clinical API
CMD ["python", "scripts/run_api.py", "--host", "0.0.0.0", "--port", "8000"]
