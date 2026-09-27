from collections import Counter
from typing import List, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, ComplianceFlag, Camera
from app.models.enums import UserRole, FlagStatus, ViolationType, RejectionReasonType
from app.schemas.schemas import TelemetryResponse, ViolationFPRMetric, CameraFPRMetric
from app.api.deps import require_roles

router = APIRouter(prefix="/compliance", tags=["Compliance Telemetry"])

@router.get("/telemetry", response_model=TelemetryResponse)
async def get_compliance_telemetry(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.REVIEWER]))
):
    # Fetch all reviewed flags (confirmed or rejected)
    result = await db.execute(
        select(ComplianceFlag)
        .options(selectinload(ComplianceFlag.camera))
        .where(ComplianceFlag.status.in_([FlagStatus.CONFIRMED, FlagStatus.REJECTED]))
    )
    reviewed_flags = result.scalars().all()
    total_reviewed = len(reviewed_flags)

    # 1. Overall FPR
    total_rejected = sum(1 for f in reviewed_flags if f.status == FlagStatus.REJECTED)
    if total_reviewed >= settings.TELEMETRY_MIN_SAMPLE_SIZE:
        overall_fpr = round((total_rejected / total_reviewed * 100.0), 2)
        overall_status = "calibrated"
    else:
        overall_fpr = None
        overall_status = "insufficient_data"

    # 2. Per-Violation Breakdown
    violation_metrics: List[ViolationFPRMetric] = []
    for v_type in ViolationType:
        v_flags = [f for f in reviewed_flags if f.violation_type == v_type]
        v_tot = len(v_flags)
        v_rej = sum(1 for f in v_flags if f.status == FlagStatus.REJECTED)
        v_conf = sum(1 for f in v_flags if f.status == FlagStatus.CONFIRMED)
        
        if v_tot >= settings.TELEMETRY_MIN_SAMPLE_SIZE:
            v_fpr = round((v_rej / v_tot * 100.0), 2)
            v_status = "calibrated"
        else:
            v_fpr = None
            v_status = "insufficient_data"

        violation_metrics.append(
            ViolationFPRMetric(
                violation_type=v_type.value,
                total_reviewed=v_tot,
                rejected_count=v_rej,
                confirmed_count=v_conf,
                fpr_percentage=v_fpr,
                status_label=v_status
            )
        )

    # 3. Per-Camera & Per-Zone Breakdown
    cam_result = await db.execute(select(Camera))
    cameras = cam_result.scalars().all()
    camera_metrics: List[CameraFPRMetric] = []

    for cam in cameras:
        cam_flags = [f for f in reviewed_flags if f.camera_id == cam.id]
        c_tot = len(cam_flags)
        c_rej = [f for f in cam_flags if f.status == FlagStatus.REJECTED]
        c_rej_count = len(c_rej)

        # Calculate leading rejection reason for this camera
        leading_reason = None
        if c_rej:
            reason_counts = Counter(f.rejection_reason.value for f in c_rej if f.rejection_reason)
            if reason_counts:
                leading_reason = reason_counts.most_common(1)[0][0]

        # LOW SAMPLE SIZE GUARD: Require N >= TELEMETRY_MIN_SAMPLE_SIZE (e.g. 15)
        # before calculating FPR or flagging "Environmental Calibration Recommended"
        recommend_calibration = False
        if c_tot >= settings.TELEMETRY_MIN_SAMPLE_SIZE:
            c_fpr = round((c_rej_count / c_tot * 100.0), 2)
            if c_fpr >= 35.0 and leading_reason == RejectionReasonType.LIGHTING_CONTRAST_ARTIFACT.value:
                recommend_calibration = True
                c_status = "calibration_recommended"
            else:
                c_status = "calibrated"
        else:
            c_fpr = None
            c_status = "insufficient_data"

        camera_metrics.append(
            CameraFPRMetric(
                camera_id=cam.id,
                camera_name=cam.name,
                zone=cam.zone,
                total_reviewed=c_tot,
                rejected_count=c_rej_count,
                fpr_percentage=c_fpr,
                leading_rejection_reason=leading_reason,
                environmental_calibration_recommended=recommend_calibration,
                status_label=c_status
            )
        )

    # 4. Rejection Reason Distribution
    all_rejections = [f.rejection_reason.value for f in reviewed_flags if f.rejection_reason]
    reason_dist = dict(Counter(all_rejections))
    for r_type in RejectionReasonType:
        if r_type.value not in reason_dist:
            reason_dist[r_type.value] = 0

    return TelemetryResponse(
        overall_fpr_percentage=overall_fpr,
        total_flags_reviewed=total_reviewed,
        min_sample_size=settings.TELEMETRY_MIN_SAMPLE_SIZE,
        status_label=overall_status,
        by_violation=violation_metrics,
        by_camera=camera_metrics,
        rejection_reason_distribution=reason_dist
    )
