from enum import Enum

class UserRole(str, Enum):
    STUDENT = "student"
    EVENT_STAFF = "event_staff"
    REVIEWER = "reviewer"
    ADMIN = "admin"

class EmbeddingSource(str, Enum):
    SELFIE = "selfie"
    ENROLLMENT = "enrollment"
    EVENT_PHOTO = "event_photo"
    FRAME = "frame"

class FlagStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"

class ViolationType(str, Enum):
    UNTUCKED_SHIRT = "untucked_shirt"
    CASUAL_ATTIRE = "casual_attire"
    NO_ID_BADGE = "no_id_badge"
    LAB_COAT_MISSING = "lab_coat_missing"

class UnmatchedReasonType(str, Enum):
    NONE = "none"
    NO_CONSENT = "no_consent"
    LOW_CONFIDENCE = "low_confidence"
    NO_FACE_DETECTED = "no_face_detected"
    NOT_IN_DATABASE = "not_in_database"

class RejectionReasonType(str, Enum):
    FALSE_POSITIVE_CLOTHING = "false_positive_clothing"
    LIGHTING_CONTRAST_ARTIFACT = "lighting_contrast_artifact"
    STUDENT_POSTURE_ANGLE = "student_posture_angle"
    INCORRECT_IDENTITY_MATCH = "incorrect_identity_match"
    NO_VIOLATION_FOUND = "no_violation_found"
    OTHER = "other"
