# CVIS — Ethical AI, Biometric Privacy & Legal Compliance Guide

## 1. Principles of Campus Vision Intelligence

CVIS is engineered according to the **Privacy by Design** framework. It establishes a strict operational boundary between self-service utility and compliance review.

---

## 2. Core Privacy Tenets

### 2.1 The Human-in-the-Loop Disciplinary Firewall
Under no circumstances may an automated AI prediction trigger a student reprimand, disciplinary penalty, or formal record.
- **AI as Decision Support**: Computer vision models act solely as triage filters, populating an internal staff review queue.
- **Draft-and-Send Requirement**: Notices are never dispatched by system triggers. A human reviewer must explicitly inspect the evidence, confirm the finding, and authorize dispatch.

### 2.2 Pre-Search Biometric Consent Isolation
- **Voluntary Enrollment**: Students decide whether campus cameras may attempt to identify them for compliance reviews.
- **Pre-Search Guarantee**: Students who have not consented are not matched and then filtered out; rather, **their face embeddings never enter the active search index (`consented_students`)**.
- **Auditability of Unmatched Individuals**: When an unconsented student is present in a flagged frame, the system records `unmatched_reason = "no_consent"` and sets `matched_student_id = NULL`. No student PII is written to the flag.

### 2.3 Ephemeral Self-Service Search
- In the Event Photo Finder, uploaded search selfies are held solely in RAM during feature extraction and similarity ranking.
- Selfies are discarded immediately after the HTTP response is completed. They are never written to disk, stored in databases, or added to training pools.

---

## 3. Data Retention Lifecycle & Right to Erasure

### 3.1 Automated Purge Schedule
Campus CCTV footage contains non-relevant individuals. To prevent surveillance creep:
1. **Raw Video Footage**: Purged automatically after 30 days (configurable up to 90 days).
2. **Unconfirmed Flags**: Purged automatically after 30 days.
3. **Face & Body Crops**: Pruned from storage upon flag deletion.
4. **Retained Cases**: Flags tied to an active notice or disciplinary proceeding (`is_retained_case = true`) are exempt from automatic erasure until the matter is resolved.

### 3.2 Right to Erasure (GDPR / State Biometric Laws)
When a student requests deletion or revokes consent:
- `compliance_flags.matched_student_id` is foreign-keyed with `ON DELETE SET NULL`. If a student record is removed, past historical flags remain intact for statistical audits without retaining student identity.
- Vector embeddings in `face_embeddings` are immediately wiped.
- The student's face is cleared from FAISS in-memory indices.

---

## 4. Immutable Audit Logging

Every critical read and write operation is recorded in the `audit_logs` table:
- User logins and role assignments.
- Biometric consent grants and revocations.
- Student history views (audited to prevent unauthorized staff snooping).
- Reviewer confirmations, rejections, and dismissals.
- Notice drafting and sending.
- Data retention purge executions.

Audit logs cannot be modified or truncated via standard user or reviewer interfaces.
