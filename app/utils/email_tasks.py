from app.config.settings import settings


def build_verification_email(token: str, email: str):
    subject = "Verify your email"
    body = (
        f"Please verify your email by clicking this link: "
        f"{settings.FRONTEND_URL}/verify-email?token={token}"
    )
    return email, subject, body
