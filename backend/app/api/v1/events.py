import io
import zipfile
from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from app.core.database import get_db
from app.core.storage import storage_manager
from app.core.config import settings
from app.core.audit import log_audit_event
from app.core.rate_limiter import enforce_rate_limit
from app.models.models import User, Event, EventPhoto, FaceEmbedding, UnknownFaceCluster
from app.models.enums import UserRole, EmbeddingSource
from app.schemas.schemas import EventCreate, EventResponse, EventPhotoResponse, UnknownFaceClusterResponse
from app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/events", tags=["Events & Photo Management"])

@router.get("", response_model=List[EventResponse])
async def list_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Event).options(selectinload(Event.photos)).order_by(Event.created_at.desc()))
    events = result.scalars().all()
    resp = []
    for ev in events:
        resp.append(EventResponse(
            id=ev.id,
            name=ev.name,
            description=ev.description,
            date=ev.date,
            created_by=ev.created_by,
            created_at=ev.created_at,
            photo_count=len(ev.photos)
        ))
    return resp

@router.post("", response_model=EventResponse)
async def create_event(
    req: EventCreate,
    current_user: User = Depends(require_roles([UserRole.EVENT_STAFF, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    event = Event(
        name=req.name,
        description=req.description,
        date=req.date,
        created_by=current_user.id
    )
    db.add(event)
    await db.flush()

    await log_audit_event(
        db, current_user, "EVENT_CREATED", "events", event.id, {"name": event.name}
    )
    await db.commit()
    await db.refresh(event)
    return EventResponse(
        id=event.id,
        name=event.name,
        description=event.description,
        date=event.date,
        created_by=event.created_by,
        created_at=event.created_at,
        photo_count=0
    )

@router.get("/{event_id}/photos", response_model=List[EventPhotoResponse])
async def list_event_photos(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(EventPhoto).where(EventPhoto.event_id == event_id).order_by(EventPhoto.created_at.desc())
    )
    return result.scalars().all()

@router.post("/{event_id}/upload")
async def upload_event_photos(
    event_id: str,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles([UserRole.EVENT_STAFF, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    enforce_rate_limit(request, "bulk_upload", max_requests=settings.RATE_LIMIT_BULK_UPLOAD, window_seconds=60)

    # Check event exists
    ev_res = await db.execute(select(Event).where(Event.id == event_id))
    event = ev_res.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty upload payload.")

    image_files: List[tuple[str, bytes]] = []

    # Check if zip file or individual image
    if file.filename and file.filename.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                for name in zf.namelist():
                    if name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) and not name.startswith("__MACOSX"):
                        img_data = zf.read(name)
                        image_files.append((name, img_data))
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid zip archive.")
    else:
        image_files.append((file.filename or "upload.jpg", content))

    processed_count = 0
    total_faces_indexed = 0

    async with httpx.AsyncClient(timeout=settings.ML_TIMEOUT_SECONDS) as client:
        for fname, img_bytes in image_files:
            try:
                # Save full image and thumbnail
                storage_ref = storage_manager.save_bytes(img_bytes, "event_photos", "jpg")
                thumb_ref = storage_manager.create_thumbnail(img_bytes)

                photo = EventPhoto(
                    event_id=event_id,
                    storage_ref=storage_ref,
                    thumbnail_ref=thumb_ref,
                    face_count=0
                )
                db.add(photo)
                await db.flush()

                # Call ML service for face detection
                det_resp = await client.post(
                    f"{settings.ML_SERVICE_URL}/api/v1/detect-faces",
                    files={"file": (fname, img_bytes, "image/jpeg")}
                )
                faces = []
                if det_resp.status_code == 200:
                    faces = det_resp.json().get("faces", [])

                photo.face_count = len(faces)
                photo.processed_at = datetime.now(timezone.utc)

                # For each detected face, extract embedding and index into vector collection
                vectors_to_index = []
                for face in faces:
                    box = face["box"]
                    crop_ref = storage_manager.create_crop(img_bytes, box, subfolder="crops")
                    crop_bytes = storage_manager.read_bytes(crop_ref)

                    if crop_bytes:
                        emb_resp = await client.post(
                            f"{settings.ML_SERVICE_URL}/api/v1/extract-embeddings",
                            files={"file": ("face_crop.jpg", crop_bytes, "image/jpeg")}
                        )
                        if emb_resp.status_code == 200:
                            emb_vec = emb_resp.json()["embedding"]
                            emb_record = FaceEmbedding(
                                source_type=EmbeddingSource.EVENT_PHOTO,
                                source_ref=photo.id,
                                bounding_box=box,
                                vector_json=emb_vec,
                                model_version="cvis-arcface-v1.0"
                            )
                            db.add(emb_record)
                            await db.flush()

                            vectors_to_index.append({
                                "id": f"{photo.id}_{emb_record.id}",
                                "vector": emb_vec,
                                "metadata": {
                                    "photo_id": photo.id,
                                    "event_id": event_id,
                                    "storage_ref": storage_ref,
                                    "thumbnail_ref": thumb_ref,
                                    "bounding_box": box
                                }
                            })

                if vectors_to_index:
                    await client.post(
                        f"{settings.ML_SERVICE_URL}/api/v1/index-faces",
                        json={
                            "collection": "event_photos",
                            "items": vectors_to_index
                        }
                    )
                    total_faces_indexed += len(vectors_to_index)

                processed_count += 1
            except Exception as e:
                # Log error and continue with remaining photos
                continue

    await log_audit_event(
        db, current_user, "EVENT_PHOTOS_UPLOADED", "events", event_id,
        {"photos_processed": processed_count, "faces_indexed": total_faces_indexed}
    )
    await db.commit()

    return {
        "event_id": event_id,
        "photos_processed": processed_count,
        "faces_indexed": total_faces_indexed,
        "message": f"Successfully ingested {processed_count} photo(s) with {total_faces_indexed} indexed face(s)."
    }

@router.post("/{event_id}/cluster-unknowns", response_model=List[UnknownFaceClusterResponse])
async def cluster_unknown_faces(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.EVENT_STAFF, UserRole.ADMIN]))
):
    ev_res = await db.execute(select(Event).where(Event.id == event_id))
    event = ev_res.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    # 1. Fetch all photos for this event
    photo_res = await db.execute(select(EventPhoto).where(EventPhoto.event_id == event_id))
    photos = photo_res.scalars().all()
    photo_ids = [p.id for p in photos]
    photo_map = {p.id: p for p in photos}

    if not photo_ids:
        return []

    # 2. Fetch all face embeddings belonging to these photos
    emb_res = await db.execute(
        select(FaceEmbedding).where(
            FaceEmbedding.source_type == EmbeddingSource.EVENT_PHOTO,
            FaceEmbedding.source_ref.in_(photo_ids)
        )
    )
    embeddings = emb_res.scalars().all()
    if not embeddings:
        return []

    # 3. Pairwise cosine clustering
    valid_embs = [e for e in embeddings if e.vector_json and len(e.vector_json) == 512]
    n = len(valid_embs)
    if n == 0:
        return []

    def cosine_similarity(v1, v2):
        return sum(a * b for a, b in zip(v1, v2))

    CLUSTERING_SIM_THRESHOLD = 0.58
    visited = set()
    clusters = []

    for i in range(n):
        if i in visited:
            continue
        current_cluster = [valid_embs[i]]
        visited.add(i)
        v_i = valid_embs[i].vector_json

        for j in range(i + 1, n):
            if j not in visited:
                v_j = valid_embs[j].vector_json
                sim = cosine_similarity(v_i, v_j)
                if sim >= CLUSTERING_SIM_THRESHOLD:
                    current_cluster.append(valid_embs[j])
                    visited.add(j)

        clusters.append(current_cluster)

    clusters.sort(key=lambda c: len(c), reverse=True)

    # 4. Remove previous clusters for this event
    old_clusters = await db.execute(select(UnknownFaceCluster).where(UnknownFaceCluster.event_id == event_id))
    for c in old_clusters.scalars().all():
        await db.delete(c)
    await db.flush()

    # 5. Persist clusters in database
    created_clusters = []
    for idx, cluster in enumerate(clusters):
        lead_emb = cluster[0]
        lead_photo = photo_map.get(lead_emb.source_ref)
        
        rep_crop_ref = None
        if lead_photo and lead_emb.bounding_box:
            photo_bytes = storage_manager.read_bytes(lead_photo.storage_ref)
            if photo_bytes:
                rep_crop_ref = storage_manager.create_crop(photo_bytes, lead_emb.bounding_box, "crops")
        if not rep_crop_ref and lead_photo:
            rep_crop_ref = lead_photo.thumbnail_ref or lead_photo.storage_ref

        cluster_record = UnknownFaceCluster(
            event_id=event_id,
            cluster_label=f"Unidentified Person #{idx + 1}",
            representative_crop_ref=rep_crop_ref,
            face_count=len(cluster),
            member_embedding_ids=[e.id for e in cluster]
        )
        db.add(cluster_record)
        created_clusters.append(cluster_record)

    await log_audit_event(
        db, current_user, "UNKNOWN_FACES_CLUSTERED", "events", event_id,
        {"clusters_found": len(created_clusters), "total_faces": n}
    )
    await db.commit()

    for c in created_clusters:
        await db.refresh(c)

    return created_clusters

@router.get("/{event_id}/clusters", response_model=List[UnknownFaceClusterResponse])
async def list_unknown_clusters(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.EVENT_STAFF, UserRole.ADMIN]))
):
    result = await db.execute(
        select(UnknownFaceCluster).where(UnknownFaceCluster.event_id == event_id).order_by(UnknownFaceCluster.face_count.desc())
    )
    return result.scalars().all()
