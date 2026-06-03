import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.constants.messages import INTERNAL_ERROR
from app.exceptions import AppError
from app.utils.db_errors import extract_pg_error

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppError):
    """Map domain errors to HTTP responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


async def db_exception_handler(request: Request, exc: IntegrityError):
    """
    Global handler for SQLAlchemy IntegrityError.
    Handles UNIQUE, NOT NULL, FK, CHECK, and all other constraint errors.
    """
    message = extract_pg_error(exc)
    logger.warning(f"Database integrity error: {message}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": message},
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    fields = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"] if x != "body") or "body"
        msg = error["msg"]
        fields.append({"field": field, "message": msg})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation failed", "fields": fields},
    )


async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": INTERNAL_ERROR},
    )
