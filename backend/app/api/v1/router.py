from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.consent import router as consent_router
from app.api.v1.events import router as events_router
from app.api.v1.search import router as search_router
from app.api.v1.cameras import router as cameras_router
from app.api.v1.compliance import router as compliance_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.notices import router as notices_router
from app.api.v1.telemetry import router as telemetry_router
from app.api.v1.system import router as system_router
from app.api.v1.audit import router as audit_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(consent_router)
api_router.include_router(events_router)
api_router.include_router(search_router)
api_router.include_router(cameras_router)
api_router.include_router(compliance_router)
api_router.include_router(reviews_router)
api_router.include_router(notices_router)
api_router.include_router(telemetry_router)
api_router.include_router(system_router)
api_router.include_router(audit_router)
