import unittest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.core.database import Base
from app.models.models import ComplianceFlag, Notice
from app.models.enums import FlagStatus, ViolationType, UnmatchedReasonType

class TestRetentionPurge(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_purge_removes_expired_unconfirmed_but_preserves_retained_cases(self):
        async with self.async_session() as db:
            now = datetime.now(timezone.utc)
            old_time = now - timedelta(days=45) # 45 days old (retention is 30 days)
            recent_time = now - timedelta(days=5) # 5 days old

            # Flag 1: Old, unconfirmed, NOT retained -> SHOULD BE PURGED
            flag_expired = ComplianceFlag(
                frame_timestamp_ms=1000,
                frame_ref="frames/old_unconfirmed.jpg",
                violation_type=ViolationType.UNTUCKED_SHIRT,
                violation_confidence=0.75,
                status=FlagStatus.PENDING,
                is_retained_case=False,
                created_at=old_time
            )

            # Flag 2: Old, CONFIRMED and RETAINED -> MUST BE PRESERVED
            flag_retained = ComplianceFlag(
                frame_timestamp_ms=2000,
                frame_ref="frames/old_retained.jpg",
                violation_type=ViolationType.CASUAL_ATTIRE,
                violation_confidence=0.88,
                status=FlagStatus.CONFIRMED,
                is_retained_case=True, # Protected
                created_at=old_time
            )

            # Flag 3: Recent, unconfirmed -> MUST BE PRESERVED (within window)
            flag_recent = ComplianceFlag(
                frame_timestamp_ms=3000,
                frame_ref="frames/recent.jpg",
                violation_type=ViolationType.NO_ID_BADGE,
                violation_confidence=0.79,
                status=FlagStatus.PENDING,
                is_retained_case=False,
                created_at=recent_time
            )

            db.add_all([flag_expired, flag_retained, flag_recent])
            await db.commit()

            # Execute Purge Query: Delete flags older than 30 days that are NOT is_retained_case
            cutoff = now - timedelta(days=30)
            candidates_res = await db.execute(
                select(ComplianceFlag).where(
                    ComplianceFlag.created_at < cutoff,
                    ComplianceFlag.is_retained_case == False
                )
            )
            to_delete = candidates_res.scalars().all()
            self.assertEqual(len(to_delete), 1)
            self.assertEqual(to_delete[0].id, flag_expired.id)

            for item in to_delete:
                await db.delete(item)
            await db.commit()

            # Check remaining flags in database
            all_remaining = await db.execute(select(ComplianceFlag))
            remaining_ids = [f.id for f in all_remaining.scalars().all()]

            self.assertNotIn(flag_expired.id, remaining_ids)
            self.assertIn(flag_retained.id, remaining_ids)
            self.assertIn(flag_recent.id, remaining_ids)

    async def test_sent_notice_automatically_retains_case_against_purge(self):
        async with self.async_session() as db:
            now = datetime.now(timezone.utc)
            old_time = now - timedelta(days=45)

            # Create a flag that is confirmed but initially not retained
            flag = ComplianceFlag(
                frame_timestamp_ms=5000,
                frame_ref="frames/notice_case.jpg",
                violation_type=ViolationType.UNTUCKED_SHIRT,
                violation_confidence=0.85,
                status=FlagStatus.CONFIRMED,
                is_retained_case=False, # initially False
                created_at=old_time
            )
            db.add(flag)
            await db.flush()

            # Create draft notice
            notice = Notice(
                flag_id=flag.id,
                drafted_by="reviewer-1",
                subject="Dress Code Notice",
                content="Please tuck in your shirt.",
                created_at=old_time
            )
            db.add(notice)
            await db.commit()

            # Simulate notice dispatch (same atomic transaction as in notices.py /approve)
            notice.sent_by = "reviewer-1"
            notice.sent_at = now
            flag.is_retained_case = True # Tagged automatically upon dispatch
            await db.commit()

            self.assertTrue(flag.is_retained_case)

            # Run retention purge query (30-day cutoff)
            cutoff = now - timedelta(days=30)
            purge_candidates = await db.execute(
                select(ComplianceFlag).where(
                    ComplianceFlag.created_at < cutoff,
                    ComplianceFlag.is_retained_case == False
                )
            )
            candidates = purge_candidates.scalars().all()
            self.assertNotIn(flag.id, [c.id for c in candidates], "Flag with sent notice must be protected from purge candidates.")

            # Perform purge on candidates
            for item in candidates:
                await db.delete(item)
            await db.commit()

            # Confirm flag still exists in DB
            db_flag = await db.get(ComplianceFlag, flag.id)
            self.assertIsNotNone(db_flag, "Retained case flag must survive retention purge.")
            self.assertTrue(db_flag.is_retained_case)

if __name__ == "__main__":
    unittest.main()
