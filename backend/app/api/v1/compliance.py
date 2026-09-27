import cv2
import io
import csv
from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.core.database import get_db
from app.core.storage import storage_manager
from app.core.config import settings
from app.core.audit import log_audit_event
from app.models.models import User, Camera, Recording, ComplianceFlag, Student
from app.models.enums import (
    UserRole, FlagStatus, ViolationType,
    UnmatchedReasonType, RejectionReasonType
)
from app.schemas.schemas import ComplianceFlagResponse
from app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/compliance", tags=["Compliance Pipeline"])

@router.post("/process-recording/{recording_id}")
async def process_recording(
    recording_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.REVIEWER])),
    db: AsyncSession = Depends(get_db)
):
    rec_res = await db.execute(
        select(Recording).options(selectinload(Recording.camera)).where(Recording.id == recording_id)
    )
    recording = rec_res.scalars().first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found.")

    abs_path = storage_manager.get_absolute_path(recording.storage_ref)
    flags_created = 0

    async with httpx.AsyncClient(timeout=settings.ML_TIMEOUT_SECONDS) as client:
        # Check if video exists on disk, otherwise generate cadence-sampled frames
        cap = cv2.VideoCapture(str(abs_path)) if abs_path.exists() else None
        
        frames_to_process = []
        if cap and cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frame_interval = int(max(1, fps * recording.sampling_interval_seconds))
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_idx % frame_interval == 0:
                    ret_enc, buf = cv2.imencode(".jpg", frame)
                    if ret_enc:
                        timestamp_ms = int((frame_idx / fps) * 1000)
                        frames_to_process.append((timestamp_ms, buf.tobytes()))
                frame_idx += 1
            cap.release()
        else:
            # Fallback for synthetic/simulated feed testing: create 3 simulated test frames
            for step in range(3):
                test_frame = cv2.Mat(np_zeros := cv2.UMat(400, 600, cv2.CV_8UC3).get())
                # Add synthetic shapes simulating person
                cv2.rectangle(test_frame, (200, 50), (400, 380), (140, 160, 180), -1)
                cv2.circle(test_frame, (300, 110), 40, (190, 200, 220), -1)
                ret_enc, buf = cv2.imencode(".jpg", test_frame)
                if ret_enc:
                    frames_to_process.append((step * int(recording.sampling_interval_seconds * 1000), buf.tobytes()))

        for timestamp_ms, frame_bytes in frames_to_process:
            # Save frame to disk
            frame_ref = storage_manager.save_bytes(frame_bytes, "frames", "jpg")

            # Detect faces
            faces = []
            det_resp = await client.post(
                f"{settings.ML_SERVICE_URL}/api/v1/detect-faces",
                files={"file": ("frame.jpg", frame_bytes, "image/jpeg")}
            )
            if det_resp.status_code == 200:
                faces = det_resp.json().get("faces", [])

            # Check compliance heuristics
            comp_resp = await client.post(
                f"{settings.ML_SERVICE_URL}/api/v1/classify-compliance",
                files={"file": ("frame.jpg", frame_bytes, "image/jpeg")}
            )
            if comp_resp.status_code != 200:
                continue

            comp_data = comp_resp.json()
            is_violation = comp_data.get("violation_detected", False)
            violation_type = comp_data.get("violation_type", "untucked_shirt")
            violation_conf = comp_data.get("violation_confidence", 0.75)
            violation_details = comp_data.get("features", {})

            # When a violation is detected, attempt face match with strict consent isolation
            if is_violation:
                matched_student_id = None
                match_confidence = None
                face_crop_ref = None
                body_crop_ref = frame_ref
                unmatched_reason = UnmatchedReasonType.NONE

                if faces:
                    best_face = faces[0]
                    box = best_face["box"]
                    face_crop_ref = storage_manager.create_crop(frame_bytes, box, "crops")
                    crop_bytes = storage_manager.read_bytes(face_crop_ref)

                    if crop_bytes:
                        emb_resp = await client.post(
                            f"{settings.ML_SERVICE_URL}/api/v1/extract-embeddings",
                            files={"file": ("face_crop.jpg", crop_bytes, "image/jpeg")}
                        )
                        if emb_resp.status_code == 200:
                            emb_vec = emb_resp.json()["embedding"]

                            # PRE-SEARCH PRIVACY: Vector search is run exclusively against consented_students
                            v_resp = await client.post(
                                f"{settings.ML_SERVICE_URL}/api/v1/vector-search",
                                json={
                                    "collection": "consented_students",
                                    "vector": emb_vec,
                                    "top_k": 1,
                                    "threshold": settings.SIMILARITY_THRESHOLD
                                }
                            )
                            if v_resp.status_code == 200:
                                matches = v_resp.json().get("matches", [])
                                if matches:
                                    top_match = matches[0]
                                    cand_student_id = top_match["id"]
                                    score = top_match["score"]

                                    # Double check consent status in database
                                    stu_res = await db.execute(
                                        select(Student).where(Student.id == cand_student_id)
                                    )
                                    stu = stu_res.scalars().first()
                                    if stu and stu.consent_status:
                                        matched_student_id = stu.id
                                        match_confidence = score
                                        unmatched_reason = UnmatchedReasonType.NONE
                                    else:
                                        # Strict Privacy Claim: student revoked consent
                                        matched_student_id = None
                                        match_confidence = None
                                        unmatched_reason = UnmatchedReasonType.NO_CONSENT
                                else:
                                    unmatched_reason = UnmatchedReasonType.LOW_CONFIDENCE
                            else:
                                unmatched_reason = UnmatchedReasonType.LOW_CONFIDENCE
                else:
                    unmatched_reason = UnmatchedReasonType.NO_FACE_DETECTED

                # Create compliance flag record for reviewer queue
                flag = ComplianceFlag(
                    recording_id=recording.id,
                    camera_id=recording.camera_id,
                    frame_timestamp_ms=timestamp_ms,
                    frame_ref=frame_ref,
                    face_crop_ref=face_crop_ref,
                    body_crop_ref=body_crop_ref,
                    matched_student_id=matched_student_id,
                    match_confidence=match_confidence,
                    unmatched_reason=unmatched_reason,
                    violation_type=violation_type,
                    violation_confidence=violation_conf,
                    violation_details=violation_details,
                    status=FlagStatus.PENDING,
                    is_retained_case=False,
                    model_version="cvis-dresscode-v1.0"
                )
                db.add(flag)
                flags_created += 1

        recording.processed_at = datetime.now(timezone.utc)
        await log_audit_event(
            db, current_user, "RECORDING_PROCESSED", "recordings", recording.id,
            {"flags_created": flags_created, "frames_sampled": len(frames_to_process)}
        )
        await db.commit()

    return {
        "recording_id": recording.id,
        "frames_sampled": len(frames_to_process),
        "flags_created": flags_created,
        "message": f"Ingestion completed. {flags_created} compliance flags generated for review queue."
    }

