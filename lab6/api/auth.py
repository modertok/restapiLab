from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.user import UserCreate, UserResponse
from schemas.token import LoginRequest, TokenResponse, RefreshRequest
from services import auth_service
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register(db, data)
    if user is None:
        raise HTTPException(status_code=409, detail="Username already exists")
    return user


@router.post("/login", response_model=TokenResponse, status_code=200)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    tokens = await auth_service.login(db, data.username, data.password)
    if tokens is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return tokens


@router.post("/refresh", response_model=TokenResponse, status_code=200)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    tokens = await auth_service.refresh(db, data.refresh_token)
    if tokens is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return tokens


@router.post("/logout", status_code=200)
async def logout(data: RefreshRequest):
    auth_service.logout(data.refresh_token)
    return {"message": "Successfully logged out"}
