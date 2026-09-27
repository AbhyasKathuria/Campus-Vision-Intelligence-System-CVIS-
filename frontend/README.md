# CVIS Frontend Application

A modern **React 18 + Vite + Tailwind CSS** application featuring two distinct visual experiences:

---

## 1. Staff Command Console ("Ops Center" Theme)
- Designed for security and discipline operations centers.
- Dark theme (`#0B0F17` base, `#131A26` panels, `#3DA9FC` live cyan accent).
- Live CCTV camera grid with real-time detection bounding overlays (green for compliant person, amber for uniform flag).
- Side-by-side biometric comparison queue (captured CCTV crop vs enrolled student photo).
- AI explainability metrics and typed rejection modal.
- Multi-dimensional FPR telemetry dashboard with camera segmentation and sample size guards.
- Event photo album manager with bulk zip upload and face indexing progress.
- Searchable immutable audit trail and retention management.

---

## 2. Student Self-Service App (Light, Task-First Theme)
- Designed for students searching event photos and managing privacy.
- Clean, warm light neutral background (`#FAFAF8`) with deep teal accent (`#0D9488`).
- Selfie search with ephemeral in-memory processing (selfies are never stored permanently).
- Responsive matched photo gallery with high-res download.
- Biometric consent manager with armed/disarmed toggle and plain-language privacy explanations.
- Verified personal compliance history viewer.

---

## Development

```bash
cd frontend
npm install
npm run dev
```

Build for production:
```bash
npm run build
```
