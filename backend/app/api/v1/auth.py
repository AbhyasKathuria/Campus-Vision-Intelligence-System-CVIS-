from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.rate_limiter import enforce_rate_limit
from app.core.config import settings
from app.core.audit import log_audit_event
from app.models.models import User, Student
from app.models.enums import UserRole
from app.schemas.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(req: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check duplicate email
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    new_user = User(
        name=req.name,
        email=req.email,
        role=req.role,
        password_hash=get_password_hash(req.password)
    )
    db.add(new_user)
    await db.flush()

    if req.role == UserRole.STUDENT:
        roll = req.roll_number or f"STU-{new_user.id[:8].upper()}"
        student = Student(
            user_id=new_user.id,
            roll_number=roll,
            consent_status=False
        )
        db.add(student)
        await db.flush()

    await log_audit_event(
        db, new_user, "USER_REGISTERED", "users", new_user.id, {"role": req.role.value}
    )
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=TokenResponse)
async def login(req: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    # Rate limit login attempts: 5 per minute per IP
    enforce_rate_limit(request, "login", max_requests=settings.RATE_LIMIT_LOGIN, window_seconds=60)

    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalars().first()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    token = create_access_token({"sub": user.id, "role": user.role.value, "email": user.email})
    await log_audit_event(db, user, "USER_LOGIN", "users", user.id)
    await db.commit()

    user_response = (
        UserResponse.model_validate(user)
        if hasattr(UserResponse, "model_validate")
        else UserResponse.from_orm(user)
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user_response
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
