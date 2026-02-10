from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BlacklistedToken


async def is_token_blacklisted(db: AsyncSession, jti: str) -> bool:
    """Check if a token JTI is blacklisted."""
    query = select(BlacklistedToken).where(BlacklistedToken.jti == jti)
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def blacklist_token(
    db: AsyncSession, user_id: UUID, jti: str, expires_at: datetime
) -> BlacklistedToken:
    """Blacklist a token by its JTI."""
    blacklisted = BlacklistedToken(user_id=user_id, jti=jti, expires_at=expires_at)
    db.add(blacklisted)
    await db.flush()
    await db.refresh(blacklisted)
    return blacklisted


async def blacklist_all_user_tokens(db: AsyncSession, user_id: UUID) -> int:
    """
    Blacklist all tokens for a user by incrementing their token_version.
    Directly updates the user model to avoid circular dependency with user_crud.
    Returns 1 if successful, 0 otherwise.
    """
    from app.models import User

    user = await db.get(User, user_id)
    if not user:
        return 0

    user.token_version += 1
    await db.flush()
    return 1


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """Delete expired blacklisted tokens. Returns count of deleted tokens."""
    from sqlalchemy import delete

    stmt = delete(BlacklistedToken).where(
        BlacklistedToken.expires_at < datetime.now(UTC)
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount
