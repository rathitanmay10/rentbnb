from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import jwt

from app.config import settings

SECRET = settings.SECRET_KEY
ALGO = settings.ALGORITHM
ACCESS_EXPIRE_MIN = settings.ACCESS_EXPIRE_MIN
REFRESH_EXPIRE_DAYS = settings.REFRESH_EXPIRE_DAYS


def create_access_token(user):
    now = datetime.now(UTC)
    payload = {
        "sub": str(user.id),
        "jti": str(uuid4()),
        "token_version": user.token_version,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_EXPIRE_MIN),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def create_refresh_token(user):
    now = datetime.now(UTC)
    payload = {
        "sub": str(user.id),
        "jti": str(uuid4()),
        "token_version": user.token_version,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)
