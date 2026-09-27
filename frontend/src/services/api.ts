import { 
  User, Student, Camera, ComplianceFlag, Notice, Event, 
  EventPhoto, PhotoMatchItem, TelemetryResponse, AuditLog,
  FlagStatus, ViolationType, RejectionReasonType, UnknownFaceCluster 
} from '../types';

const API_BASE = '/api/v1';

class ApiService {
  private getHeaders(isFormData = false): HeadersInit {
    const token = localStorage.getItem('cvis_token');
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    return headers;
  }

  // --- Auth ---
  async login(email: string, password: string):Promise<{ access_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    localStorage.setItem('cvis_token', data.access_token);
    localStorage.setItem('cvis_user', JSON.stringify(data.user));
    return data;
  }

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch profile');
    return res.json();
  }

  logout() {
    localStorage.removeItem('cvis_token');
    localStorage.removeItem('cvis_user');
  }

  // --- Student Self-Service ---
  async searchSelfie(file: File, threshold?: number): Promise<{ total_matches: number; matches: PhotoMatchItem[] }> {
    const formData = new FormData();
    formData.append('file', file);
    if (threshold !== undefined) {
      formData.append('threshold', threshold.toString());
    }

    const res = await fetch(`${API_BASE}/search/selfie`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Search failed' }));
      throw new Error(err.detail || 'Search failed');
    }
    return res.json();
  }

  async getConsentStatus(): Promise<Student> {
    const res = await fetch(`${API_BASE}/consent/status`, {
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to get consent status');
    return res.json();
  }

  async updateConsent(consent_status: boolean): Promise<Student> {
    const res = await fetch(`${API_BASE}/consent/update`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ consent_status })
    });
    if (!res.ok) throw new Error('Failed to update consent');
    return res.json();
  }

  async uploadEnrollmentPhoto(file: File): Promise<Student> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/consent/enrollment-photo`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: formData
    });
    if (!res.ok) throw new Error('Failed to upload enrollment photo');
    return res.json();
  }

  async getStudentHistory(): Promise<ComplianceFlag[]> {
    const res = await fetch(`${API_BASE}/compliance/student-history`, {
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch history');
    return res.json();
  }

  // --- Ops Center & Cameras ---
  async listCameras(): Promise<Camera[]> {
    const res = await fetch(`${API_BASE}/cameras`, {
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to list cameras');
    return res.json();
  }

  async createCamera(camera: Partial<Camera>): Promise<Camera> {
    const res = await fetch(`${API_BASE}/cameras`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(camera)
    });
    if (!res.ok) throw new Error('Failed to create camera');
    return res.json();
  }

  async listFlags(params?: { status?: FlagStatus; camera_id?: string; violation_type?: ViolationType }): Promise<ComplianceFlag[]> {
    const query = new URLSearchParams();
    if (params?.status) query.append('status_filter', params.status);
    if (params?.camera_id) query.append('camera_id', params.camera_id);
    if (params?.violation_type) query.append('violation_type', params.violation_type);

    const res = await fetch(`${API_BASE}/compliance/flags?${query.toString()}`, {
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch flags');
    return res.json();
  }

  async confirmFlag(flagId: string, notes?: string, confirmedStudentId?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/reviews/flags/${flagId}/confirm`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ notes, confirmed_student_id: confirmedStudentId })
    });
    if (!res.ok) throw new Error('Failed to confirm flag');
    return res.json();
  }

  async rejectFlag(flagId: string, reason: RejectionReasonType, notes?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/reviews/flags/${flagId}/reject`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ rejection_reason: reason, rejection_notes: notes })
    });
    if (!res.ok) throw new Error('Failed to reject flag');
    return res.json();
  }

  async dismissFlag(flagId: string, notes?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/reviews/flags/${flagId}/dismiss`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ notes })
    });
    if (!res.ok) throw new Error('Failed to dismiss flag');
    return res.json();
  }

  // --- Notices ---
  async draftNotice(flagId: string, subject: string, content: string): Promise<Notice> {
    const res = await fetch(`${API_BASE}/notices/draft`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ flag_id: flagId, subject, content })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to draft notice' }));
      throw new Error(err.detail || 'Failed to draft notice');
    }
    return res.json();
  }

  async sendNotice(noticeId: string): Promise<Notice> {
    const res = await fetch(`${API_BASE}/notices/${noticeId}/send`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ approved: true })
    });
    if (!res.ok) throw new Error('Failed to send notice');
    return res.json();
  }

  async recallNotice(noticeId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/notices/${noticeId}/recall`, {
      method: 'POST',
      headers: this.getHeaders()
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to recall notice' }));
      throw new Error(err.detail || 'Failed to recall notice');
    }
    return res.json();
  }

  async exportCommitteeReport(format: 'csv' | 'html'): Promise<Blob | string> {
    const res = await fetch(`${API_BASE}/compliance/export-report?format=${format}`, {
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to export committee report');
    if (format === 'html') {
      return res.text();
    }
    return res.blob();
  }

  async getNoticeForFlag(flagId: string): Promise<Notice | null> {
    const res = await fetch(`${API_BASE}/notices/flag/${flagId}`, {
      headers: this.getHeaders()
    });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error('Failed to fetch notice');
    return res.json();
  }

  // --- Telemetry & Analytics ---
  async getTelemetry(): Promise<TelemetryResponse> {
    const res = await fetch(`${API_BASE}/compliance/telemetry`, {
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch telemetry');
    return res.json();
  }

  // --- Events & Bulk Upload ---
  async listEvents(): Promise<Event[]> {
    const res = await fetch(`${API_BASE}/events`, {
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to list events');
    return res.json();
  }

  async createEvent(event: { name: string; description?: string; date: string }): Promise<Event> {
    const res = await fetch(`${API_BASE}/events`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(event)
    });
    if (!res.ok) throw new Error('Failed to create event');
    return res.json();
  }

  async uploadEventPhotos(eventId: string, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/events/${eventId}/upload`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: formData
    });
    if (!res.ok) throw new Error('Failed to upload photos');
    return res.json();
  }

  async listEventPhotos(eventId: string): Promise<EventPhoto[]> {
    const res = await fetch(`${API_BASE}/events/${eventId}/photos`, {
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to list photos');
    return res.json();
  }

  async clusterUnknownFaces(eventId: string): Promise<UnknownFaceCluster[]> {
    const res = await fetch(`${API_BASE}/events/${eventId}/cluster-unknowns`, {
      method: 'POST',
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to cluster unidentified faces');
    return res.json();
  }

  async listUnknownClusters(eventId: string): Promise<UnknownFaceCluster[]> {
    const res = await fetch(`${API_BASE}/events/${eventId}/clusters`, {
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to list unknown clusters');
    return res.json();
  }

  // --- System Settings & Retention Purge ---
  async getSystemConfig(): Promise<Record<string, any>> {
    const res = await fetch(`${API_BASE}/system/config`, {
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to get system configs');
    return res.json();
  }

  async updateSystemConfig(configs: Record<string, any>): Promise<any> {
    const res = await fetch(`${API_BASE}/system/config`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify({ configs })
    });
    if (!res.ok) throw new Error('Failed to update config');
    return res.json();
  }

  async purgeExpiredRecords(): Promise<any> {
    const res = await fetch(`${API_BASE}/system/purge-expired`, {
      method: 'POST',
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to trigger retention purge');
    return res.json();
  }

  async listAuditLogs(): Promise<AuditLog[]> {
    const res = await fetch(`${API_BASE}/audit`, {
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch audit logs');
    return res.json();
  }
}

export const api = new ApiService();
