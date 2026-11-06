"""Auth - bcrypt password hashing + JWT tokens (HS256).

Uses the ``bcrypt`` package directly instead of passlib so we are not
subject to passlib's 72-byte handling / version-probe issues with
bcrypt 4.x. bcrypt silently truncates at 72 bytes on both sides as long
as we pre-encode; we pre-truncate defensively to make the behaviour
explicit and deterministic.

JWTs are issued and verified with PyJWT. python-jose was used previously but
carries unfixed advisories (PYSEC-2026-4298, plus PYSEC-2026-1325 in its
``ecdsa`` dependency) with no released fix, so it was replaced. ``PyJWTError``
is PyJWT's root exception type and stands in for the old ``JWTError``.
"""
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from sqlalchemy.orm import Session

from .config import settings
from .database import User, get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=True)

_BCRYPT_MAX_BYTES = 72


def _encode_password(plain: str) -> bytes:
    b = plain.encode("utf-8")
    return b[:_BCRYPT_MAX_BYTES]


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(_encode_password(plain), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_encode_password(plain), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    minutes = expires_minutes or settings.JWT_EXPIRES_MINUTES
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {"sub": subject, "exp": exp, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _decode(token: str) -> str:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing subject")
    return sub


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    email = _decode(token)
    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_admin(current: User = Depends(get_current_user)) -> User:
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return current


def require_roles(*roles: str) -> Callable[..., User]:
    allowed = set(roles)

    def _dependency(current: User = Depends(get_current_user)) -> User:
        if current.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles is required: {', '.join(sorted(allowed))}",
            )
        return current

    return _dependency
