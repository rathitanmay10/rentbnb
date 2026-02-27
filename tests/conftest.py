import factory
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.settings import settings
from app.database.base import Base
from app.database.init_db import get_db
from app.enums.user_role import UserRole
from app.main import app
from app.models import Amenity, User
from app.utils.jwt_handler import create_access_token
from app.utils.password import hash_password

# Create test DB engine
engine = create_async_engine(
    settings.TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def db_engine():
    """
    Creates and drops the database tables once per test session.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """
    Provides a fresh database session for each test.
    This session runs inside a transaction, which can be rolled back to isolate tests.
    """
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """
    Provides an async test client and overrides the database dependency to use the test session.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


class UserFactory(factory.Factory):
    class Meta:
        model = User
        exclude = ("password",)

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    password = factory.Faker("password")
    hashed_password = factory.LazyAttribute(lambda obj: hash_password(obj.password))
    role = UserRole.GUEST
    tenant_id = None
    is_active = True
    is_verified = True


class AmenityFactory(factory.Factory):
    class Meta:
        model = Amenity

    name = factory.Faker("word")


@pytest_asyncio.fixture
async def create_sample_guest_user(db_session: AsyncSession):
    user = UserFactory.build()
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def create_guest_user_token(create_sample_guest_user):
    token = create_access_token(create_sample_guest_user)
    return token


@pytest_asyncio.fixture
async def create_sample_admin_user(db_session: AsyncSession):
    user = UserFactory.build(role=UserRole.SUPER_ADMIN)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def create_admin_user_token(create_sample_admin_user):
    token = create_access_token(create_sample_admin_user)
    return token


@pytest_asyncio.fixture
async def create_sample_amenity(db_session: AsyncSession):
    amenity = AmenityFactory.build()
    db_session.add(amenity)
    await db_session.commit()
    await db_session.refresh(amenity)
    return amenity
