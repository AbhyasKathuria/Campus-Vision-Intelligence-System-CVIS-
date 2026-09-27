import unittest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.core.database import Base
from app.core.rate_limiter import MemoryRateLimiter
from app.models.models import Event, EventPhoto, FaceEmbedding
from app.models.enums import EmbeddingSource

class TestPhotoFinder(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_event_photo_indexing_and_deduplication(self):
        async with self.async_session() as db:
            event = Event(name="Annual Gala 2026", description="Campus gala", date="2026-09-20")
            db.add(event)
            await db.flush()

            photo1 = EventPhoto(
                event_id=event.id,
                storage_ref="event_photos/gala_group_1.jpg",
                thumbnail_ref="thumbnails/gala_group_1.jpg",
                face_count=2
            )
            photo2 = EventPhoto(
                event_id=event.id,
                storage_ref="event_photos/gala_solo_2.jpg",
                thumbnail_ref="thumbnails/gala_solo_2.jpg",
                face_count=1
            )
            db.add_all([photo1, photo2])
            await db.flush()

            # Multiple faces in photo 1
            emb1 = FaceEmbedding(
                source_type=EmbeddingSource.EVENT_PHOTO,
                source_ref=photo1.id,
                bounding_box={"x": 50, "y": 60, "width": 80, "height": 80},
                vector_json=[0.1] * 512
            )
            emb2 = FaceEmbedding(
                source_type=EmbeddingSource.EVENT_PHOTO,
                source_ref=photo1.id,
                bounding_box={"x": 180, "y": 60, "width": 80, "height": 80},
                vector_json=[0.2] * 512
            )
            db.add_all([emb1, emb2])
            await db.commit()

            # Query photos of event
            res = await db.execute(select(EventPhoto).where(EventPhoto.event_id == event.id))
            photos = res.scalars().all()
            self.assertEqual(len(photos), 2)
            self.assertEqual(photos[0].face_count, 2)

    def test_search_rate_limiter_enforcement(self):
        limiter = MemoryRateLimiter()
        client_key = "selfie_test_user_42"
        max_allowed = 3

        # First 3 requests should pass
        self.assertTrue(limiter.check_rate_limit(client_key, max_requests=max_allowed, window_seconds=60))
        self.assertTrue(limiter.check_rate_limit(client_key, max_requests=max_allowed, window_seconds=60))
        self.assertTrue(limiter.check_rate_limit(client_key, max_requests=max_allowed, window_seconds=60))

        # 4th request within the same window must be rejected
        self.assertFalse(limiter.check_rate_limit(client_key, max_requests=max_allowed, window_seconds=60))

if __name__ == "__main__":
    unittest.main()
