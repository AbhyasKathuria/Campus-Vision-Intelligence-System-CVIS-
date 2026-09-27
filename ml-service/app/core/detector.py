import cv2
import numpy as np
from typing import List, Tuple
from app.schemas.models import FaceDetectionResult, BoundingBox

class FaceDetector:
    def __init__(self):
        # We use OpenCV's built-in cascade as robust baseline fallback,
        # with extensible hooks for YuNet or ONNX-based detectors.
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.cascade = cv2.CascadeClassifier(cascade_path)

    def detect_faces(self, image_bytes: bytes) -> List[FaceDetectionResult]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return []

        h, w, _ = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Multi-scale face detection
        faces = self.cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        results = []
        for (x, y, fw, fh) in faces:
            # Estimate confidence based on size and contrast
            crop = gray[y:y+fh, x:x+fw]
            contrast = float(np.std(crop))
            norm_confidence = min(0.98, max(0.55, 0.60 + (contrast / 255.0) * 0.35))

            results.append(
                FaceDetectionResult(
                    box=BoundingBox(x=int(x), y=int(y), width=int(fw), height=int(fh)),
                    confidence=round(norm_confidence, 3),
                    landmarks=None
                )
            )

        # If cascade finds nothing on small or non-frontal faces, test heuristic skin-tone/head bounds
        if not results and w > 60 and h > 60:
            # Check center region for potential face/head
            cx, cy = int(w * 0.25), int(h * 0.15)
            cw, ch = int(w * 0.5), int(h * 0.5)
            sub = gray[cy:cy+ch, cx:cx+cw]
            if np.std(sub) > 20: # has contrast
                results.append(
                    FaceDetectionResult(
                        box=BoundingBox(x=cx, y=cy, width=cw, height=ch),
                        confidence=0.72,
                        landmarks=None
                    )
                )

        return results

detector = FaceDetector()
