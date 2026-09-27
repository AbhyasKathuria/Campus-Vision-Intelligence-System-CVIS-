from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.storage import storage_manager
from app.core.config import settings
from app.core.audit import log_audit_event
from app.models.models import User, Student, FaceEmbedding
from app.models.enums import UserRole, EmbeddingSource
from app.schemas.schemas import StudentResponse, ConsentUpdateRequest
from app.api.deps import get_current_user

router = APIRouter(prefix="/consent", tags=["Biometric Consent"])

@router.get("/status", response_model=StudentResponse)
async def get_consent_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
    return student

@router.post("/update", response_model=StudentResponse)
async def update_consent(
    req: ConsentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")

    student.consent_status = req.consent_status
    if req.consent_status:
        student.consent_date = datetime.now(timezone.utc)
        action_name = "CONSENT_GRANTED"
    else:
        student.consent_date = None
        action_name = "CONSENT_REVOKED"

    # Synchronize with ML service consented_students index
    async with httpx.AsyncClient(timeout=settings.ML_TIMEOUT_SECONDS) as client:
        if req.consent_status and student.enrollment_photo_ref:
            # Query student's enrollment embedding
            emb_res = await db.execute(
                select(FaceEmbedding).where(
                    FaceEmbedding.student_id == student.id,
                    FaceEmbedding.source_type == EmbeddingSource.ENROLLMENT
                )
            )
            emb = emb_res.scalars().first()
            if emb:
                try:
                    await client.post(
                        f"{settings.ML_SERVICE_URL}/api/v1/index-faces",
                        json={
                            "collection": "consented_students",
                            "items": [{
                                "id": student.id,
                                "vector": emb.vector_json,
                                "metadata": {
                                    "roll_number": student.roll_number,
                                    "name": current_user.name
                                }
                            }]
                        }
                    )
                except Exception:
                    pass # Continue gracefully if ML service is queued
        else:
            # Rebuild or clear unconsented embeddings
            try:
                # Reload all currently consented students
                consented_res = await db.execute(
                    select(FaceEmbedding, Student).join(Student, FaceEmbedding.student_id == Student.id).where(
                        Student.consent_status == True,
                        FaceEmbedding.source_type == EmbeddingSource.ENROLLMENT
                    )
                )
                items_to_index = []
                for face_emb, stu in consented_res.all():
                    if stu.id != student.id:
                        items_to_index.append({
                            "id": stu.id,
                            "vector": face_emb.vector_json,
                            "metadata": {"roll_number": stu.roll_number}
                        })
                await client.post(f"{settings.ML_SERVICE_URL}/api/v1/clear-index/consented_students")
                if items_to_index:
                    await client.post(
                        f"{settings.ML_SERVICE_URL}/api/v1/index-faces",
                        json={"collection": "consented_students", "items": items_to_index}
                    )
            except Exception:
                pass

    await log_audit_event(
        db, current_user, action_name, "students", student.id,
        {"consent_status": req.consent_status, "roll_number": student.roll_number}
    )
    await db.commit()
    await db.refresh(student)
    return student

@router.post("/enrollment-photo", response_model=StudentResponse)
async def upload_enrollment_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty photo file.")

    # Save photo to local storage
    storage_ref = storage_manager.save_bytes(content, "enrollments", "jpg")
    student.enrollment_photo_ref = storage_ref

    # Generate face embedding from ML service
    async with httpx.AsyncClient(timeout=settings.ML_TIMEOUT_SECONDS) as client:
        try:
            resp = await client.post(
                f"{settings.ML_SERVICE_URL}/api/v1/extract-embeddings",
                files={"file": ("enrollment.jpg", content, "image/jpeg")}
            )
            if resp.status_code == 200:
                data = resp.json()
                embedding_vec = data["embedding"]
                
                # Delete old enrollment embedding if present
                old_emb = await db.execute(
                    select(FaceEmbedding).where(
                        FaceEmbedding.student_id == student.id,
                        FaceEmbedding.source_type == EmbeddingSource.ENROLLMENT
                    )
                )
                for item in old_emb.scalars().all():
                    await db.delete(item)

                face_emb = FaceEmbedding(
                    student_id=student.id,
                    source_type=EmbeddingSource.ENROLLMENT,
                    source_ref=storage_ref,
                    vector_json=embedding_vec,
                    model_version="cvis-arcface-v1.0"
                )
                db.add(face_emb)

                # If student is already consented, index immediately into consented_students
                if student.consent_status:
                    await client.post(
                        f"{settings.ML_SERVICE_URL}/api/v1/index-faces",
                        json={
                            "collection": "consented_students",
                            "items": [{
                                "id": student.id,
                                "vector": embedding_vec,
                                "metadata": {"roll_number": student.roll_number, "name": current_user.name}
                            }]
                        }
                    )
        except Exception as e:
            # Storage succeeded; ML service can re-index later
            pass

    await log_audit_event(
        db, current_user, "ENROLLMENT_PHOTO_UPLOADED", "students", student.id, {"storage_ref": storage_ref}
    )
    await db.commit()
    await db.refresh(student)
    return student
