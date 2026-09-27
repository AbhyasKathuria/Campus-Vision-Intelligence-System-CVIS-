export type UserRole = 'student' | 'event_staff' | 'reviewer' | 'admin';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  created_at: string;
}

export interface Student {
  id: string;
  user_id: string;
  roll_number: string;
  enrollment_photo_ref?: string;
  consent_status: boolean;
  consent_date?: string;
  created_at: string;
  user?: User;
}

export interface Camera {
  id: string;
  name: string;
  location: string;
  zone: string;
  stream_url?: string;
  sampling_interval_seconds: number;
  active: boolean;
  created_at: string;
}

export type FlagStatus = 'pending' | 'confirmed' | 'rejected';
export type ViolationType = 'untucked_shirt' | 'casual_attire' | 'no_id_badge' | 'lab_coat_missing';
export type UnmatchedReasonType = 'none' | 'no_consent' | 'low_confidence' | 'no_face_detected' | 'not_in_database';
export type RejectionReasonType = 
  | 'false_positive_clothing'
  | 'lighting_contrast_artifact'
  | 'student_posture_angle'
  | 'incorrect_identity_match'
  | 'no_violation_found'
  | 'other';

export interface ComplianceFlag {
  id: string;
  recording_id?: string;
  camera_id?: string;
  camera_name?: string;
  camera_zone?: string;
  frame_timestamp_ms: number;
  frame_ref: string;
  face_crop_ref?: string;
  body_crop_ref?: string;
  matched_student_id?: string;
  matched_student_name?: string;
  matched_student_roll?: string;
  enrollment_photo_ref?: string;
  match_confidence?: number;
  unmatched_reason: UnmatchedReasonType;
  violation_type: ViolationType;
  violation_confidence: number;
  violation_details?: Record<string, any>;
  status: FlagStatus;
  reviewed_by?: string;
  reviewed_at?: string;
  rejection_reason?: RejectionReasonType;
  rejection_notes?: string;
  reviewer_notes?: string;
  is_retained_case: boolean;
  created_at: string;
}

export interface Notice {
  id: string;
  flag_id: string;
  student_id?: string;
  drafted_by: string;
  sent_by?: string;
  sent_at?: string;
  subject: string;
  content: string;
  created_at: string;
}

export interface Event {
  id: string;
  name: string;
  description?: string;
  date: string;
  created_by?: string;
  created_at: string;
  photo_count: number;
}

export interface EventPhoto {
  id: string;
  event_id: string;
  storage_ref: string;
  thumbnail_ref?: string;
  face_count: number;
  processed_at?: string;
  created_at: string;
}

export interface PhotoMatchItem {
  photo_id: string;
  event_id: string;
  storage_ref: string;
  thumbnail_ref: string;
  confidence_score: number;
  bounding_box?: { x: number; y: number; width: number; height: number };
}

export interface ViolationFPRMetric {
  violation_type: string;
  total_reviewed: number;
  rejected_count: number;
  confirmed_count: number;
  fpr_percentage?: number | null;
  status_label: string;
}

export interface CameraFPRMetric {
  camera_id: string;
  camera_name: string;
  zone: string;
  total_reviewed: number;
  rejected_count: number;
  fpr_percentage?: number | null;
  leading_rejection_reason?: string | null;
  environmental_calibration_recommended: boolean;
  status_label: string;
}

export interface TelemetryResponse {
  overall_fpr_percentage?: number | null;
  total_flags_reviewed: number;
  min_sample_size: number;
  status_label: string;
  by_violation: ViolationFPRMetric[];
  by_camera: CameraFPRMetric[];
  rejection_reason_distribution: Record<string, number>;
}

export interface AuditLog {
  id: string;
  actor_id?: string;
  actor_role?: UserRole;
  action: string;
  target_type: string;
  target_id: string;
  metadata_json?: Record<string, any>;
  timestamp: string;
}

export interface UnknownFaceCluster {
  id: string;
  event_id: string;
  cluster_label: string;
  representative_crop_ref?: string | null;
  face_count: number;
  member_embedding_ids: string[];
  created_at: string;
}
