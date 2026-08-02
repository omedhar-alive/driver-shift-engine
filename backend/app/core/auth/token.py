from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import settings


def create_access_token(
    driver_code: str,
    session_id: str,
    remember_me: bool = False,
) -> str:
    expire_minutes = (
        settings.remember_me_expire_minutes
        if remember_me
        else settings.access_token_expire_minutes
    )
    expire = datetime.now(UTC) + timedelta(minutes=expire_minutes)

    payload = {
        "sub": driver_code,
        "session_id": session_id,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])