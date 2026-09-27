from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Any

from app.core.database import get_db
from app.core.storage import storage_manager
from app.core.config import settings
from app.core.audit import log_audit_event
from app.models.models import User, ComplianceFlag, Recording, SystemConfig
from app.models.enums import UserRole
from app.schemas.schemas import SystemConfigUpdate, PurgeResponse
from app.api.deps import require_roles

router = APIRouter(prefix="/system", tags=["System Management & Retention"])

@router.get("/config")
async def get_system_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    result = await db.execute(select(SystemConfig))
    configs = {c.key: c.value_json for c in result.scalars().all()}
    
    # Defaults
    defaults = {
        "similarity_threshold": settings.SIMILARITY_THRESHOLD,
        "default_retention_days": settings.DEFAULT_RETENTION_DAYS,
        "camera_cadence_seconds": settings.DEFAULT_CAMERA_CADENCE_SECONDS,
        "telemetry_min_sample_size": settings.TELEMETRY_MIN_SAMPLE_SIZE
    }
    defaults.update(configs)
    return defaults

@router.put("/config")
async def update_system_config(
    req: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    for k, v in req.configs.items():
        res = await db.execute(select(SystemConfig).where(SystemConfig.key == k))
        item = res.scalars().first()
        if item:
            item.value_json = v
        else:
            db.add(SystemConfig(key=k, value_json=v))

    await log_audit_event(
        db, current_user, "SYSTEM_CONFIG_UPDATED", "system_configs", "global", req.configs
    )
    await db.commit()
    return {"status": "success", "updated": req.configs}

@router.post("/purge-expired", response_model=PurgeResponse)
async def purge_expired_records(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    # Lookup retention days config
    cfg_res = await db.execute(select(SystemConfig).where(SystemConfig.key == "default_retention_days"))
    cfg = cfg_res.scalars().first()
    retention_days = int(cfg.value_json) if cfg and isinstance(cfg.value_json, (int, float)) else settings.DEFAULT_RETENTION_DAYS

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

    # 1. Purge ComplianceFlags older than cutoff EXCEPT those marked is_retained_case == True
    flags_res = await db.execute(
        select(ComplianceFlag).where(
            ComplianceFlag.created_at < cutoff_date,
            ComplianceFlag.is_retained_case == False
        )
    )
    flags_to_purge = flags_res.scalars().all()
    purged_flags_count = len(flags_to_purge)
    purged_files_count = 0

    for flag in flags_to_purge:
        if flag.frame_ref:
            if storage_manager.delete_file(flag.frame_ref):
                purged_files_count += 1
        if flag.face_crop_ref:
            if storage_manager.delete_file(flag.face_crop_ref):
                purged_files_count += 1
        await db.delete(flag)

    # 2. Purge recordings older than cutoff that have no remaining flags
    rec_res = await db.execute(
        select(Recording).where(Recording.uploaded_at < cutoff_date)
    )
    recordings_to_purge = rec_res.scalars().all()
    purged_recordings_count = 0

    for rec in recordings_to_purge:
        # Check if any retained flags point to this recording
        retained_check = await db.execute(
            select(ComplianceFlag).where(
                ComplianceFlag.recording_id == rec.id,
                ComplianceFlag.is_retained_case == True
            )
        )
        if not retained_check.scalars().first():
            if rec.storage_ref:
                storage_manager.delete_file(rec.storage_ref)
                purged_files_count += 1
            await db.delete(rec)
            purged_recordings_count += 1

    await log_audit_event(
        db, current_user, "PURGE_EXECUTED", "system", "retention_worker",
        {
            "retention_days": retention_days,
            "purged_flags_count": purged_flags_count,
            "purged_recordings_count": purged_recordings_count,
            "purged_files_count": purged_files_count
        }
    )
    await db.commit()

    return PurgeResponse(
        purged_flags_count=purged_flags_count,
        purged_recordings_count=purged_recordings_count,
        purged_files_count=purged_files_count,
        retention_cutoff=cutoff_date
    )
