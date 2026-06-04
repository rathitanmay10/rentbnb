"""Domain-level exceptions.

Services and utilities raise these instead of ``HTTPException`` so business
logic stays decoupled from the HTTP transport. ``app_exception_handler`` in
``app/utils/exception_handlers.py`` maps each to an HTTP response.
"""


class AppError(Exception):
    """Base class for all domain errors. Maps to an HTTP status code."""

    status_code: int = 500

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    status_code = 404


class ForbiddenError(AppError):
    status_code = 403


class ConflictError(AppError):
    status_code = 409


class BadRequestError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class TooManyRequestsError(AppError):
    status_code = 429


class InternalError(AppError):
    status_code = 500
