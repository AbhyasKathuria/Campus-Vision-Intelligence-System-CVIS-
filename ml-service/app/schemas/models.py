from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x: int = Field(..., description="Top left X coordinate")
    y: int = Field(..., description="Top left Y coordinate")
    width: int = Field(..., description="Box width")
    height: int = Field(..., description="Box height")

class FaceDetectionResult(BaseModel):
    box: BoundingBox
    confidence: float
    landmarks: Optional[List[List[float]]] = None

class DetectFacesResponse(BaseModel):
    face_count: int
    faces: List[FaceDetectionResult]

class ExtractEmbeddingResponse(BaseModel):
    embedding: List[float] = Field(..., description="512-dim unit-normalized vector")
    dimension: int = 512

class VectorSearchItem(BaseModel):
    id: str
    score: float
    metadata: Optional[Dict[str, Any]] = None

class VectorSearchRequest(BaseModel):
    collection: str = Field(..., description="'event_photos' or 'consented_students'")
    vector: List[float] = Field(..., description="512-dim query embedding")
    top_k: int = 10
    threshold: float = 0.55

class VectorSearchResponse(BaseModel):
    matches: List[VectorSearchItem]
    total_searched: int

class IndexVectorsRequest(BaseModel):
    collection: str
    items: List[Dict[str, Any]]  # [{"id": str, "vector": List[float], "metadata": dict}]

class IndexVectorsResponse(BaseModel):
    indexed_count: int
    collection: str

class ComplianceViolationResult(BaseModel):
    violation_detected: bool
    violation_type: str = Field(..., description="untucked_shirt, casual_attire, no_id_badge, lab_coat_missing")
    violation_confidence: float
    features: Dict[str, Any] = Field(default_factory=dict)
    summary: str
