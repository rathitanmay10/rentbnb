from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import with_loader_criteria

from app.database.session import async_session
from app.dependencies.auth import get_current_user
from app.models import User
from app.models.mixins import TenantMixin


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_tenant_db(
    current_user: User | None = Depends(get_current_user),
) -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        if current_user and getattr(current_user, "tenant_id"):
            await session.execution_options(
                with_loader_criteria(
                    TenantMixin,
                    lambda cls: cls.tenant_id == current_user.tenant_id,
                    include_aliases=True,
                )
            )

        yield session
