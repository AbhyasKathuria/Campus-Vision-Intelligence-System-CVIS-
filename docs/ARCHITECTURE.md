# CVIS — System Architecture & Design Specification

## 1. Executive Architecture Summary

The **Campus Vision Intelligence System (CVIS)** is an enterprise university computer-vision platform composed of two decoupled functional subsystems powered by a shared, CPU-optimized face recognition and vector search core:

```
                               ┌─────────────────────────────────────────┐
                               │           Shared Biometric Core         │
                               │  - Face Detection (YuNet / Multi-scale) │
                               │  - 512-dim Embeddings (ArcFace / L2)    │
                               │  - Vector Indexing (FAISS / Cosine IP)  │
                               └────────────────────┬────────────────────┘
                                                    │
                 ┌──────────────────────────────────┴──────────────────────────────────┐
                 ▼                                                                     ▼
┌─────────────────────────────────┐                                 ┌─────────────────────────────────────┐
│  Subsystem A: Event Photo Finder│                                 │ Subsystem B: Compliance Review      │
│  - Self-Service Student Search  │                                 │ - Cadence CCTV Frame Ingestion      │
│  - Multi-Face Album Ingestion   │                                 │ - Dress-Code Heuristic Classifier   │
│  - Ephemeral Memory Processing  │                                 │ - Pre-Search Consent Isolation      │
│  - Strict Rate Limiting         │                                 │ - Strict Human-in-the-Loop Queue    │
│  - No Student Data Retention    │                                 │ - Draft-and-Send Disciplinary Guard │
└─────────────────────────────────┘                                 └─────────────────────────────────────┘
```

---

## 2. Microservice Boundaries

```mermaid
flowchart TB
    subgraph Client ["Client Layer"]
        OpsUI["Staff Command Console (Dark Theme: #0B0F17)"]
        StudentUI["Student Self-Service App (Light Theme: #FAFAF8)"]
    end

    subgraph Gateway ["Backend API Gateway (FastAPI :8000)"]
        AuthModule["Auth & RBAC (JWT / Bcrypt)"]
        EventModule["Event & Photo Ingestion Engine"]
        SearchModule["Ephemeral Selfie Search Engine"]
        ComplianceModule["Compliance & Frame Cadence Ingester"]
        ReviewModule["Reviewer Queue & Notice Guard"]
        TelemetryModule["Segmented FPR Telemetry Engine"]
        RetentionModule["Retention & Purge Service"]
    end

    subgraph MLMicroservice ["ML Inference Service (FastAPI :8001)"]
        Detector["Face & Person Detector"]
        Embedder["ArcFace 512-dim Normalized Embedder"]
        Classifier["Dress-Code Heuristic Engine"]
        FAISS_Events["FAISS Index: event_photos"]
        FAISS_Students["FAISS Index: consented_students"]
    end

    subgraph Persistence ["Data & Storage Layer"]
        Postgres[(PostgreSQL / SQLite Database)]
        RedisCache[(Redis Cache & Task Broker)]
        MediaStorage[(Local Storage / S3 Bucket)]
    end

    Client -->|HTTPS REST| Gateway
    Gateway --> Postgres
    Gateway --> RedisCache
    Gateway --> MediaStorage
    Gateway -->|Internal HTTP| MLMicroservice
```

---

## 3. Pre-Search Consent Isolation Architecture

A core privacy guarantee of CVIS is that unconsented individuals are not merely filtered out *after* vector matching; rather, **unconsented faces never enter the search comparison at all**.

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant Backend as Backend Gateway
    participant ML as ML Service (FAISS)
    participant CCTV as CCTV Ingestion

    Note over Student,Backend: Step 1: Opt-in Consent Workflow
    Student->>Backend: POST /api/v1/consent/update { consent_status: true }
    Backend->>ML: POST /api/v1/index-faces (collection: consented_students)
    ML-->>Backend: Vector indexed in active memory
    Backend-->>Student: Biometric Consent Active

    Note over Student,Backend: Step 2: Opt-out Revocation Workflow
    Student->>Backend: POST /api/v1/consent/update { consent_status: false }
    Backend->>ML: POST /api/v1/clear-index/consented_students (rebuild minus student)
    Backend-->>Student: Consent Revoked (Embeddings Purged)

    Note over CCTV,Backend: Step 3: Compliance Ingestion Query
    CCTV->>Backend: Extracted Frame with Flagged Violation
    Backend->>ML: POST /api/v1/vector-search (collection: consented_students)
    Note over ML: Only consented faces exist in this index
    alt Match Found (Score >= 0.65)
        ML-->>Backend: Match: Student ID
        Backend->>Backend: Create Flag (matched_student_id = ID, unmatched_reason = none)
    else Unconsented or Low Confidence
        ML-->>Backend: No Match
        Backend->>Backend: Create Flag (matched_student_id = NULL, unmatched_reason = no_consent | low_confidence)
    end
```

---

## 4. Human-in-the-Loop Disciplinary Guard

Under no circumstances does CVIS dispatch automated disciplinary notices.

1. **State 1: AI Detection**: Frame violation detected $\rightarrow$ Flag created with `status = PENDING`.
2. **State 2: Reviewer Inspection**: Staff inspects side-by-side face comparison and heuristic breakdown.
3. **State 3: Human Verdict**:
   - If confirmed $\rightarrow$ `status = CONFIRMED`, `reviewed_by = reviewer_id`.
   - If rejected $\rightarrow$ `status = REJECTED`, `rejection_reason = typed_enum` (feeds telemetry).
4. **State 4: Draft & Send**:
   - Reviewer drafts a formal advisory.
   - Reviewer explicitly clicks "Approve & Dispatch Notice".
   - System automatically sets `is_retained_case = true`, protecting the record from scheduled purges.

---

## 5. Multi-Dimensional FPR Telemetry

Reviewer rejections feed an analytical engine that isolates model accuracy from hardware/environmental faults:

$$\text{FPR}_{\text{global}} = \frac{\sum \text{Rejected Flags}}{\sum \text{Reviewed Flags}} \times 100$$

$$\text{FPR}_{c, v} = \frac{\text{Rejected Flags for Camera } c, \text{ Violation } v}{\text{Total Reviewed Flags for Camera } c, \text{ Violation } v} \times 100$$

### Statistical Significance Threshold ($N \ge 10$)
If a camera exhibits an $\text{FPR} \ge 35\%$ with `lighting_contrast_artifact` as the leading rejection reason, the Ops Console highlights the sensor with an **"Environmental Calibration Recommended"** tag, provided $N \ge 10$. This guarantees small-sample outliers (e.g. 1 rejection out of 2 reviews) do not trigger false alerts.
