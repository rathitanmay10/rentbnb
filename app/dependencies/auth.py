from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.database.session import async_session
from app.models import User
from app.utils.jwt_handler import ALGO, SECRET

security = HTTPBearer(scheme_name="Bearer", description="Enter your JWT access token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    authorization: str | None = Header(default=None),
) -> User | None:

    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split()[1]

    try:
        payload = jwt.decode(
            token,
            SECRET,
            algorithms=[ALGO],
            options={"verify_exp": True},
        )
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Access token required")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token payload")

    async with async_session() as db:
        user = await db.get(User, UUID(user_id))

    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    if payload.get("token_version") != user.token_version:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalidated")

    return user
