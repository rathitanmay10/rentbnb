from app.config.settings import settings
from app.models import Booking, Property


def build_verification_email(token: str, email: str):
    subject = "Verify your email"
    body = (
        f"Please verify your email by clicking this link: "
        f"{settings.FRONTEND_URL}/verify-email?token={token}"
    )
    return email, subject, body


def build_otp_email(otp: str, email: str):
    subject = "Your Login OTP"
    body = f"Your OTP for login is: {otp}. It expires in 5 minutes."
    return email, subject, body


def build_reset_password_email(token: str, email: str):
    subject = "Reset Password"
    body = (
        f"Please reset your password by clicking this link: "
        f"{settings.FRONTEND_URL}/reset-password?token={token}"
    )
    return email, subject, body


def build_booking_email(email: str, booking: Booking, property_obj: Property):
    subject = f"Booking Update: {booking.status}"
    body = (
        f"Your booking {booking.id} for {property_obj.name} "
        f"from {booking.check_in} to {booking.check_out} is now {booking.status}."
    )
    return email, subject, body
