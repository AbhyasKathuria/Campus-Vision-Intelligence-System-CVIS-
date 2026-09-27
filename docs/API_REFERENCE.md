# CVIS REST API Reference Specification

Base URL: `http://localhost:8000/api/v1`  
Interactive Swagger Docs: `http://localhost:8000/docs`

All protected endpoints require the HTTP Authorization header:
```
Authorization: Bearer <jwt_access_token>
```

---

## 1. Authentication & Users

### `POST /auth/register`
Creates a new university user profile. If role is `student`, creates an associated student record.
- **Access**: Public
- **Request Body**:
  ```json
  {
    "name": "Jane Doe",
    "email": "jane@campus.edu",
    "role": "student",
    "password": "Password123!",
    "roll_number": "STU-2024-042"
  }
  ```
- **Response**: `200 OK` (`UserResponse`)

### `POST /auth/login`
Authenticates user, verifies bcrypt hash, and issues a 24-hour JWT token.
- **Rate Limit**: 5 attempts per minute per IP.
- **Request Body**:
  ```json
  {
    "email": "reviewer@campus.edu",
    "password": "Password123!"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": "uuid",
      "name": "Warden Arthur Pendelton",
      "email": "reviewer@campus.edu",
      "role": "reviewer"
    }
  }
  ```

### `GET /auth/me`
Returns the currently authenticated user profile.
- **Access**: Authenticated

---

## 2. Biometric Consent Management

### `GET /consent/status`
Returns the student's current biometric consent status.
- **Access**: Student

### `POST /consent/update`
Grants or revokes biometric consent for campus compliance camera matching.
- **Access**: Student
- **Request Body**:
  ```json
  {
    "consent_status": true
  }
  ```
- **Effect**: If true, synchronizes face embedding into `consented_students` vector index. If false, completely purges embedding from the compliance index and records an immutable audit log entry.

### `POST /consent/enrollment-photo`
Uploads official student ID photo, extracts 512-dim face embedding, and links to profile.
- **Access**: Student
- **Payload**: `multipart/form-data` with `file: Binary`

---

## 3. Subsystem A — Event Photo Finder

### `GET /events`
Lists all campus events with album photo counts.
- **Access**: Authenticated

### `POST /events`
Creates a new campus event album.
- **Access**: Event Staff, Admin
- **Request Body**:
  ```json
  {
    "name": "Annual Convocation 2026",
    "date": "2026-10-15",
    "description": "Graduation ceremony gallery"
  }
  ```

### `POST /events/{event_id}/upload`
Bulk ingests event photos from individual images or a `.zip` archive.
- **Access**: Event Staff, Admin
- **Upload Cap**: 500 MB max.
- **Payload**: `multipart/form-data` with `file: Binary`
- **Effect**: Unpacks archive, detects all faces in each photo, extracts 512-dim ArcFace embeddings, indexes vectors into `event_photos` FAISS collection, and generates web thumbnails.

### `POST /search/selfie`
Student self-service photo finder. Searches campus event dumps for matching photos of the student.
- **Access**: Authenticated Student / Staff
- **Rate Limit**: 10 requests per minute.
- **Upload Cap**: 10 MB max.
- **Privacy Assurance**: Selfie is processed entirely in-memory and discarded immediately after vector query.
- **Payload**: `multipart/form-data` with `file: Binary`, optional `threshold: float` (default: 0.65)
- **Response**: `200 OK`
  ```json
  {
    "total_matches": 3,
    "matches": [
      {
        "photo_id": "uuid",
        "event_id": "uuid",
        "storage_ref": "event_photos/photo1.jpg",
        "thumbnail_ref": "thumbnails/photo1.jpg",
        "confidence_score": 0.892,
        "bounding_box": { "x": 120, "y": 60, "width": 90, "height": 90 }
      }
    ]
  }
  ```

---

## 4. Subsystem B — Compliance & Ingestion

### `GET /cameras`
Lists all registered camera sensors, zones, stream protocols, and sampling cadences.
- **Access**: Authenticated

### `POST /cameras`
Registers a new CCTV camera.
- **Access**: Admin, Reviewer
- **Request Body**:
  ```json
  {
    "name": "Science Block Lab 3",
    "location": "Science Wing Floor 2",
    "zone": "Science Block",
    "stream_url": "rtsp://camera.campus.internal:554/feed",
    "sampling_interval_seconds": 2.0,
    "active": true
  }
  ```

### `POST /compliance/process-recording/{recording_id}`
Triggers background cadence-based frame extraction, person & face detection, dress-code heuristics, and pre-search consent face matching.
- **Access**: Admin, Reviewer

### `GET /compliance/flags`
Queries compliance review queue with filters.
- **Access**: Admin, Reviewer
- **Query Params**:
  - `status_filter`: `pending` | `confirmed` | `rejected`
  - `camera_id`: UUID
  - `violation_type`: `untucked_shirt` | `casual_attire` | `no_id_badge` | `lab_coat_missing`

### `GET /compliance/student-history`
Allows students to view their own verified, confirmed compliance advisories. Unconfirmed or dismissed flags are never exposed.
- **Access**: Student

---

## 5. Reviewer Actions & Notice Guard

### `POST /reviews/flags/{flag_id}/confirm`
Reviewer confirms both identity and violation.
- **Access**: Reviewer, Admin
- **Request Body**:
  ```json
  {
    "notes": "Confirmed student identity and untucked shirt.",
    "confirmed_student_id": "optional-override-uuid"
  }
  ```

### `POST /reviews/flags/{flag_id}/reject`
Reviewer rejects the detection, standardizing FPR telemetry.
- **Access**: Reviewer, Admin
- **Request Body**:
  ```json
  {
    "rejection_reason": "lighting_contrast_artifact",
    "rejection_notes": "Morning sun reflection created false waistband edge."
  }
  ```

### `POST /reviews/flags/{flag_id}/dismiss`
Dismisses a flag without action (`rejection_reason = no_violation_found`).
- **Access**: Reviewer, Admin

### `POST /notices/draft`
Drafts a compliance advisory for a confirmed flag.
- **Access**: Reviewer, Admin
- **Guard**: Fails with 400 if underlying flag is not in `CONFIRMED` status.

### `POST /notices/{notice_id}/send`
Reviewer approves and dispatches the notice.
- **Access**: Reviewer, Admin
- **Automatic Retention**: Automatically marks the underlying flag as `is_retained_case = true`.

---

## 6. Telemetry & Retention Purge

### `GET /compliance/telemetry`
Returns multi-dimensional FPR telemetry segmented by violation type and camera/zone, including leading rejection reasons and statistical significance guards.
- **Access**: Reviewer, Admin

### `GET /system/config` & `PUT /system/config`
Retrieves or updates operational parameters (similarity threshold, retention window, sampling cadence, minimum sample size).
- **Access**: Admin

### `POST /system/purge-expired`
Executes data retention purge. Wipes unconfirmed flags, video recordings, and frame crops older than configured days, while preserving active retained cases and audit logs.
- **Access**: Admin

### `GET /audit`
Queries immutable system audit trail.
- **Access**: Admin, Reviewer
