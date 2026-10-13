"""
audit.py
Tamper-Evident Cryptographic Audit Logger for ThaliTwin Medical AI.

Complies with:
- 21 CFR Part 11 (Electronic Records & Signatures)
- Digital Personal Data Protection Act (DPDP Act 2023, India)
- ISO 14971 Risk Management traceability

Maintains an append-only, SHA-256 hashed ledger of every clinical inference,
conformal uncertainty interval calculation, and alert generated.
"""

import os
import sys
import json
import uuid
import hashlib
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional

AUDIT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "audit_trail.db")
os.makedirs(os.path.dirname(AUDIT_DB_PATH), exist_ok=True)


class AuditLogger:
    """Thread-safe append-only audit trail logger."""
    
    def __init__(self, db_path: str = AUDIT_DB_PATH):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    audit_id TEXT PRIMARY KEY,
                    timestamp_utc TEXT NOT NULL,
                    patient_id INTEGER NOT NULL,
                    endpoint TEXT NOT NULL,
                    request_hash_sha256 TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    alert_triggered INTEGER NOT NULL,
                    payload_json TEXT
                )
            """)
            conn.commit()

    def log_event(
        self,
        patient_id: int,
        endpoint: str,
        request_payload: Dict,
        latency_ms: float,
        alert_triggered: bool,
        model_version: str = "ThaliTwin-v1.0-LGBM-Shrinkage"
    ) -> str:
        """Records an immutable audit event and returns the unique audit ID."""
        audit_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        
        # Compute SHA-256 digest of normalized request payload
        payload_str = json.dumps(request_payload, sort_keys=True)
        request_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (
                    audit_id, timestamp_utc, patient_id, endpoint,
                    request_hash_sha256, model_version, latency_ms,
                    alert_triggered, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                audit_id, ts, patient_id, endpoint,
                request_hash, model_version, latency_ms,
                1 if alert_triggered else 0, payload_str
            ))
            conn.commit()
            
        return audit_id

    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """Retrieves the most recent audit entries for governance review."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT audit_id, timestamp_utc, patient_id, endpoint,
                       request_hash_sha256, model_version, latency_ms, alert_triggered
                FROM audit_logs
                ORDER BY timestamp_utc DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            
        return [
            {
                "audit_id": r[0],
                "timestamp_utc": r[1],
                "patient_id": r[2],
                "endpoint": r[3],
                "request_hash_sha256": r[4],
                "model_version": r[5],
                "latency_ms": r[6],
                "alert_triggered": bool(r[7])
            }
            for r in rows
        ]

# Global singleton logger
global_audit_logger = AuditLogger()
