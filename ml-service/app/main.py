import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

from app.schemas.models import (
    DetectFacesResponse,
    ExtractEmbeddingResponse,
    ComplianceViolationResult,
    VectorSearchRequest,
    VectorSearchResponse,
    IndexVectorsRequest,
    IndexVectorsResponse
)
from app.core.detector import detector
from app.core.embedder import embedder
from app.core.classifier import classifier
from app.core.indexer import vector_manager

app = FastAPI(
    title="CVIS ML Inference Microservice",
    description="Face Detection, ArcFace Embedding, Dress-Code Heuristics & FAISS Search",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "cvis-ml-service",
        "indices": {
            "event_photos": vector_manager.get_count("event_photos"),
            "consented_students": vector_manager.get_count("consented_students")
        }
    }

@app.post("/api/v1/detect-faces", response_model=DetectFacesResponse)
async def detect_faces(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty image file received.")
    faces = detector.detect_faces(content)
    return DetectFacesResponse(face_count=len(faces), faces=faces)

@app.post("/api/v1/extract-embeddings", response_model=ExtractEmbeddingResponse)
async def extract_embeddings(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty image file received.")
    vec = embedder.extract_embedding(content)
    return ExtractEmbeddingResponse(embedding=vec, dimension=len(vec))

@app.post("/api/v1/classify-compliance", response_model=ComplianceViolationResult)
async def classify_compliance(
    file: UploadFile = File(...),
    target_check: Optional[str] = Form(None)
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty image file received.")
    result = classifier.analyze_clothing(content, target_check=target_check)
    return result

@app.post("/api/v1/index-faces", response_model=IndexVectorsResponse)
async def index_faces(request: IndexVectorsRequest):
    count = vector_manager.index_vectors(request.collection, request.items)
    return IndexVectorsResponse(indexed_count=count, collection=request.collection)

@app.post("/api/v1/vector-search", response_model=VectorSearchResponse)
async def vector_search(request: VectorSearchRequest):
    matches = vector_manager.search(
        collection=request.collection,
        query_vector=request.vector,
        top_k=request.top_k,
        threshold=request.threshold
    )
    total = vector_manager.get_count(request.collection)
    return VectorSearchResponse(matches=matches, total_searched=total)

@app.post("/api/v1/clear-index/{collection}")
async def clear_index(collection: str):
    vector_manager.clear(collection)
    return {"message": f"Index {collection} cleared successfully."}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
