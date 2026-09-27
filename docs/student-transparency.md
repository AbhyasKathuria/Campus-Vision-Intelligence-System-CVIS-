# Student Privacy & Transparency Guide
## How CVIS Protects Your Identity and Visual Data

*Plain-Language Transparency Document for Students & University Community.*

---

## 1. What is CVIS?

The **Campus Vision Intelligence System (CVIS)** provides two services on campus:
1. **Event Photo Finder**: A service that lets you find all photos of yourself across university events (like sports day, graduation, cultural fests) by uploading a single selfie.
2. **Compliance Monitoring**: An internal assistant for university staff to maintain campus dress code and ID-badge standards.

We believe that computer vision must never come at the expense of your personal freedom, dignity, or privacy. This document explains your rights, our technology, and how your data is handled.

---

## 2. Your Five Inviolable Rights

### 1. You Have Full Control Over Your Biometrics (Opt-In Only)
- Enrolling your face into CVIS compliance monitoring is **100% voluntary**.
- If you do not give explicit consent, **your face is never indexed in the compliance database**.
- You can grant or revoke consent at any time directly from the Student Portal.

### 2. No Autonomous AI Penalties Ever
- **An algorithm can never punish you, issue a fine, or send a disciplinary notice.**
- The system merely highlights possible dress-code discrepancies to trained university staff.
- A human reviewer must examine the footage side-by-side, verify whether a policy was actually violated, write any notice by hand, and receive formal supervisory approval before any message reaches you.

### 3. Your Event Selfies Are Ephemeral (Deleted Immediately)
- When you upload a selfie to find photos from campus events:
  - Your selfie is used **only** for the few seconds required to search that specific event's photo album.
  - As soon as the search completes, your selfie is **permanently deleted** from our servers.
  - Your selfie is **never** added to the compliance database, CCTV systems, or any permanent profile.

### 4. Right to Erasure / Immediate Forget
- If you revoke your consent in the portal, your facial recognition embedding is immediately purged from active search indexes.
- You can also request complete deletion of any stored enrollment portraits.

### 5. Strict 30-Day Data Expiry
- Footage and unconfirmed flags automatically expire and are purged after 30 days.
- Nothing is retained indefinitely unless an official inquiry was formally documented and dispatched to you.

---

## 3. What Happens If I Opt-Out (Do Not Consent)?

| Scenario | What Happens |
| :--- | :--- |
| **You walk past a campus camera** | The camera samples periodic frames. If an attire issue is detected, the system attempts to check against *consented* students only. |
| **Identity matching** | Because your face was never added to the index, **no identity match occurs**. The record states `unmatched_reason: no_consent`. |
| **Student profile link** | **Your name, student ID, and roll number are never linked** to the record. |
| **Event Photo Finder** | You can still freely use Event Photo Finder using temporary selfies whenever you attend campus festivals! |

---

## 4. How Does Face Recognition Actually Work?

1. **Detection**: OpenCV AI locates the bounding box around a face.
2. **Feature Extraction**: The deep neural network calculates an anonymous mathematical vector (a list of 512 numbers representing proportions like distance between pupils and cheekbones).
3. **Similarity Comparison**: The math compares two vectors. **Your actual photo is not stored in the AI search engine — only numbers.**

---

## 5. Frequently Asked Questions (FAQ)

### Can staff browse CCTV feeds live through CVIS?
No. CVIS is not a live surveillance monitoring feed. It operates on periodic sampled clips solely for standardized compliance reporting and human auditing.

### Who can view my compliance notices?
Only authorized University Reviewers, the Discipline Committee, and you. Your notices are never shared with peers or public portals.

### How do I revoke my consent?
1. Log into the CVIS Student Portal (`http://localhost:5173`).
2. Go to **Consent & Privacy**.
3. Toggle the **Biometric Consent** switch to OFF.
4. Your vector is immediately removed from the active compliance index.

---

*For further inquiries regarding privacy policies, contact the Campus Data Protection Officer at: `dpo@campus.edu`.*
