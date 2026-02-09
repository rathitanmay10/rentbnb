from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt

from app.config import settings

SECRET = settings.SECRET_KEY
ALGO = settings.ALGORITHM

ACCESS_EXPIRE_MIN = settings.ACCESS_EXPIRE_MIN
REFRESH_EXPIRE_DAYS = settings.REFRESH_EXPIRE_DAYS


def create_access_token(user):
    payload = {
        "sub": str(user.id),
        "jti": str(uuid4()),
        "token_version": user.token_version,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRE_MIN),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def create_refresh_token(user):
    payload = {
        "sub": str(user.id),
        "jti": str(uuid4()),
        "token_version": user.token_version,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)
