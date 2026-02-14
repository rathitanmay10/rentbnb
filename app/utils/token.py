from jose import jwt

from app.config.settings import settings


def verify_token(token: str, token_type: str):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True},
        )
        if payload.get("type") != token_type:
            return None
        return payload
    except Exception:
        return None