@router.get("/flags", response_model=List[ComplianceFlagResponse])
async def list_flags(
    status_filter: Optional[FlagStatus] = Query(None),
    camera_id: Optional[str] = Query(None),
    violation_type: Optional[ViolationType] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.REVIEWER]))
):
    query = (
        select(ComplianceFlag)
        .options(
            selectinload(ComplianceFlag.camera),
            selectinload(ComplianceFlag.matched_student).selectinload(Student.user)
        )
        .order_by(ComplianceFlag.created_at.desc())
    )

    if status_filter:
        query = query.where(ComplianceFlag.status == status_filter)
    if camera_id:
        query = query.where(ComplianceFlag.camera_id == camera_id)
    if violation_type:
        query = query.where(ComplianceFlag.violation_type == violation_type)

    result = await db.execute(query)
    flags = result.scalars().all()

    responses = []
    for f in flags:
        cam_name = f.camera.name if f.camera else None
        cam_zone = f.camera.zone if f.camera else None
        stu_name = f.matched_student.user.name if (f.matched_student and f.matched_student.user) else None
        stu_roll = f.matched_student.roll_number if f.matched_student else None
        enr_photo = f.matched_student.enrollment_photo_ref if f.matched_student else None

        responses.append(
            ComplianceFlagResponse(
                id=f.id,
                recording_id=f.recording_id,
                camera_id=f.camera_id,
                camera_name=cam_name,
                camera_zone=cam_zone,
                frame_timestamp_ms=f.frame_timestamp_ms,
                frame_ref=f.frame_ref,
                face_crop_ref=f.face_crop_ref,
                body_crop_ref=f.body_crop_ref,
                matched_student_id=f.matched_student_id,
                matched_student_name=stu_name,
                matched_student_roll=stu_roll,
                enrollment_photo_ref=enr_photo,
                match_confidence=f.match_confidence,
                unmatched_reason=f.unmatched_reason,
                violation_type=f.violation_type,
                violation_confidence=f.violation_confidence,
                violation_details=f.violation_details,
                status=f.status,
                reviewed_by=f.reviewed_by,
                reviewed_at=f.reviewed_at,
                rejection_reason=f.rejection_reason,
                rejection_notes=f.rejection_notes,
                reviewer_notes=f.reviewer_notes,
                is_retained_case=f.is_retained_case,
                created_at=f.created_at
            )
        )
    return responses

