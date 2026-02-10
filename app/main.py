from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config.settings import settings
from app.routers import auth, tenant, user
from app.utils.exception_handlers import (
    db_exception_handler,
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.utils.redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify Redis connection
    try:
        await redis_client.get_client().ping()
    except Exception:
        raise

    yield

    # Shutdown
    await redis_client.close()


app = FastAPI(
    title="RentBnB API",
    description="Multi-tenant property rental management system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(IntegrityError, db_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# API v1 router
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth.router)
api_v1.include_router(tenant.router)
api_v1.include_router(user.router)

app.include_router(api_v1)
