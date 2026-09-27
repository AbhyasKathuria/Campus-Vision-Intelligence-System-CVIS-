from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.storage import storage_manager
from app.core.config import settings
from app.core.audit import log_audit_event
from app.models.models import User, Camera, Recording
from app.models.enums import UserRole
from app.schemas.schemas import CameraCreate, CameraResponse, RecordingResponse
from app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/cameras", tags=["Cameras & Streams"])

@router.get("", response_model=List[CameraResponse])
async def list_cameras(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Camera).order_by(Camera.created_at.asc()))
    return result.scalars().all()

@router.post("", response_model=CameraResponse)
async def create_camera(
    req: CameraCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.REVIEWER])),
    db: AsyncSession = Depends(get_db)
):
    camera = Camera(
        name=req.name,
        location=req.location,
        zone=req.zone,
        stream_url=req.stream_url,
        sampling_interval_seconds=req.sampling_interval_seconds,
        active=req.active
    )
    db.add(camera)
    await db.flush()

    await log_audit_event(
        db, current_user, "CAMERA_CREATED", "cameras", camera.id,
        {"name": camera.name, "zone": camera.zone}
    )
    await db.commit()
    await db.refresh(camera)
    return camera

@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: str,
    req: CameraCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.REVIEWER])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalars().first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found.")

    camera.name = req.name
    camera.location = req.location
    camera.zone = req.zone
    camera.stream_url = req.stream_url
    camera.sampling_interval_seconds = req.sampling_interval_seconds
    camera.active = req.active

    await log_audit_event(
        db, current_user, "CAMERA_UPDATED", "cameras", camera.id,
        {"cadence": camera.sampling_interval_seconds, "active": camera.active}
    )
    await db.commit()
    await db.refresh(camera)
    return camera

@router.post("/{camera_id}/recordings", response_model=RecordingResponse)
async def upload_recording(
    camera_id: str,
    file: UploadFile = File(...),
    sampling_interval: float = Form(2.0),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.REVIEWER])),
    db: AsyncSession = Depends(get_db)
):
    cam_res = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = cam_res.scalars().first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty video file.")

    ext = "mp4"
    if file.filename and "." in file.filename:
        ext = file.filename.split(".")[-1].lower()

    storage_ref = storage_manager.save_bytes(content, "recordings", ext)

    recording = Recording(
        camera_id=camera_id,
        storage_ref=storage_ref,
        sampling_interval_seconds=sampling_interval or camera.sampling_interval_seconds or 2.0
    )
    db.add(recording)
    await db.flush()

    await log_audit_event(
        db, current_user, "RECORDING_UPLOADED", "recordings", recording.id,
        {"camera_id": camera_id, "storage_ref": storage_ref}
    )
    await db.commit()
    await db.refresh(recording)
    return recording