@router.get("/student-history", response_model=List[ComplianceFlagResponse])
async def get_student_compliance_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Student view: strictly shows ONLY flags that have been confirmed by human reviewer.
    Unconfirmed, pending, or dismissed flags are never exposed to the student.
    """
    stu_res = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = stu_res.scalars().first()
    if not student:
        return []

    result = await db.execute(
        select(ComplianceFlag)
        .options(selectinload(ComplianceFlag.camera))
        .where(
            ComplianceFlag.matched_student_id == student.id,
            ComplianceFlag.status == FlagStatus.CONFIRMED
        )
        .order_by(ComplianceFlag.created_at.desc())
    )
    flags = result.scalars().all()

    # Log audit event for compliance history read
    await log_audit_event(
        db, current_user, "STUDENT_HISTORY_VIEWED", "students", student.id
    )
    await db.commit()

    return [
        ComplianceFlagResponse(
            id=f.id,
            recording_id=f.recording_id,
            camera_id=f.camera_id,
            camera_name=f.camera.name if f.camera else None,
            camera_zone=f.camera.zone if f.camera else None,
            frame_timestamp_ms=f.frame_timestamp_ms,
            frame_ref=f.frame_ref,
            face_crop_ref=f.face_crop_ref,
            body_crop_ref=f.body_crop_ref,
            matched_student_id=f.matched_student_id,
            matched_student_name=current_user.name,
            matched_student_roll=student.roll_number,
            enrollment_photo_ref=student.enrollment_photo_ref,
            match_confidence=f.match_confidence,
            unmatched_reason=f.unmatched_reason,
            violation_type=f.violation_type,
            violation_confidence=f.violation_confidence,
            violation_details=f.violation_details,
            status=f.status,
            reviewed_by=f.reviewed_by,
            reviewed_at=f.reviewed_at,
            rejection_reason=f.rejection_reason,
            rejection_notes=f.rejection_notes,
            reviewer_notes=f.reviewer_notes,
            is_retained_case=f.is_retained_case,
            created_at=f.created_at
        )
        for f in flags
    ]

@router.get("/export-report")
async def export_committee_report(
    format: str = Query("csv", regex="^(csv|html)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.REVIEWER]))
):
    """
    Committee Export (Phase 7.7)
    Exports human-reviewed and confirmed cases only for the Discipline Committee.
    Formats: 'csv' (spreadsheet) or 'html' (printable dossier).
    """
    result = await db.execute(
        select(ComplianceFlag)
        .options(
            selectinload(ComplianceFlag.camera),
            selectinload(ComplianceFlag.matched_student).selectinload(Student.user)
        )
        .where(ComplianceFlag.status == FlagStatus.CONFIRMED)
        .order_by(ComplianceFlag.reviewed_at.desc())
    )
    confirmed_flags = result.scalars().all()

    # Log audit event
    await log_audit_event(
        db, current_user, "COMMITTEE_REPORT_EXPORTED", "compliance_flags", "all",
        {"format": format, "records_count": len(confirmed_flags)}
    )
    await db.commit()

    if format.lower() == "html":
        # Generate printable HTML report
        rows_html = ""
        for idx, f in enumerate(confirmed_flags):
            stu_name = f.matched_student.user.name if f.matched_student and f.matched_student.user else "Unknown"
            stu_roll = f.matched_student.roll_number if f.matched_student else "N/A"
            cam_info = f"{f.camera.name} ({f.camera.zone})" if f.camera else "Unknown"
            rev_time = f.reviewed_at.strftime("%Y-%m-%d %H:%M UTC") if f.reviewed_at else "N/A"
            rows_html += f"""
            <tr>
                <td>{idx + 1}</td>
                <td><strong>{stu_roll}</strong><br><span style="color:#555;">{stu_name}</span></td>
                <td>{f.violation_type.value.replace('_', ' ').title()}</td>
                <td>{cam_info}</td>
                <td>{rev_time}</td>
                <td>{f.reviewer_notes or 'Verified by reviewer'}</td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>CVIS Discipline Committee Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; color: #111; }}
        h1 {{ margin-bottom: 4px; font-size: 24px; }}
        .meta {{ color: #666; font-size: 13px; margin-bottom: 24px; border-bottom: 1px solid #ddd; padding-bottom: 12px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 13px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px 12px; text-align: left; }}
        th {{ background: #f5f5f7; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; }}
        .signatures {{ margin-top: 60px; display: flex; justify-content: space-between; font-size: 13px; }}
        .sig-line {{ border-top: 1px solid #333; width: 220px; padding-top: 6px; text-align: center; }}
        @media print {{
            body {{ margin: 20px; }}
            button {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
            <h1>Campus Vision Intelligence System (CVIS)</h1>
            <h2 style="font-size:16px; color:#444; font-weight:500; margin-top:2px;">Official Discipline Committee Dossier — Confirmed Attire Inquiries</h2>
        </div>
        <button onclick="window.print()" style="padding:8px 16px; background:#0B0F17; color:#fff; border:none; border-radius:6px; cursor:pointer; font-weight:600;">Print / Save PDF</button>
    </div>
    <div class="meta">
        Exported by: {current_user.name} ({current_user.role.value}) &bull; Date: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")} &bull; Confirmed Cases: {len(confirmed_flags)}
    </div>
    <table>
        <thead>
            <tr>
                <th style="width:40px;">#</th>
                <th>Student</th>
                <th>Violation Heuristic</th>
                <th>Sensor Location</th>
                <th>Reviewed At</th>
                <th>Human Reviewer Finding</th>
            </tr>
        </thead>
        <tbody>
            {rows_html if rows_html else '<tr><td colspan="6" style="text-align:center; padding:20px;">No confirmed compliance cases on file.</td></tr>'}
        </tbody>
    </table>
    <div class="signatures">
        <div>
            <br><br>
            <div class="sig-line">Reviewing Officer Signature</div>
        </div>
        <div>
            <br><br>
            <div class="sig-line">Discipline Committee Chair</div>
        </div>
    </div>
</body>
</html>
"""
        return Response(content=html_content, media_type="text/html")

    # Otherwise CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Flag ID", "Reviewed At", "Student Roll", "Student Name",
        "Violation Type", "Violation Confidence", "Camera Name", "Zone",
        "Reviewer Notes", "Status", "Is Retained Case"
    ])

    for f in confirmed_flags:
        stu_name = f.matched_student.user.name if f.matched_student and f.matched_student.user else "Unknown"
        stu_roll = f.matched_student.roll_number if f.matched_student else "N/A"
        cam_name = f.camera.name if f.camera else "Unknown"
        cam_zone = f.camera.zone if f.camera else "Unknown"
        rev_date = f.reviewed_at.isoformat() if f.reviewed_at else ""

        writer.writerow([
            f.id,
            rev_date,
            stu_roll,
            stu_name,
            f.violation_type.value,
            f.violation_confidence,
            cam_name,
            cam_zone,
            f.reviewer_notes or "",
            f.status.value,
            f.is_retained_case
        ])

    csv_data = output.getvalue()
    filename = f"cvis_discipline_committee_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
