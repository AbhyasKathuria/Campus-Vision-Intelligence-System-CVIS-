import io
import unittest
import numpy as np
from PIL import Image
from app.core.detector import detector
from app.core.embedder import embedder
from app.core.classifier import classifier
from app.core.indexer import vector_manager

def create_synthetic_image(width=150, height=200, color=(120, 150, 180)):
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

class TestFaceCore(unittest.TestCase):
    def test_detector_basic(self):
        img_bytes = create_synthetic_image(200, 200)
        faces = detector.detect_faces(img_bytes)
        self.assertIsInstance(faces, list)
        self.assertTrue(len(faces) >= 0)

    def test_embedder_512_dim_and_normalization(self):
        img_bytes = create_synthetic_image(112, 112)
        vec = embedder.extract_embedding(img_bytes)
        self.assertEqual(len(vec), 512)
        norm = np.linalg.norm(vec)
        self.assertAlmostEqual(float(norm), 1.0, places=3)

    def test_vector_indexing_and_search(self):
        vector_manager.clear("test_collection")
        
        # Create two distinct unit vectors
        v1 = np.random.randn(512).astype(np.float32)
        v1 /= np.linalg.norm(v1)
        
        v2 = np.random.randn(512).astype(np.float32)
        v2 /= np.linalg.norm(v2)

        indexed = vector_manager.index_vectors("test_collection", [
            {"id": "doc1", "vector": v1.tolist(), "metadata": {"name": "Alice"}},
            {"id": "doc2", "vector": v2.tolist(), "metadata": {"name": "Bob"}}
        ])
        self.assertEqual(indexed, 2)

        # Query with v1 (similarity should be ~1.0)
        matches = vector_manager.search("test_collection", v1.tolist(), top_k=2, threshold=0.8)
        self.assertGreaterEqual(len(matches), 1)
        self.assertEqual(matches[0].id, "doc1")
        self.assertGreaterEqual(matches[0].score, 0.99)
        self.assertEqual(matches[0].metadata["name"], "Alice")

    def test_compliance_classifier_features(self):
        img_bytes = create_synthetic_image(200, 400)
        result = classifier.analyze_clothing(img_bytes)
        self.assertTrue(hasattr(result, "violation_detected"))
        self.assertTrue(hasattr(result, "violation_type"))
        self.assertTrue(hasattr(result, "violation_confidence"))
        self.assertIn("collar_detected", result.features)
        self.assertIn("waistband_edge_gradient", result.features)
        self.assertGreater(len(result.summary), 0)

if __name__ == "__main__":
    unittest.main()
