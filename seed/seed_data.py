import sys
from pathlib import Path

# Anchor sys.path to backend directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone, timedelta
from app.core.database import AsyncSessionLocal, init_db, engine, Base
from app.core.security import get_password_hash
from app.core.storage import storage_manager
from app.models.models import (
    User, Student, Camera, Recording, Event, EventPhoto,
    FaceEmbedding, ComplianceFlag, Notice, AuditLog, SystemConfig,
    TrainingExample, UnknownFaceCluster
)
from app.models.enums import (
    UserRole, EmbeddingSource, FlagStatus,
    ViolationType, UnmatchedReasonType, RejectionReasonType
)

def create_synthetic_portrait(name: str, bg_color=(200, 220, 240)):
    img = Image.new("RGB", (200, 250), color=bg_color)
    draw = ImageDraw.Draw(img)
    # Head
    draw.ellipse([60, 40, 140, 130], fill=(230, 200, 175), outline=(180, 150, 130), width=2)
    # Eyes
    draw.ellipse([80, 75, 92, 85], fill=(50, 50, 50))
    draw.ellipse([108, 75, 120, 85], fill=(50, 50, 50))
    # Mouth
    draw.arc([85, 95, 115, 115], start=0, end=180, fill=(150, 50, 50), width=2)
    # Body/Torso
    draw.rectangle([40, 140, 160, 250], fill=(70, 90, 130))
    # Text label
    draw.text((30, 220), name, fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def create_synthetic_event_photo(event_title: str):
    img = Image.new("RGB", (640, 480), color=(40, 45, 60))
    draw = ImageDraw.Draw(img)
    # Background banner
    draw.rectangle([50, 30, 590, 90], fill=(60, 75, 100))
    draw.text((70, 50), event_title, fill=(240, 240, 240))
    # Draw 3 simulated attendees
    coords = [(120, 180), (300, 160), (480, 190)]
    for i, (cx, cy) in enumerate(coords):
        draw.ellipse([cx-40, cy-50, cx+40, cy+40], fill=(225, 195, 170), outline=(150, 120, 100), width=2)
        draw.rectangle([cx-60, cy+45, cx+60, cy+220], fill=((i*60)%200 + 40, 90, 120))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

async def run_seed():
    print("Initializing database tables...")
    async with engine.begin() as conn:
        print("Resetting database schema...")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        print("Populating seed records...")
        # Add system configurations
        configs = [
            ("similarity_threshold", 0.65),
            ("default_retention_days", 30),
            ("camera_cadence_seconds", 2.0),
            ("telemetry_min_sample_size", 15)
        ]
        for k, v in configs:
            db.add(SystemConfig(key=k, value_json=v))

        # 1. Create Core Users
        pw_hash = get_password_hash("Password123!")

        admin = User(name="System Administrator", email="admin@campus.edu", role=UserRole.ADMIN, password_hash=pw_hash)
        reviewer = User(name="Warden Arthur Pendelton", email="reviewer@campus.edu", role=UserRole.REVIEWER, password_hash=pw_hash)
        photographer = User(name="Elena Rostova (Campus Media)", email="photographer@campus.edu", role=UserRole.EVENT_STAFF, password_hash=pw_hash)
        db.add_all([admin, reviewer, photographer])
        await db.flush()

        # 2. Create Students (Consented & Unconsented)
        student_data = [
            ("Alice Walker", "alice@campus.edu", "STU-2024-001", True),
            ("Bob Vance", "bob@campus.edu", "STU-2024-002", True),
            ("Carol Danvers", "carol@campus.edu", "STU-2024-003", False), # Unconsented
            ("David Kim", "dave@campus.edu", "STU-2024-004", True),
            ("Eva Green", "eva@campus.edu", "STU-2024-005", False),       # Unconsented
        ]

        students = []
        for name, email, roll, consent in student_data:
            u = User(name=name, email=email, role=UserRole.STUDENT, password_hash=pw_hash)
            db.add(u)
            await db.flush()

            # Synthetic portrait photo
            photo_bytes = create_synthetic_portrait(name)
            photo_ref = storage_manager.save_bytes(photo_bytes, "enrollments", "jpg")

            stu = Student(
                user_id=u.id,
                roll_number=roll,
                enrollment_photo_ref=photo_ref,
                consent_status=consent,
                consent_date=datetime.now(timezone.utc) if consent else None
            )
            db.add(stu)
            await db.flush()

            # Generate synthetic 512-dim embedding
            v = np.random.randn(512).astype(np.float32)
            v /= np.linalg.norm(v)

            emb = FaceEmbedding(
                student_id=stu.id,
                source_type=EmbeddingSource.ENROLLMENT,
                source_ref=photo_ref,
                vector_json=v.tolist(),
                model_version="cvis-arcface-v1.0"
            )
            db.add(emb)
            students.append((stu, u, v))

        # 3. Create Cameras
        cameras = [
            Camera(name="Library Main Foyer", location="North Academic Block, Level 1", zone="North Academic Block", stream_url="rtsp://simulated/cam1", sampling_interval_seconds=2.0, active=True),
            Camera(name="Science Complex Lab 3", location="Science Wing, 2nd Floor", zone="Science Block", stream_url="rtsp://simulated/cam2", sampling_interval_seconds=2.0, active=True),
            Camera(name="Hostel Quad North", location="Residential Sector Gate B", zone="Residential Quad", stream_url="rtsp://simulated/cam3", sampling_interval_seconds=3.0, active=True),
            Camera(name="Cafeteria Central Atrium", location="Student Union Building", zone="Student Center", stream_url="rtsp://simulated/cam4", sampling_interval_seconds=1.5, active=True),
        ]
        db.add_all(cameras)
        await db.flush()

        # 4. Create Events & Photos
        events = [
            Event(name="Orientation Week 2026", description="Freshman welcoming ceremony and club fair", date="2026-09-10", created_by=photographer.id),
            Event(name="Annual Science & Innovation Expo", description="Departmental projects presentation", date="2026-09-18", created_by=photographer.id),
            Event(name="Inter-University Sports Gala", description="Athletics and sports meet", date="2026-09-22", created_by=photographer.id),
        ]
        db.add_all(events)
        await db.flush()

        for ev in events:
            for p_idx in range(3):
                p_bytes = create_synthetic_event_photo(f"{ev.name} - Photo {p_idx+1}")
                p_ref = storage_manager.save_bytes(p_bytes, "event_photos", "jpg")
                t_ref = storage_manager.create_thumbnail(p_bytes)

                photo = EventPhoto(
                    event_id=ev.id,
                    storage_ref=p_ref,
                    thumbnail_ref=t_ref,
                    face_count=3,
                    processed_at=datetime.now(timezone.utc)
                )
                db.add(photo)
                await db.flush()

                # Add 3 face embeddings per photo (one matches Alice, one matches Bob, one random)
                for f_idx in range(3):
                    if f_idx == 0:
                        vec = students[0][2].tolist() # Alice match
                    elif f_idx == 1:
                        vec = students[1][2].tolist() # Bob match
                    else:
                        rand_v = np.random.randn(512).astype(np.float32)
                        rand_v /= np.linalg.norm(rand_v)
                        vec = rand_v.tolist()

                    db.add(FaceEmbedding(
                        source_type=EmbeddingSource.EVENT_PHOTO,
                        source_ref=photo.id,
                        bounding_box={"x": 100 + f_idx * 160, "y": 140, "width": 90, "height": 90},
                        vector_json=vec,
                        model_version="cvis-arcface-v1.0"
                    ))

        # 5. Create Compliance Flags for Ops Review Queue
        alice_stu = students[0][0]
        bob_stu = students[1][0]
        dave_stu = students[3][0]

        # Flag 1: PENDING untucked shirt - matched to Alice (consented)
        f1_bytes = create_synthetic_portrait("Alice Violation", bg_color=(180, 200, 220))
        f1_frame = storage_manager.save_bytes(f1_bytes, "frames", "jpg")
        f1_face = storage_manager.create_crop(f1_bytes, {"x": 60, "y": 40, "width": 80, "height": 90}, "crops")
        flag1 = ComplianceFlag(
            camera_id=cameras[1].id, # Science Lab
            frame_timestamp_ms=14200,
            frame_ref=f1_frame,
            face_crop_ref=f1_face,
            body_crop_ref=f1_frame,
            matched_student_id=alice_stu.id,
            match_confidence=0.91,
            unmatched_reason=UnmatchedReasonType.NONE,
            violation_type=ViolationType.UNTUCKED_SHIRT,
            violation_confidence=0.86,
            violation_details={
                "waistband_edge_gradient": 8.4,
                "waistband_max_edge": 14.2,
                "lower_hem_dispersion": 42.1,
                "collar_detected": True
            },
            status=FlagStatus.PENDING,
            is_retained_case=False
        )

        # Flag 2: PENDING casual attire - matched to Bob (consented)
        f2_bytes = create_synthetic_portrait("Bob Casual Attire", bg_color=(220, 200, 180))
        f2_frame = storage_manager.save_bytes(f2_bytes, "frames", "jpg")
        f2_face = storage_manager.create_crop(f2_bytes, {"x": 60, "y": 40, "width": 80, "height": 90}, "crops")
        flag2 = ComplianceFlag(
            camera_id=cameras[0].id, # Library
            frame_timestamp_ms=28400,
            frame_ref=f2_frame,
            face_crop_ref=f2_face,
            body_crop_ref=f2_frame,
            matched_student_id=bob_stu.id,
            match_confidence=0.87,
            unmatched_reason=UnmatchedReasonType.NONE,
            violation_type=ViolationType.CASUAL_ATTIRE,
            violation_confidence=0.78,
            violation_details={
                "collar_detected": False,
                "collar_gradient_score": 0.02,
                "torso_contrast_difference": 12.5
            },
            status=FlagStatus.PENDING,
            is_retained_case=False
        )

        # Flag 3: PENDING unconsented violation - NO MATCH ALLOWED
        f3_bytes = create_synthetic_portrait("Unconsented Student", bg_color=(200, 200, 200))
        f3_frame = storage_manager.save_bytes(f3_bytes, "frames", "jpg")
        flag3 = ComplianceFlag(
            camera_id=cameras[1].id, # Science Lab
            frame_timestamp_ms=45100,
            frame_ref=f3_frame,
            body_crop_ref=f3_frame,
            matched_student_id=None, # Strictly nullified
            match_confidence=None,
            unmatched_reason=UnmatchedReasonType.NO_CONSENT,
            violation_type=ViolationType.LAB_COAT_MISSING,
            violation_confidence=0.89,
            violation_details={"white_coat_coverage_ratio": 0.12},
            status=FlagStatus.PENDING,
            is_retained_case=False
        )

        # Flag 4: CONFIRMED flag for Dave with Draft Notice
        f4_bytes = create_synthetic_portrait("Dave Notice Sent", bg_color=(190, 210, 230))
        f4_frame = storage_manager.save_bytes(f4_bytes, "frames", "jpg")
        flag4 = ComplianceFlag(
            camera_id=cameras[0].id,
            frame_timestamp_ms=10500,
            frame_ref=f4_frame,
            matched_student_id=dave_stu.id,
            match_confidence=0.94,
            unmatched_reason=UnmatchedReasonType.NONE,
            violation_type=ViolationType.NO_ID_BADGE,
            violation_confidence=0.82,
            violation_details={"id_badge_detected": False},
            status=FlagStatus.CONFIRMED,
            reviewed_by=reviewer.id,
            reviewed_at=datetime.now(timezone.utc) - timedelta(hours=3),
            reviewer_notes="Confirmed via side-by-side inspection.",
            is_retained_case=True, # Notice sent, retained case
            model_version="cvis-dresscode-v1.0"
        )
        db.add_all([flag1, flag2, flag3, flag4])
        await db.flush()

        notice = Notice(
            flag_id=flag4.id,
            student_id=dave_stu.id,
            drafted_by=reviewer.id,
            sent_by=reviewer.id,
            sent_at=datetime.now(timezone.utc) - timedelta(hours=2),
            subject="Dress Code Reminder: Campus ID Badge Protocol",
            content="Dear David,\n\nDuring routine operations in Library Main Foyer, you were observed without your university ID badge visible. Please remember to display your badge at all times.\n\nDiscipline Committee"
        )
        db.add(notice)

        # Flag 5 & 6: Historical Rejections for Telemetry
        flag5 = ComplianceFlag(
            camera_id=cameras[0].id,
            frame_timestamp_ms=6200,
            frame_ref=f1_frame,
            body_crop_ref=f1_frame,
            violation_type=ViolationType.UNTUCKED_SHIRT,
            violation_confidence=0.71,
            status=FlagStatus.REJECTED,
            reviewed_by=reviewer.id,
            reviewed_at=datetime.now(timezone.utc) - timedelta(days=1),
            rejection_reason=RejectionReasonType.LIGHTING_CONTRAST_ARTIFACT,
            rejection_notes="Lens flare on foyer camera caused false waistline edge.",
            is_retained_case=False,
            model_version="cvis-dresscode-v1.0"
        )
        flag6 = ComplianceFlag(
            camera_id=cameras[2].id,
            frame_timestamp_ms=8800,
            frame_ref=f2_frame,
            body_crop_ref=f2_frame,
            violation_type=ViolationType.CASUAL_ATTIRE,
            violation_confidence=0.69,
            status=FlagStatus.REJECTED,
            reviewed_by=reviewer.id,
            reviewed_at=datetime.now(timezone.utc) - timedelta(days=1),
            rejection_reason=RejectionReasonType.FALSE_POSITIVE_CLOTHING,
            rejection_notes="Formal turtleneck misinterpreted as casual t-shirt.",
            is_retained_case=False,
            model_version="cvis-dresscode-v1.0"
        )
        db.add_all([flag5, flag6])
        await db.flush()

        # 6. Seed Active Learning Training Examples (Phase 7.1)
        # PRIVACY GUARANTEE: Body crops only, never unconsented student faces
        t1 = TrainingExample(
            flag_id=flag4.id,
            body_crop_ref=f4_frame,
            violation_type=flag4.violation_type,
            is_violation=True,
            rejection_reason=None,
            features_json=flag4.violation_details,
            model_version="cvis-dresscode-v1.0",
            labeled_by=reviewer.id
        )
        t2 = TrainingExample(
            flag_id=flag5.id,
            body_crop_ref=f1_frame,
            violation_type=flag5.violation_type,
            is_violation=False,
            rejection_reason=flag5.rejection_reason,
            features_json={"waistline_sobel_gradient": 14.2},
            model_version="cvis-dresscode-v1.0",
            labeled_by=reviewer.id
        )
        t3 = TrainingExample(
            flag_id=flag6.id,
            body_crop_ref=f2_frame,
            violation_type=flag6.violation_type,
            is_violation=False,
            rejection_reason=flag6.rejection_reason,
            features_json={"collar_gradient_score": 0.02},
            model_version="cvis-dresscode-v1.0",
            labeled_by=reviewer.id
        )
        db.add_all([t1, t2, t3])

        # 7. Seed Unidentified Face Cluster (Phase 7.2)
        cluster1 = UnknownFaceCluster(
            event_id=events[0].id,
            cluster_label="Unidentified Person #1",
            representative_crop_ref=f1_face,
            face_count=3,
            member_embedding_ids=["seed-face-emb-1", "seed-face-emb-2", "seed-face-emb-3"]
        )
        db.add(cluster1)

        # Audit logs for demo
        db.add(AuditLog(
            actor_id=admin.id,
            actor_role=UserRole.ADMIN,
            action="SYSTEM_SEEDED",
            target_type="system",
            target_id="genesis",
            metadata_json={"seed_version": "1.1.0", "phase": 7}
        ))

        await db.commit()
        print("Database successfully seeded with realistic synthetic CVIS data!")

if __name__ == "__main__":
    asyncio.run(run_seed())
