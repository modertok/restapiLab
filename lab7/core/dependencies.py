from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError

from core.security import decode_token

# auto_error=False lets us return 401 (not 403) when header is missing
_bearer = HTTPBearer(auto_error=False)


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[dict]:
    """Return user dict if token is valid, otherwise None (no exception)."""
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        return {
            "id": payload["sub"],
            "username": payload["username"],
            "role": payload["role"],
        }
    except InvalidTokenError:
        return None


def get_current_user(
    current_user: Optional[dict] = Depends(get_optional_user),
) -> dict:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authorization required")
    return current_user


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
