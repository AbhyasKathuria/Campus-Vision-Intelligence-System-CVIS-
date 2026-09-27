import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.tasks.worker import celery_app
from app.core.database import AsyncSessionLocal
from app.core.storage import storage_manager
from app.core.config import settings
from app.core.audit import log_audit_event
from app.models.models import ComplianceFlag, Recording, SystemConfig

async def _execute_purge_async():
    async with AsyncSessionLocal() as db:
        cfg_res = await db.execute(select(SystemConfig).where(SystemConfig.key == "default_retention_days"))
        cfg = cfg_res.scalars().first()
        retention_days = int(cfg.value_json) if cfg and isinstance(cfg.value_json, (int, float)) else settings.DEFAULT_RETENTION_DAYS

        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        # Query unconfirmed and non-retained flags older than cutoff
        flags_res = await db.execute(
            select(ComplianceFlag).where(
                ComplianceFlag.created_at < cutoff,
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

        # Query expired recordings without retained cases
        rec_res = await db.execute(select(Recording).where(Recording.uploaded_at < cutoff))
        recordings_to_purge = rec_res.scalars().all()
        purged_recordings_count = 0

        for rec in recordings_to_purge:
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
            db, None, "SCHEDULED_PURGE_EXECUTED", "system", "celery_worker",
            {
                "retention_days": retention_days,
                "purged_flags_count": purged_flags_count,
                "purged_recordings_count": purged_recordings_count,
                "purged_files_count": purged_files_count
            }
        )
        await db.commit()
        return {
            "purged_flags": purged_flags_count,
            "purged_recordings": purged_recordings_count,
            "purged_files": purged_files_count
        }

@celery_app.task(name="app.tasks.purge_job.run_scheduled_retention_purge")
def run_scheduled_retention_purge():
    return asyncio.run(_execute_purge_async())
