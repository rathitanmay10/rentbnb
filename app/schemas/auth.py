from pydantic import BaseModel, EmailStr, field_validator

from app.utils.validators import validate_password, validate_username


class RegisterSchema(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def _validate_username(cls, v):
        return validate_username(v)

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v):
        return validate_password(v)


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access: str
    refresh: str


class RefreshSchema(BaseModel):
    refresh: str


class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _validate_new_password(cls, v):
        return validate_password(v)
