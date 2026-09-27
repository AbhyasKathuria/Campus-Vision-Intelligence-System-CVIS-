from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.audit import log_audit_event
from app.models.models import User, ComplianceFlag, Notice
from app.models.enums import UserRole, FlagStatus
from app.schemas.schemas import NoticeDraftRequest, NoticeResponse, NoticeApproveRequest
from app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/notices", tags=["Notice Management"])

@router.post("/draft", response_model=NoticeResponse)
async def draft_notice(
    req: NoticeDraftRequest,
    current_user: User = Depends(require_roles([UserRole.REVIEWER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    flag_res = await db.execute(select(ComplianceFlag).where(ComplianceFlag.id == req.flag_id))
    flag = flag_res.scalars().first()
    if not flag:
        raise HTTPException(status_code=404, detail="Compliance flag not found.")

    # Guard: A notice can only be drafted for a confirmed flag with an identified student
    if flag.status != FlagStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot draft a notice for an unconfirmed flag. A human reviewer must confirm first."
        )

    if not flag.matched_student_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot draft a notice without an identified and confirmed student."
        )

    notice = Notice(
        flag_id=flag.id,
        student_id=flag.matched_student_id,
        drafted_by=current_user.id,
        sent_by=None,
        sent_at=None,
        subject=req.subject,
        content=req.content
    )
    db.add(notice)
    await db.flush()

    await log_audit_event(
        db, current_user, "NOTICE_DRAFTED", "notices", notice.id,
        {"flag_id": flag.id, "student_id": flag.matched_student_id}
    )
    await db.commit()
    await db.refresh(notice)
    return notice

@router.post("/{notice_id}/send", response_model=NoticeResponse)
async def send_notice(
    notice_id: str,
    req: NoticeApproveRequest,
    current_user: User = Depends(require_roles([UserRole.REVIEWER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    not_res = await db.execute(select(Notice).where(Notice.id == notice_id))
    notice = not_res.scalars().first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found.")

    flag_res = await db.execute(select(ComplianceFlag).where(ComplianceFlag.id == notice.flag_id))
    flag = flag_res.scalars().first()
    if not flag or flag.status != FlagStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot dispatch notice: Underlying compliance flag has not been confirmed."
        )

    notice.sent_by = current_user.id
    notice.sent_at = datetime.now(timezone.utc)

    # AUTOMATIC RETENTION: Tag underlying flag as an active retained case to protect from purge!
    flag.is_retained_case = True

    await log_audit_event(
        db, current_user, "NOTICE_SENT", "notices", notice.id,
        {"flag_id": flag.id, "student_id": notice.student_id, "sent_by": current_user.id}
    )
    await db.commit()
    await db.refresh(notice)
    return notice

@router.get("/flag/{flag_id}", response_model=NoticeResponse)
async def get_notice_for_flag(
    flag_id: str,
    current_user: User = Depends(require_roles([UserRole.REVIEWER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Notice).where(Notice.flag_id == flag_id))
    notice = result.scalars().first()
    if not notice:
        raise HTTPException(status_code=404, detail="No notice found for this flag.")
    return notice

@router.post("/{notice_id}/recall")
async def recall_notice(
    notice_id: str,
    current_user: User = Depends(require_roles([UserRole.REVIEWER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Reviewer Undo Window (Phase 7.6)
    Allows revoking/recalling a dispatched notice within a 60-second safety window.
    """
    not_res = await db.execute(select(Notice).where(Notice.id == notice_id))
    notice = not_res.scalars().first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found.")

    if not notice.sent_at:
        raise HTTPException(status_code=400, detail="Notice has not been dispatched yet.")

    # Check 60-second window (with 10s leeway for network latency -> 70s)
    now_utc = datetime.now(timezone.utc)
    sent_utc = notice.sent_at if notice.sent_at.tzinfo else notice.sent_at.replace(tzinfo=timezone.utc)
    elapsed = (now_utc - sent_utc).total_seconds()
    if elapsed > 70:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Undo window expired ({int(elapsed)}s elapsed; maximum allowed is 60s)."
        )

    notice.sent_at = None
    notice.sent_by = None

    await log_audit_event(
        db, current_user, "NOTICE_DISPATCH_RECALLED", "notices", notice.id,
        {"flag_id": notice.flag_id, "student_id": notice.student_id, "recalled_by": current_user.id}
    )
    await db.commit()
    return {"status": "recalled", "notice_id": notice.id, "message": "Notice dispatch successfully recalled."}
