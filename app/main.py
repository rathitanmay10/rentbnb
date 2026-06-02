from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import setup_logging
from app.core.settings import settings
from app.exceptions import AppError
from app.routers import (
    amenity,
    auth,
    booking,
    dashboard,
    message,
    payment,
    property,
    review,
    tenant,
    user,
    websocket,
)
from app.utils.exception_handlers import (
    app_exception_handler,
    db_exception_handler,
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.utils.redis_client import redis_client

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
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

app.add_exception_handler(AppError, app_exception_handler)
app.add_exception_handler(IntegrityError, db_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# API v1 router
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth.router)
api_v1.include_router(user.router)
api_v1.include_router(tenant.router)
api_v1.include_router(property.router)
api_v1.include_router(amenity.router)
api_v1.include_router(booking.router)
api_v1.include_router(payment.router)
api_v1.include_router(message.router)
api_v1.include_router(review.router)
api_v1.include_router(dashboard.router)

app.include_router(api_v1)
app.include_router(websocket.router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
