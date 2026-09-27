import asyncio
import unittest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.models import User, Student, ComplianceFlag
from app.models.enums import UserRole, FlagStatus, ViolationType, UnmatchedReasonType

class TestComplianceConsent(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_unconsented_student_is_excluded_from_flag(self):
        async with self.async_session() as db:
            # Create user and student without consent
            user = User(name="Charlie Unconsented", email="charlie@campus.edu", role=UserRole.STUDENT, password_hash="hash")
            db.add(user)
            await db.flush()

            student = Student(user_id=user.id, roll_number="STU-0099", consent_status=False)
            db.add(student)
            await db.flush()

            # Simulate compliance ingestion detecting violation on an unconsented student
            # Pre-search or matching check confirms student has NOT consented
            flag = ComplianceFlag(
                frame_timestamp_ms=1000,
                frame_ref="frames/test_unconsented.jpg",
                matched_student_id=None, # Strictly nullified
                match_confidence=None,
                unmatched_reason=UnmatchedReasonType.NO_CONSENT, # Explicit reason
                violation_type=ViolationType.UNTUCKED_SHIRT,
                violation_confidence=0.88,
                status=FlagStatus.PENDING,
                is_retained_case=False
            )
            db.add(flag)
            await db.commit()

            # Verify flag in DB
            self.assertIsNone(flag.matched_student_id)
            self.assertEqual(flag.unmatched_reason, UnmatchedReasonType.NO_CONSENT)
            self.assertEqual(flag.status, FlagStatus.PENDING)

    async def test_consented_student_can_be_matched(self):
        async with self.async_session() as db:
            user = User(name="Diana Consented", email="diana@campus.edu", role=UserRole.STUDENT, password_hash="hash")
            db.add(user)
            await db.flush()

            student = Student(user_id=user.id, roll_number="STU-0100", consent_status=True)
            db.add(student)
            await db.flush()

            # Flag matched to consented student
            flag = ComplianceFlag(
                frame_timestamp_ms=2000,
                frame_ref="frames/test_consented.jpg",
                matched_student_id=student.id,
                match_confidence=0.89,
                unmatched_reason=UnmatchedReasonType.NONE,
                violation_type=ViolationType.UNTUCKED_SHIRT,
                violation_confidence=0.82,
                status=FlagStatus.PENDING,
                is_retained_case=False
            )
            db.add(flag)
            await db.commit()

            self.assertEqual(flag.matched_student_id, student.id)
            self.assertEqual(flag.unmatched_reason, UnmatchedReasonType.NONE)

if __name__ == "__main__":
    unittest.main()
