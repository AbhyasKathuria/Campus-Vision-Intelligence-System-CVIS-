from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.audit import log_audit_event
from app.models.models import User, ComplianceFlag, Student, TrainingExample
from app.models.enums import UserRole, FlagStatus, RejectionReasonType
from app.schemas.schemas import FlagConfirmRequest, FlagRejectRequest, FlagDismissRequest
from app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/reviews", tags=["Human Reviewer Actions"])

@router.post("/flags/{flag_id}/confirm")
async def confirm_flag(
    flag_id: str,
    req: FlagConfirmRequest,
    current_user: User = Depends(require_roles([UserRole.REVIEWER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ComplianceFlag).where(ComplianceFlag.id == flag_id))
    flag = result.scalars().first()
    if not flag:
        raise HTTPException(status_code=404, detail="Compliance flag not found.")

    if req.confirmed_student_id:
        stu_res = await db.execute(select(Student).where(Student.id == req.confirmed_student_id))
        if not stu_res.scalars().first():
            raise HTTPException(status_code=400, detail="Specified student does not exist.")
        flag.matched_student_id = req.confirmed_student_id

    flag.status = FlagStatus.CONFIRMED
    flag.reviewed_by = current_user.id
    flag.reviewed_at = datetime.now(timezone.utc)
    flag.reviewer_notes = req.notes

    # ACTIVE LEARNING DATASET (7.1): Record verified positive body crop (no faces)
    if flag.body_crop_ref:
        training_sample = TrainingExample(
            flag_id=flag.id,
            body_crop_ref=flag.body_crop_ref,
            violation_type=flag.violation_type,
            is_violation=True,
            rejection_reason=None,
            features_json=flag.violation_details,
            model_version=flag.model_version or "cvis-dresscode-v1.0",
            labeled_by=current_user.id
        )
        db.add(training_sample)

    await log_audit_event(
        db, current_user, "FLAG_CONFIRMED", "compliance_flags", flag.id,
        {"matched_student_id": flag.matched_student_id, "violation": flag.violation_type.value}
    )
    await db.commit()
    await db.refresh(flag)
    return {"status": "confirmed", "flag_id": flag.id, "message": "Flag confirmed by reviewer."}

@router.post("/flags/{flag_id}/reject")
async def reject_flag(
    flag_id: str,
    req: FlagRejectRequest,
    current_user: User = Depends(require_roles([UserRole.REVIEWER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ComplianceFlag).where(ComplianceFlag.id == flag_id))
    flag = result.scalars().first()
    if not flag:
        raise HTTPException(status_code=404, detail="Compliance flag not found.")

    flag.status = FlagStatus.REJECTED
    flag.reviewed_by = current_user.id
    flag.reviewed_at = datetime.now(timezone.utc)
    flag.rejection_reason = req.rejection_reason
    flag.rejection_notes = req.rejection_notes

    # ACTIVE LEARNING DATASET (7.1): Record verified negative body crop (no faces)
    if flag.body_crop_ref:
        training_sample = TrainingExample(
            flag_id=flag.id,
            body_crop_ref=flag.body_crop_ref,
            violation_type=flag.violation_type,
            is_violation=False,
            rejection_reason=req.rejection_reason,
            features_json=flag.violation_details,
            model_version=flag.model_version or "cvis-dresscode-v1.0",
            labeled_by=current_user.id
        )
        db.add(training_sample)

    await log_audit_event(
        db, current_user, "FLAG_REJECTED", "compliance_flags", flag.id,
        {
            "rejection_reason": req.rejection_reason.value,
            "violation": flag.violation_type.value,
            "camera_id": flag.camera_id
        }
    )
    await db.commit()
    await db.refresh(flag)
    return {
        "status": "rejected",
        "flag_id": flag.id,
        "rejection_reason": req.rejection_reason.value,
        "message": "Flag rejected by reviewer."
    }

@router.post("/flags/{flag_id}/dismiss")
async def dismiss_flag(
    flag_id: str,
    req: FlagDismissRequest,
    current_user: User = Depends(require_roles([UserRole.REVIEWER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ComplianceFlag).where(ComplianceFlag.id == flag_id))
    flag = result.scalars().first()
    if not flag:
        raise HTTPException(status_code=404, detail="Compliance flag not found.")

    flag.status = FlagStatus.REJECTED
    flag.reviewed_by = current_user.id
    flag.reviewed_at = datetime.now(timezone.utc)
    flag.rejection_reason = RejectionReasonType.NO_VIOLATION_FOUND
    flag.reviewer_notes = req.notes

    # ACTIVE LEARNING DATASET (7.1): Record negative example
    if flag.body_crop_ref:
        training_sample = TrainingExample(
            flag_id=flag.id,
            body_crop_ref=flag.body_crop_ref,
            violation_type=flag.violation_type,
            is_violation=False,
            rejection_reason=RejectionReasonType.NO_VIOLATION_FOUND,
            features_json=flag.violation_details,
            model_version=flag.model_version or "cvis-dresscode-v1.0",
            labeled_by=current_user.id
        )
        db.add(training_sample)

    await log_audit_event(
        db, current_user, "FLAG_DISMISSED", "compliance_flags", flag.id
    )
    await db.commit()
    await db.refresh(flag)
    return {"status": "dismissed", "flag_id": flag.id}
