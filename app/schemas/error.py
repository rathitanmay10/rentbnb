from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str


class FieldError(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    error: str
    fields: list[FieldError]


_err = {"model": ErrorResponse}
NOT_FOUND = {404: _err}
FORBIDDEN = {403: _err}
CONFLICT = {409: _err}
BAD_REQUEST = {400: _err}
UNAUTHORIZED = {401: _err}
TOO_MANY = {429: _err}
INTERNAL_SERVER_ERROR = {500: _err}
