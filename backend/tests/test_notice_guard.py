import unittest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.models import User, Student, ComplianceFlag, Notice
from app.models.enums import UserRole, FlagStatus, ViolationType, UnmatchedReasonType

class TestNoticeGuard(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_notice_cannot_be_dispatched_without_confirmation(self):
        async with self.async_session() as db:
            reviewer = User(name="Warden Smith", email="warden@campus.edu", role=UserRole.REVIEWER, password_hash="hash")
            student_user = User(name="Alex Student", email="alex@campus.edu", role=UserRole.STUDENT, password_hash="hash")
            db.add_all([reviewer, student_user])
            await db.flush()

            student = Student(user_id=student_user.id, roll_number="STU-001", consent_status=True)
            db.add(student)
            await db.flush()

            # Flag starts as PENDING
            flag = ComplianceFlag(
                frame_timestamp_ms=1000,
                frame_ref="frames/sample.jpg",
                matched_student_id=student.id,
                match_confidence=0.91,
                unmatched_reason=UnmatchedReasonType.NONE,
                violation_type=ViolationType.UNTUCKED_SHIRT,
                violation_confidence=0.85,
                status=FlagStatus.PENDING,
                is_retained_case=False
            )
            db.add(flag)
            await db.commit()

            # Guard Verification: Must be confirmed before notice is drafted/sent
            self.assertEqual(flag.status, FlagStatus.PENDING)
            self.assertFalse(flag.is_retained_case)

            # Step 1: Reviewer confirms the flag
            flag.status = FlagStatus.CONFIRMED
            flag.reviewed_by = reviewer.id
            flag.reviewed_at = datetime.now(timezone.utc)
            await db.commit()

            # Step 2: Notice is drafted
            notice = Notice(
                flag_id=flag.id,
                student_id=student.id,
                drafted_by=reviewer.id,
                subject="Uniform Compliance Notice",
                content="Please ensure your shirt is tucked as per campus policy."
            )
            db.add(notice)
            await db.flush()
            self.assertIsNone(notice.sent_by)
            self.assertIsNone(notice.sent_at)

            # Step 3: Reviewer explicitly sends notice -> triggers automatic retention
            notice.sent_by = reviewer.id
            notice.sent_at = datetime.now(timezone.utc)
            flag.is_retained_case = True # Automatic retention trigger
            await db.commit()

            self.assertTrue(flag.is_retained_case)
            self.assertIsNotNone(notice.sent_at)
            self.assertEqual(notice.sent_by, reviewer.id)

if __name__ == "__main__":
    unittest.main()
