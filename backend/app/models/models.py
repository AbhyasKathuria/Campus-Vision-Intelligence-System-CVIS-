import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, Integer, Float, BigInteger,
    ForeignKey, DateTime, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import (
    UserRole, EmbeddingSource, FlagStatus,
    ViolationType, UnmatchedReasonType, RejectionReasonType
)

def generate_uuid():
    return str(uuid.uuid4())

def get_utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.STUDENT)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    student_profile = relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="actor")

class Student(Base):
    __tablename__ = "students"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    roll_number = Column(String(64), unique=True, index=True, nullable=False)
    enrollment_photo_ref = Column(String(512), nullable=True)
    consent_status = Column(Boolean, default=False, nullable=False)
    consent_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    user = relationship("User", back_populates="student_profile")
    embeddings = relationship("FaceEmbedding", back_populates="student")
    flags = relationship("ComplianceFlag", back_populates="matched_student")

class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    source_type = Column(SQLEnum(EmbeddingSource), nullable=False)
    source_ref = Column(String(512), nullable=False) # e.g. photo path or frame path
    bounding_box = Column(JSON, nullable=True) # {"x": int, "y": int, "width": int, "height": int}
    vector_json = Column(JSON, nullable=False) # 512-dim float list
    model_version = Column(String(64), default="cvis-arcface-v1.0", nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    student = relationship("Student", back_populates="embeddings")

class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(String(32), nullable=False) # YYYY-MM-DD
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    photos = relationship("EventPhoto", back_populates="event", cascade="all, delete-orphan")

class EventPhoto(Base):
    __tablename__ = "event_photos"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    storage_ref = Column(String(512), nullable=False)
    thumbnail_ref = Column(String(512), nullable=True)
    face_count = Column(Integer, default=0)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    event = relationship("Event", back_populates="photos")

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    zone = Column(String(128), nullable=False)
    stream_url = Column(String(512), nullable=True)
    sampling_interval_seconds = Column(Float, default=2.0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    recordings = relationship("Recording", back_populates="camera", cascade="all, delete-orphan")
    flags = relationship("ComplianceFlag", back_populates="camera")

class Recording(Base):
    __tablename__ = "recordings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    camera_id = Column(String(36), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    storage_ref = Column(String(512), nullable=False)
    duration_seconds = Column(Integer, default=0)
    fps = Column(Float, default=30.0)
    sampling_interval_seconds = Column(Float, default=2.0)
    uploaded_at = Column(DateTime(timezone=True), default=get_utc_now)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    camera = relationship("Camera", back_populates="recordings")
    flags = relationship("ComplianceFlag", back_populates="recording", cascade="all, delete-orphan")

class ComplianceFlag(Base):
    __tablename__ = "compliance_flags"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    recording_id = Column(String(36), ForeignKey("recordings.id", ondelete="CASCADE"), nullable=True)
    camera_id = Column(String(36), ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)
    frame_timestamp_ms = Column(BigInteger, default=0)
    frame_ref = Column(String(512), nullable=False)
    face_crop_ref = Column(String(512), nullable=True)
    body_crop_ref = Column(String(512), nullable=True)
    
    # Matching details (strict privacy isolation)
    matched_student_id = Column(String(36), ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    match_confidence = Column(Float, nullable=True)
    unmatched_reason = Column(SQLEnum(UnmatchedReasonType), default=UnmatchedReasonType.NONE, nullable=False)

    # Violation details
    violation_type = Column(SQLEnum(ViolationType), nullable=False)
    violation_confidence = Column(Float, nullable=False)
    violation_details = Column(JSON, nullable=True) # features explanation

    # Human-in-the-loop review state
    status = Column(SQLEnum(FlagStatus), default=FlagStatus.PENDING, nullable=False)
    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(SQLEnum(RejectionReasonType), nullable=True)
    rejection_notes = Column(Text, nullable=True)
    reviewer_notes = Column(Text, nullable=True)

    # Auto-retention protection: retained cases are preserved during purge
    is_retained_case = Column(Boolean, default=False, nullable=False)
    model_version = Column(String(64), default="cvis-dresscode-v1.0", nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    recording = relationship("Recording", back_populates="flags")
    camera = relationship("Camera", back_populates="flags")
    matched_student = relationship("Student", back_populates="flags")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    notices = relationship("Notice", back_populates="flag", cascade="all, delete-orphan")

class Notice(Base):
    __tablename__ = "notices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    flag_id = Column(String(36), ForeignKey("compliance_flags.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=True)
    drafted_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    sent_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    subject = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    flag = relationship("ComplianceFlag", back_populates="notices")
    student = relationship("Student")
    drafter = relationship("User", foreign_keys=[drafted_by])
    sender = relationship("User", foreign_keys=[sent_by])

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_role = Column(SQLEnum(UserRole), nullable=True)
    action = Column(String(128), nullable=False) # e.g. 'REVIEW_CONFIRMED', 'NOTICE_SENT', 'CONSENT_GRANTED'
    target_type = Column(String(64), nullable=False)
    target_id = Column(String(64), nullable=False)
    metadata_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now)

    actor = relationship("User", back_populates="audit_logs")

class SystemConfig(Base):
    __tablename__ = "system_configs"

    key = Column(String(64), primary_key=True)
    value_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class TrainingExample(Base):
    """
    Active Learning Dataset (Item 7.1)
    Stores human-confirmed/rejected body crops with standardized labels for model retraining.
    PRIVACY SAFEGUARD: Stores clothing/body crop only, never unconsented student faces.
    """
    __tablename__ = "training_examples"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    flag_id = Column(String(36), ForeignKey("compliance_flags.id", ondelete="CASCADE"), nullable=False)
    body_crop_ref = Column(String(512), nullable=False)
    violation_type = Column(SQLEnum(ViolationType), nullable=False)
    is_violation = Column(Boolean, nullable=False) # True if confirmed, False if rejected
    rejection_reason = Column(SQLEnum(RejectionReasonType), nullable=True)
    features_json = Column(JSON, nullable=True)
    model_version = Column(String(64), default="cvis-dresscode-v1.0", nullable=False)
    labeled_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    flag = relationship("ComplianceFlag")
    reviewer = relationship("User", foreign_keys=[labeled_by])

class UnknownFaceCluster(Base):
    """
    Unknown-Face Clustering for Event Photo Finder (Item 7.2)
    Clusters unidentified faces across an event's photos for staff review.
    """
    __tablename__ = "unknown_face_clusters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    cluster_label = Column(String(128), nullable=False) # e.g. "Unidentified Person 1"
    representative_crop_ref = Column(String(512), nullable=True)
    face_count = Column(Integer, default=1)
    member_embedding_ids = Column(JSON, nullable=False) # list of FaceEmbedding IDs
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    event = relationship("Event")
