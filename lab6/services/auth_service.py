import uuid
from typing import Optional

from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from repository import user_repository
from schemas.user import UserCreate

# Whitelist of valid refresh tokens (in-memory; lost on restart)
_refresh_tokens: set[str] = set()


async def register(db: AsyncSession, data: UserCreate) -> Optional[object]:
    if await user_repository.get_by_username(db, data.username):
        return None  # duplicate username
    role = data.role if data.role in ("admin", "user") else "user"
    return await user_repository.create(db, {
        "id": str(uuid.uuid4()),
        "username": data.username,
        "hashed_password": hash_password(data.password),
        "role": role,
        "is_active": True,
    })


async def login(db: AsyncSession, username: str, password: str) -> Optional[dict]:
    user = await user_repository.get_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password) or not user.is_active:
        return None
    access = create_access_token(user.id, user.username, user.role)
    refresh = create_refresh_token(user.id)
    _refresh_tokens.add(refresh)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


async def refresh(db: AsyncSession, refresh_token: str) -> Optional[dict]:
    if refresh_token not in _refresh_tokens:
        return None
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            return None
        user_id = payload["sub"]
    except InvalidTokenError:
        _refresh_tokens.discard(refresh_token)
        return None

    user = await user_repository.get_by_id(db, user_id)
    if not user or not user.is_active:
        _refresh_tokens.discard(refresh_token)
        return None

    # Rotate: invalidate old token, issue new pair
    _refresh_tokens.discard(refresh_token)
    new_access = create_access_token(user.id, user.username, user.role)
    new_refresh = create_refresh_token(user.id)
    _refresh_tokens.add(new_refresh)
    return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}


def logout(refresh_token: str) -> None:
    _refresh_tokens.discard(refresh_token)


def clear_refresh_tokens() -> None:
    """For testing only."""
    _refresh_tokens.clear()
