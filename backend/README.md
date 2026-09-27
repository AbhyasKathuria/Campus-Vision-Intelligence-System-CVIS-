# CVIS Backend Service

The CVIS Backend is a high-performance, asynchronous REST API gateway built with **Python 3.12** and **FastAPI**. It handles authentication, role-based access control (RBAC), database persistence, task orchestration, rate limiting, and immutable audit logging.

---

## Key Features

1. **Strict Human-in-the-Loop Disciplinary Workflow**:
   - Disciplinary notices cannot be sent autonomously.
   - Every compliance flag requires a human reviewer confirmation before a notice can be drafted.
   - Notice dispatching automatically marks underlying flags as `is_retained_case = true`, protecting them from the scheduled data purge.
2. **Pre-Search Biometric Consent Isolation**:
   - Students must grant consent before entering the camera recognition pipeline.
   - Unconsented students are excluded at the vector query level and explicitly logged with `unmatched_reason = "no_consent"` (with all student PII completely excluded from the flag record).
3. **Multi-Dimensional FPR Telemetry**:
   - Reviewer rejections are typed via `RejectionReasonType` enums and segmented by violation type and camera/zone.
   - Enforces a minimum sample size guard ($N \ge 10$) before recommending environmental calibration.
4. **Data Retention & Scheduled Purge**:
   - Background worker and admin manual trigger (`POST /api/v1/system/purge-expired`) purge unconfirmed flags and raw frames older than the retention window (default 30 days) while preserving active cases and audit logs.
5. **Rate Limiting & File Size Caps**:
   - Rate limiting on selfie searches (10/min) and auth endpoints.
   - Strict upload size caps (10MB selfie, 500MB bulk zip, 200MB video).

---

## Local Setup

### 1. Environment & Dependencies
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Database Initialization & Seeding
```bash
# Set PYTHONPATH to current directory
export PYTHONPATH=.   # or $env:PYTHONPATH="." in PowerShell

# Run synthetic seed data generator
python ../seed/seed_data.py
```

### 3. Run Development Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Running Automated Tests
```bash
python -m unittest discover tests
```
The test suite validates:
- `test_auth.py`: JWT generation, password hashing, and role checks.
- `test_compliance_consent.py`: Pre-search consent isolation and explicit unmatched auditing.
- `test_notice_guard.py`: Human-in-the-loop review confirmation enforcement and automatic retention tagging.
- `test_retention_purge.py`: Automatic erasure of expired records while preserving retained cases.
- `test_telemetry.py`: Camera-segmented FPR telemetry and small-sample-size guards.
- `test_photo_finder.py`: Photo ingestion, face indexing, and search rate limiting.
