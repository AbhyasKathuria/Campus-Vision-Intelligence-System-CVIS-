# CVIS (Campus Vision Intelligence System) — Build Walkthrough

We have built and verified the complete full-stack **Campus Vision Intelligence System (CVIS)**, including all core modules (Phases 1–6), Round 2 Addendum Part A enhancements, and the Phase 7 Enterprise Differentiators.

CVIS provides two independent subsystems atop a shared face detection, ArcFace embedding, and vector search core:
1. **Event Photo Finder (Self-Service)**: Fast, self-service photo discovery with ephemeral selfie search (in-memory processing, zero permanent query face retention), rate limits, and multi-face indexation.
2. **Compliance Monitoring (Staff Review Queue)**: Multi-camera CCTV ingestion sampled at a configurable cadence (default: 0.5 FPS), dress-code heuristics, and strict **Human-in-the-Loop review**.

---

## 1. Key Architectural & Policy Guardrails Implemented

### 🛡️ Strict Human-in-the-Loop Disciplinary Workflow
- **No autonomous warnings or notices**: Reviewers must manually inspect and confirm both identity and violation before any notice can be drafted.
- **Atomic Disciplinary Case Retention**: Approving/dispatching a notice automatically marks the underlying flag as `is_retained_case = true` in the exact same transaction, protecting it from data purges.
- **60-Second Undo Window**: Staff can recall and cancel a dispatched notice within a 60-second safety window directly from the Review Queue header.

### 🔒 Pre-Search Biometric Consent Isolation (Partitioned Index)
- Students must explicitly grant consent before their face is searchable in the compliance pipeline.
- Students without consent are **completely excluded at the vector search index level** (`consented_students` collection).
- Unconsented detections are tagged with `unmatched_reason = "no_consent"` and `matched_student_id = NULL`, with all student PII completely excluded from the flag record.

### 📊 Multi-Dimensional FPR Telemetry with Statistical Significance Guard ($N \ge 15$)
- Typed rejections (`rejection_reason_type`: `false_positive_clothing`, `lighting_contrast_artifact`, etc.) segment FPR across heuristic types and cameras.
- **Sample Size Guard ($N \ge 15$)**: Sensor and violation pairs with $N < 15$ reviewed decisions display `status_label = "insufficient_data"` and `fpr_percentage = None`, preventing false calibration alerts.

### 🗑️ Data Retention & Scheduled Purge Worker
- Purges unconfirmed flags, video recordings, and frame crops older than the retention threshold (default 30 days), while strictly preserving active disciplinary cases (`is_retained_case = true`) and immutable audit logs.

---

## 2. Phase 7 Enterprise Differentiators Implemented

| Feature | Implementation | Description |
| :--- | :--- | :--- |
| **7.1 Active Learning Feedback Loop** | `backend/app/api/v1/reviews.py`, `scripts/export_training_set.py` | Reviewer decisions populate `training_examples`. Body crops are strictly isolated (no unconsented student faces). Run `python scripts/export_training_set.py` to extract labeled training sets with image manifests. |
| **7.2 Unidentified Face Clustering** | `backend/app/api/v1/events.py`, `frontend/src/pages/ops/EventPhotoManager.tsx` | Pairwise cosine topology clustering groups non-enrolled attendees across event photos into "Unidentified Person #X" clusters in Ops Console. |
| **7.3 Model & Dataset Version Tagging** | `models.py`, `compliance.py`, `consent.py`, `events.py` | All embeddings, flags, and training samples carry explicit `model_version` tags (e.g. `cvis-arcface-v1.0`, `cvis-dresscode-v1.0`). |
| **7.4 Reviewer Workflow Polish** | `frontend/src/pages/ops/ReviewQueue.tsx` | Full keyboard shortcuts (`[C]` Confirm, `[R]` Reject, `[D]` Dismiss, `[↑/↓]` Navigate, `[N]` Notice) and a 60-second undo dispatch countdown banner. |
| **7.5 Discipline Committee Export** | `backend/app/api/v1/compliance.py` | Dedicated endpoint and UI buttons to export confirmed cases as structured CSV spreadsheets or formal, printable HTML dossiers (`/api/v1/compliance/export-report`). |
| **7.6 CI Automation** | `.github/workflows/ci.yml` | GitHub Actions workflow executing backend unit tests, ML service core tests, and production Vite frontend compilation. |
| **7.7 Plain-Language Transparency & Governance** | `docs/data-protection-overview.md`, `docs/student-transparency.md` | Dual documentation covering institutional legal compliance (GDPR/FERPA) and plain-language student rights. |

