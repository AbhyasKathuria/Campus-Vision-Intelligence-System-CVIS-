# CVIS ML Inference Microservice

The CVIS ML Service is a standalone microservice responsible for CPU-optimized computer vision inference:
- **Face Detection**: OpenCV YuNet / Haar multi-scale face and person detection.
- **Face Embeddings**: ArcFace / MobileFaceNet 512-dimensional unit-normalized vector extractor ($\|v\|_2 = 1.0$).
- **Vector Search Core**: FAISS `IndexFlatIP` with unit-normalized vectors for exact cosine similarity (with seamless NumPy fallback for zero-configuration native environments).
- **Compliance & Dress-Code Classifier**: Heuristic engine analyzing upper-body crops for waistband transitions (untucked shirt), collar/lapel presence (casual vs formal), chest quadrant contours (ID badge), and high-luminance coverage ratio (lab coat).

---

## API Endpoints

- `POST /api/v1/detect-faces`: Takes image, returns bounding boxes, landmark estimates, and confidence scores.
- `POST /api/v1/extract-embeddings`: Takes face crop, returns 512-dim unit vector.
- `POST /api/v1/classify-compliance`: Takes body crop, evaluates clothing heuristics, returns violation flags and feature breakdowns.
- `POST /api/v1/index-faces`: Adds vectors to collections (`event_photos` or `consented_students`).
- `POST /api/v1/vector-search`: Performs cosine similarity search with score thresholding.
- `POST /api/v1/clear-index/{collection}`: Clears index collection (used when consent is revoked).
- `GET /api/v1/health`: Service health and index vector counts.

---

## Local Setup & Tests

```bash
cd ml-service
pip install -r requirements.txt
python -m unittest discover tests
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```
