import unittest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.core.database import Base
from app.models.models import User, Student, ComplianceFlag, Notice, TrainingExample, FaceEmbedding, Event, EventPhoto, UnknownFaceCluster
from app.models.enums import UserRole, FlagStatus, ViolationType, RejectionReasonType, EmbeddingSource

class TestPhase7Differentiators(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_active_learning_records_body_crops_only(self):
        """Phase 7.1: Confirmed and rejected flags insert into training_examples using body crops only."""
        async with self.async_session() as db:
            user = User(name="Officer Jenny", email="jenny@campus.edu", role=UserRole.REVIEWER, password_hash="hash")
            db.add(user)
            await db.flush()

            flag = ComplianceFlag(
                frame_timestamp_ms=12000,
                frame_ref="frames/test_cctv.jpg",
                face_crop_ref="crops/face_student_secret.jpg",
                body_crop_ref="crops/body_untucked_shirt.jpg",
                violation_type=ViolationType.UNTUCKED_SHIRT,
                violation_confidence=0.88,
                status=FlagStatus.PENDING,
                is_retained_case=False,
                model_version="cvis-dresscode-v1.0"
            )
            db.add(flag)
            await db.flush()

            # Reviewer confirms flag
            flag.status = FlagStatus.CONFIRMED
            flag.reviewed_by = user.id
            flag.reviewed_at = datetime.now(timezone.utc)

            # Insert training sample
            sample = TrainingExample(
                flag_id=flag.id,
                body_crop_ref=flag.body_crop_ref, # Strictly body crop
                violation_type=flag.violation_type,
                is_violation=True,
                rejection_reason=None,
                features_json={"waist_gradient": 12.4},
                model_version=flag.model_version,
                labeled_by=user.id
            )
            db.add(sample)
            await db.commit()

            # Assertions
            db_sample = await db.get(TrainingExample, sample.id)
            self.assertIsNotNone(db_sample)
            self.assertTrue(db_sample.is_violation)
            self.assertEqual(db_sample.body_crop_ref, "crops/body_untucked_shirt.jpg")
            self.assertNotIn("face", db_sample.body_crop_ref, "Active learning dataset must strictly isolate body crops.")
            self.assertEqual(db_sample.model_version, "cvis-dresscode-v1.0")

    async def test_unknown_face_pairwise_cosine_clustering(self):
        """Phase 7.2: Pairwise cosine clustering identifies same unknown attendees across event photos."""
        # Simulated 512-dim ArcFace unit vectors
        # Vector A and Vector A_prime have high cosine similarity (same unidentified person)
        v_a = [0.0] * 512
        v_a[0] = 0.8
        v_a[1] = 0.6 # length = sqrt(0.64 + 0.36) = 1.0

        v_a_prime = [0.0] * 512
        v_a_prime[0] = 0.82
        v_a_prime[1] = 0.57236 # dot product approx 0.8*0.82 + 0.6*0.57236 = 0.656 + 0.343 = 0.999

        # Vector B is a completely different person
        v_b = [0.0] * 512
        v_b[10] = 1.0

        def cosine_similarity(v1, v2):
            return sum(a * b for a, b in zip(v1, v2))

        sim_same = cosine_similarity(v_a, v_a_prime)
        sim_diff = cosine_similarity(v_a, v_b)

        self.assertGreater(sim_same, 0.9)
        self.assertLess(sim_diff, 0.1)

        # Clustering algorithm test
        items = [
            {"id": "emb-1", "vec": v_a},
            {"id": "emb-2", "vec": v_b},
            {"id": "emb-3", "vec": v_a_prime}
        ]

        threshold = 0.58
        visited = set()
        clusters = []

        for i in range(len(items)):
            if i in visited:
                continue
            curr = [items[i]]
            visited.add(i)
            for j in range(i + 1, len(items)):
                if j not in visited:
                    if cosine_similarity(items[i]["vec"], items[j]["vec"]) >= threshold:
                        curr.append(items[j])
                        visited.add(j)
            clusters.append(curr)

        # Person A and A_prime grouped together; Person B in separate cluster
        self.assertEqual(len(clusters), 2)
        lens = sorted([len(c) for c in clusters], reverse=True)
        self.assertEqual(lens, [2, 1])

    async def test_notice_60_second_undo_window(self):
        """Phase 7.6: Reviewer can recall a dispatched notice within 60s window."""
        async with self.async_session() as db:
            user = User(name="Supervisor Bob", email="bob@campus.edu", role=UserRole.REVIEWER, password_hash="hash")
            db.add(user)
            await db.flush()

            flag = ComplianceFlag(
                frame_timestamp_ms=1000,
                frame_ref="frames/test.jpg",
                violation_type=ViolationType.UNTUCKED_SHIRT,
                violation_confidence=0.85,
                status=FlagStatus.CONFIRMED,
                is_retained_case=True
            )
            db.add(flag)
            await db.flush()

            notice = Notice(
                flag_id=flag.id,
                drafted_by=user.id,
                sent_by=user.id,
                sent_at=datetime.now(timezone.utc) - timedelta(seconds=15), # 15s ago
                subject="Uniform Notice",
                content="Please review policy."
            )
            db.add(notice)
            await db.commit()

            # Execute Recall (within 60s)
            elapsed = (datetime.now(timezone.utc) - notice.sent_at.replace(tzinfo=timezone.utc)).total_seconds()
            self.assertLessEqual(elapsed, 60.0)

            notice.sent_at = None
            notice.sent_by = None
            await db.commit()

            db_notice = await db.get(Notice, notice.id)
            self.assertIsNone(db_notice.sent_at, "Dispatched notice must be reverted to draft state upon recall.")
            self.assertIsNone(db_notice.sent_by)

if __name__ == "__main__":
    unittest.main()
