import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, Dict

from app.core.database import get_db
from app.core.config import settings
from app.core.rate_limiter import enforce_rate_limit
from app.models.models import User, EventPhoto
from app.schemas.schemas import PhotoSearchResponse, PhotoMatchItem
from app.api.deps import get_current_user

router = APIRouter(prefix="/search", tags=["Photo Search"])

@router.post("/selfie", response_model=PhotoSearchResponse)
async def search_photos_by_selfie(
    request: Request,
    file: UploadFile = File(...),
    threshold: Optional[float] = Form(None),
    top_k: Optional[int] = Form(20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Enforce strict rate limit: 10 searches per minute per user/IP
    enforce_rate_limit(
        request, f"selfie_search_{current_user.id}",
        max_requests=settings.RATE_LIMIT_SELFIE_SEARCH,
        window_seconds=60
    )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty selfie upload.")

    # Size cap check
    max_bytes = settings.MAX_UPLOAD_SELFIE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Selfie image exceeds maximum allowed size of {settings.MAX_UPLOAD_SELFIE_MB}MB."
        )

    search_threshold = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD

    # Ephemeral processing: extract embedding directly in memory, do NOT persist selfie to disk
    async with httpx.AsyncClient(timeout=settings.ML_TIMEOUT_SECONDS) as client:
        # Step 1: Extract embedding
        emb_resp = await client.post(
            f"{settings.ML_SERVICE_URL}/api/v1/extract-embeddings",
            files={"file": ("selfie.jpg", content, "image/jpeg")}
        )
        if emb_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="ML inference service failed to process selfie.")

        query_vector = emb_resp.json()["embedding"]

        # Step 2: Search event_photos vector collection
        search_resp = await client.post(
            f"{settings.ML_SERVICE_URL}/api/v1/vector-search",
            json={
                "collection": "event_photos",
                "vector": query_vector,
                "top_k": top_k or 20,
                "threshold": search_threshold
            }
        )
        if search_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Vector search service failed.")

        matches_raw = search_resp.json().get("matches", [])

    # Group by photo_id so a single photo with multiple match hits is only returned once with highest score
    photo_best_score: Dict[str, dict] = {}
    for m in matches_raw:
        meta = m.get("metadata", {})
        photo_id = meta.get("photo_id")
        score = m.get("score", 0.0)
        if photo_id:
            if photo_id not in photo_best_score or score > photo_best_score[photo_id]["score"]:
                photo_best_score[photo_id] = {
                    "score": score,
                    "event_id": meta.get("event_id", ""),
                    "storage_ref": meta.get("storage_ref", ""),
                    "thumbnail_ref": meta.get("thumbnail_ref", ""),
                    "bounding_box": meta.get("bounding_box")
                }

    # Fetch database photo details
    results = []
    if photo_best_score:
        photo_ids = list(photo_best_score.keys())
        db_res = await db.execute(select(EventPhoto).where(EventPhoto.id.in_(photo_ids)))
        db_photos = {p.id: p for p in db_res.scalars().all()}

        for pid, data in sorted(photo_best_score.items(), key=lambda x: x[1]["score"], reverse=True):
            if pid in db_photos:
                p = db_photos[pid]
                results.append(
                    PhotoMatchItem(
                        photo_id=p.id,
                        event_id=p.event_id,
                        storage_ref=p.storage_ref,
                        thumbnail_ref=p.thumbnail_ref or p.storage_ref,
                        confidence_score=round(data["score"], 4),
                        bounding_box=data["bounding_box"]
                    )
                )

    return PhotoSearchResponse(
        total_matches=len(results),
        matches=results
    )
