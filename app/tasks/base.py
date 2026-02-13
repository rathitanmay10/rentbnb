import asyncio
from functools import wraps

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.database.session import get_task_engine


def db_async_task(f):
    """
    Decorator to run an async task with a fresh, disposed-on-exit database engine.
    Injects the 'db' session as the first argument to the decorated function.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        async def _run():
            task_engine = get_task_engine()
            task_session_factory = async_sessionmaker(
                task_engine, expire_on_commit=False, autoflush=False
            )

            try:
                async with task_session_factory() as db:
                    return await f(db, *args, **kwargs)
            finally:
                await task_engine.dispose()

        return asyncio.run(_run())

    return wrapper