---

## 3. Automated Test Suite Results

### Backend Core, Privacy & Differentiator Tests (`backend/tests/`)
```text
Ran 15 tests in 5.692s
OK
- test_auth.py: Verified bcrypt hashing, JWT token lifecycle, invalid token rejection
- test_compliance_consent.py: Verified unconsented student is excluded with unmatched_reason = no_consent
- test_notice_guard.py: Verified notices cannot be drafted/sent without prior reviewer confirmation
- test_retention_purge.py: Verified expired unconfirmed flags are purged while retained cases and sent notice flags are preserved
- test_telemetry.py: Verified camera-segmented FPR telemetry and small-sample-size guard (N < 15)
- test_photo_finder.py: Verified multi-face event photo indexing and search rate limiter triggers
- test_phase7_differentiators.py: Verified active learning body crop isolation, unknown face clustering, and 60s notice recall
```

### ML Inference Microservice (`ml-service/tests/test_face_core.py`)
```text
Ran 4 tests in 0.553s
OK
- test_detector_basic: Multi-scale face and contrast detection
- test_embedder_512_dim_and_normalization: 512-dim unit vector normalization (||v||2 == 1.0)
- test_vector_indexing_and_search: FAISS/NumPy exact cosine similarity ranking
- test_compliance_classifier_features: Explainability features (waistband, collar, badge)
```

### Frontend Production Build (`frontend`)
```text
✓ 1501 modules transformed.
dist/index.html                   0.83 kB │ gzip:  0.48 kB
dist/assets/index-C13GlcoR.css   29.32 kB │ gzip:  6.02 kB
dist/assets/index-BSF-v6Jh.js   286.79 kB │ gzip: 77.60 kB
✓ built in 12.79s
```

---

## 4. Documentation Suite

1. [System Architecture & Visual Diagrams](file:///c:/Users/kathu/Desktop/projects/Campus%20Vision%20Intelligence%20System%20%28CVIS%29/docs/ARCHITECTURE.md)
2. [REST API Reference & Endpoints](file:///c:/Users/kathu/Desktop/projects/Campus%20Vision%20Intelligence%20System%20%28CVIS%29/docs/API_REFERENCE.md)
3. [Compliance, Privacy & Retention Guide](file:///c:/Users/kathu/Desktop/projects/Campus%20Vision%20Intelligence%20System%20%28CVIS%29/docs/COMPLIANCE_AND_PRIVACY_GUIDE.md)
4. [Deployment & Production Runbook](file:///c:/Users/kathu/Desktop/projects/Campus%20Vision%20Intelligence%20System%20%28CVIS%29/docs/DEPLOYMENT_GUIDE.md)
5. [Active Learning & Continuous Calibration Guide](file:///c:/Users/kathu/Desktop/projects/Campus%20Vision%20Intelligence%20System%20%28CVIS%29/docs/ACTIVE_LEARNING_GUIDE.md)
6. [Data Protection & Governance Overview (Legal/Admin)](file:///c:/Users/kathu/Desktop/projects/Campus%20Vision%20Intelligence%20System%20%28CVIS%29/docs/data-protection-overview.md)
7. [Student Privacy & Transparency Guide (Plain Language)](file:///c:/Users/kathu/Desktop/projects/Campus%20Vision%20Intelligence%20System%20%28CVIS%29/docs/student-transparency.md)

---

## 5. One-Click Quick Start Launchers

- `start.bat`: Starts Backend (8000), ML Service (8001), and Frontend (5173 / 3000) in separate persistent terminals.
- `stop.bat`: Gracefully stops all local CVIS processes.
- `start-docker.bat`: Launches containerized CVIS stack via Docker Compose.
