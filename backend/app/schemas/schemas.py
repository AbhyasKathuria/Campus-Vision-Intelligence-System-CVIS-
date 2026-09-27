from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.models.enums import (
    UserRole, EmbeddingSource, FlagStatus,
    ViolationType, UnmatchedReasonType, RejectionReasonType
)

# --- User & Auth Schemas ---
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole = UserRole.STUDENT

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    roll_number: Optional[str] = None # required if role is student

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Student Schemas ---
class StudentResponse(BaseModel):
    id: str
    user_id: str
    roll_number: str
    enrollment_photo_ref: Optional[str] = None
    consent_status: bool
    consent_date: Optional[datetime] = None
    created_at: datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True

class ConsentUpdateRequest(BaseModel):
    consent_status: bool

# --- Event & Photo Schemas ---
class EventBase(BaseModel):
    name: str
    description: Optional[str] = None
    date: str

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: str
    created_by: Optional[str] = None
    created_at: datetime
    photo_count: Optional[int] = 0

    class Config:
        from_attributes = True

class EventPhotoResponse(BaseModel):
    id: str
    event_id: str
    storage_ref: str
    thumbnail_ref: Optional[str] = None
    face_count: int
    processed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PhotoMatchItem(BaseModel):
    photo_id: str
    event_id: str
    storage_ref: str
    thumbnail_ref: Optional[str] = None
    confidence_score: float
    bounding_box: Optional[Dict[str, int]] = None

class PhotoSearchResponse(BaseModel):
    total_matches: int
    matches: List[PhotoMatchItem]

class UnknownFaceClusterResponse(BaseModel):
    id: str
    event_id: str
    cluster_label: str
    representative_crop_ref: Optional[str] = None
    face_count: int
    member_embedding_ids: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

# --- Camera & Recording Schemas ---
class CameraCreate(BaseModel):
    name: str
    location: str
    zone: str
    stream_url: Optional[str] = None
    sampling_interval_seconds: float = 2.0
    active: bool = True

class CameraResponse(CameraCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class RecordingResponse(BaseModel):
    id: str
    camera_id: str
    storage_ref: str
    duration_seconds: int
    fps: float
    sampling_interval_seconds: float
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Compliance Flag & Review Schemas ---
class ComplianceFlagResponse(BaseModel):
    id: str
    recording_id: Optional[str] = None
    camera_id: Optional[str] = None
    camera_name: Optional[str] = None
    camera_zone: Optional[str] = None
    frame_timestamp_ms: int
    frame_ref: str
    face_crop_ref: Optional[str] = None
    body_crop_ref: Optional[str] = None
    matched_student_id: Optional[str] = None
    matched_student_name: Optional[str] = None
    matched_student_roll: Optional[str] = None
    enrollment_photo_ref: Optional[str] = None
    match_confidence: Optional[float] = None
    unmatched_reason: UnmatchedReasonType
    violation_type: ViolationType
    violation_confidence: float
    violation_details: Optional[Dict[str, Any]] = None
    status: FlagStatus
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[RejectionReasonType] = None
    rejection_notes: Optional[str] = None
    reviewer_notes: Optional[str] = None
    is_retained_case: bool
    created_at: datetime

    class Config:
        from_attributes = True

class FlagConfirmRequest(BaseModel):
    notes: Optional[str] = None
    confirmed_student_id: Optional[str] = None # can override/verify student match

class FlagRejectRequest(BaseModel):
    rejection_reason: RejectionReasonType
    rejection_notes: Optional[str] = None

class FlagDismissRequest(BaseModel):
    notes: Optional[str] = None

# --- Notice Schemas ---
class NoticeDraftRequest(BaseModel):
    flag_id: str
    subject: str
    content: str

class NoticeResponse(BaseModel):
    id: str
    flag_id: str
    student_id: Optional[str] = None
    drafted_by: str
    sent_by: Optional[str] = None
    sent_at: Optional[datetime] = None
    subject: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class NoticeApproveRequest(BaseModel):
    approved: bool = True

# --- Telemetry & Analytics Schemas ---
class ViolationFPRMetric(BaseModel):
    violation_type: str
    total_reviewed: int
    rejected_count: int
    confirmed_count: int
    fpr_percentage: Optional[float] = None
    status_label: str = "insufficient_data"

class CameraFPRMetric(BaseModel):
    camera_id: str
    camera_name: str
    zone: str
    total_reviewed: int
    rejected_count: int
    fpr_percentage: Optional[float] = None
    leading_rejection_reason: Optional[str] = None
    environmental_calibration_recommended: bool
    status_label: str = "insufficient_data"

class TelemetryResponse(BaseModel):
    overall_fpr_percentage: Optional[float] = None
    total_flags_reviewed: int
    min_sample_size: int
    status_label: str = "insufficient_data"
    by_violation: List[ViolationFPRMetric]
    by_camera: List[CameraFPRMetric]
    rejection_reason_distribution: Dict[str, int]

# --- Audit & System Schemas ---
class AuditLogResponse(BaseModel):
    id: str
    actor_id: Optional[str] = None
    actor_role: Optional[UserRole] = None
    action: str
    target_type: str
    target_id: str
    metadata_json: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class SystemConfigUpdate(BaseModel):
    configs: Dict[str, Any]

class PurgeResponse(BaseModel):
    purged_flags_count: int
    purged_recordings_count: int
    purged_files_count: int
    retention_cutoff: datetime
