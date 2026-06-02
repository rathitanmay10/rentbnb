from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.utils.validators import validate_password, validate_username


class RegisterSchema(BaseModel):
    email: EmailStr = Field(max_length=255)
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def _validate_username(cls, v: str) -> str:
        return validate_username(v)

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v: str) -> str:
        return validate_password(v)


class VerifyEmailSchema(BaseModel):
    token: str


class EmailOnlySchema(BaseModel):
    email: EmailStr = Field(max_length=255)


class LoginSchema(BaseModel):
    email: EmailStr = Field(max_length=255)
    password: str


class VerifyLoginSchema(BaseModel):
    email: EmailStr = Field(max_length=255)
    otp: str = Field(min_length=6, max_length=6, description="6-digit OTP")


class TokenResponse(BaseModel):
    access: str
    refresh: str


class RefreshSchema(BaseModel):
    refresh: str


class ChangePasswordSchema(BaseModel):
    old_password: str = Field(min_length=1)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _validate_new_password(cls, v: str) -> str:
        return validate_password(v)

    @model_validator(mode="after")
    def check_passwords_different(self):
        if self.old_password == self.new_password:
            raise ValueError("New password must be different from old password")
        return self


class ForgotPasswordSchema(BaseModel):
    email: EmailStr = Field(max_length=255)


class ResetPasswordSchema(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _validate_new_password(cls, v: str) -> str:
        return validate_password(v)
