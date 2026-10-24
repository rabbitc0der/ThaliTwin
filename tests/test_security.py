"""
test_security.py
Automated security & pre-deploy checks for ThaliTwin CDSCO SaMD Proposed Class B API.
Validates OWASP security headers, sliding-window rate limiting, ID bounds, and secret guards.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from thalitwin.api.service import app, SlidingWindowRateLimiter


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_owasp_security_headers(client):
    """
    Check 03: Pre-Deploy Production Audit.
    Validates that essential OWASP security headers are injected on API responses.
    """
    res = client.get("/health")
    headers = res.headers

    assert headers.get("X-Content-Type-Options") == "nosniff", "Missing X-Content-Type-Options nosniff"
    assert headers.get("X-Frame-Options") == "DENY", "Missing X-Frame-Options DENY"
    assert "Strict-Transport-Security" in headers, "Missing Strict-Transport-Security header"
    assert headers.get("X-XSS-Protection") == "1; mode=block", "Missing X-XSS-Protection header"
    assert "strict-origin" in headers.get("Referrer-Policy", ""), "Missing secure Referrer-Policy"
    assert headers.get("X-ThaliTwin-SaMD-Class") == "Class-IIa-CDSS"


def test_sliding_window_rate_limiter_unit():
    """
    Check 03 & 05: Validates sliding window rate limiter logic.
    """
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
    ip = "192.168.1.100"

    assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is True
    # 4th request must be rejected
    assert limiter.is_allowed(ip) is False


def test_rate_limiter_http_429(client):
    """
    Check 03 & 05: Verifies that API returns HTTP 429 when rate limit is exceeded.
    """
    from thalitwin.api import service
    # Temporarily set max_requests to 2 for testing
    original_max = service.rate_limiter.max_requests
    service.rate_limiter.max_requests = 2
    service.rate_limiter.requests.clear()

    try:
        r1 = client.get("/api/v1/patients/1")
        r2 = client.get("/api/v1/patients/1")
        r3 = client.get("/api/v1/patients/1")

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r3.status_code == 429
        assert "Rate limit exceeded" in r3.json()["detail"]
        assert r3.headers.get("Retry-After") == "60"
    finally:
        # Restore original rate limit
        service.rate_limiter.max_requests = original_max
        service.rate_limiter.requests.clear()


def test_idor_and_patient_id_bounds(client):
    """
    Check 04 & 05: Validates that invalid or out-of-bounds patient IDs (IDOR attack path)
    are strictly rejected with clean 404 or 422 errors and no stack traces.
    """
    # Non-existent ID above cohort size (45)
    res_high = client.get("/api/v1/patients/99")
    assert res_high.status_code == 404
    assert "not found" in res_high.json()["detail"].lower()

    # Negative or zero ID (violates Path(..., ge=1))
    res_zero = client.get("/api/v1/patients/0")
    assert res_zero.status_code == 422  # Unprocessable Entity (Pydantic validation failure)


def test_env_file_gitignored():
    """
    Check 01: Secret Leak Prevention.
    Verifies that .env and secret patterns are explicitly listed in .gitignore.
    """
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    gitignore_path = os.path.join(root_dir, ".gitignore")

    assert os.path.exists(gitignore_path), ".gitignore must exist"
    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert ".env" in content
    assert "*.env" in content or ".env.*" in content
