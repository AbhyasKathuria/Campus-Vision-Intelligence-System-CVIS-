import os
from pathlib import Path
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel as BaseSettings

# Resolve Project Root: <root>/backend/app/core/config.py -> parents[3] is <root>
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_FILE = PROJECT_ROOT / "cvis.db"
DEFAULT_STORAGE_DIR = PROJECT_ROOT / "storage_data"

# Ensure storage directory exists
DEFAULT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    PROJECT_NAME: str = "Campus Vision Intelligence System (CVIS)"
    
    # Database: Use absolute path if not provided via environment
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite+aiosqlite:///{DEFAULT_DB_FILE.as_posix()}"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # JWT Authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET", "cvis_super_secret_production_key_32_bytes_min!")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours
    
    # ML Microservice
    ML_SERVICE_URL: str = os.getenv("ML_SERVICE_URL", "http://localhost:8001")
    ML_TIMEOUT_SECONDS: int = 30
    
    # Storage: Absolute path to storage_data
    STORAGE_LOCAL_ROOT: str = os.getenv("STORAGE_LOCAL_ROOT", str(DEFAULT_STORAGE_DIR))
    MAX_UPLOAD_SELFIE_MB: int = 10
    MAX_UPLOAD_BULK_ZIP_MB: int = 500
    MAX_UPLOAD_VIDEO_MB: int = 200
    
    # Rate Limits (requests / minute)
    RATE_LIMIT_LOGIN: int = 5
    RATE_LIMIT_SELFIE_SEARCH: int = 10
    RATE_LIMIT_BULK_UPLOAD: int = 5
    
    # Compliance & Ingestion
    DEFAULT_CAMERA_CADENCE_SECONDS: float = 2.0
    DEFAULT_RETENTION_DAYS: int = 30
    SIMILARITY_THRESHOLD: float = 0.65
    TELEMETRY_MIN_SAMPLE_SIZE: int = 15

settings = Settings()
