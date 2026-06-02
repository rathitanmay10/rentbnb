import asyncio
import hashlib
import hmac
import secrets
from uuid import UUID

from fastapi import BackgroundTasks

from app.constants.auth_ttl import OTP_COOLDOWN, OTP_MAX_ATTEMPTS, OTP_TTL
from app.constants.messages import (
    OTP_COOLDOWN_MSG,
    OTP_INVALID,
    OTP_RATE_LIMITED,
    OTP_SENT,
)
from app.constants.redis_keys import (
    REDIS_OTP,
    REDIS_OTP_ATTEMPTS,
    REDIS_OTP_COOLDOWN,
    get_tenant_prefix,
)
from app.exceptions import BadRequestError, TooManyRequestsError
from app.services.email_service import email_service
from app.utils.redis_client import redis_client


class OTPHandler:
    @staticmethod
    async def send_otp(
        email: str, background_tasks: BackgroundTasks, tenant_id: UUID | None
    ) -> str:
        """
        Generates and sends a secure OTP to the given email.
        Enforces cooldown.
        """
        tenant_prefix = get_tenant_prefix(tenant_id)

        cooldown_key = f"{tenant_prefix}{REDIS_OTP_COOLDOWN.format(email=email)}"
        otp_key = f"{tenant_prefix}{REDIS_OTP.format(email=email)}"
        attempt_key = f"{tenant_prefix}{REDIS_OTP_ATTEMPTS.format(email=email)}"

        # Enforce cooldown
        if await redis_client.get(cooldown_key):
            raise TooManyRequestsError(OTP_COOLDOWN_MSG)

        # Generate 6-digit secure OTP
        otp = "".join(str(secrets.randbelow(10)) for _ in range(6))

        # Hash OTP before storing
        hashed_otp = hashlib.sha256(otp.encode()).hexdigest()

        # Store OTP + attempts + cooldown
        await redis_client.set(otp_key, hashed_otp, expire=OTP_TTL)
        await redis_client.set(attempt_key, 0, expire=OTP_TTL)
        await redis_client.set(cooldown_key, "1", expire=OTP_COOLDOWN)

        # Send Email in Background
        subject = "Your Login OTP"
        body = f"Your OTP is: {otp}. It expires in {OTP_TTL // 60} minutes."
        background_tasks.add_task(email_service.send_email, email, subject, body)

        return OTP_SENT

    @staticmethod
    async def verify_otp(email: str, otp: str, tenant_id: UUID | None) -> bool:
        """
        Verifies the provided OTP.
        Enforces max attempts.
        Returns True if valid, otherwise raises a domain error.
        """
        tenant_prefix = get_tenant_prefix(tenant_id)

        otp_key = f"{tenant_prefix}{REDIS_OTP.format(email=email)}"
        attempt_key = f"{tenant_prefix}{REDIS_OTP_ATTEMPTS.format(email=email)}"
        cooldown_key = f"{tenant_prefix}{REDIS_OTP_COOLDOWN.format(email=email)}"

        stored_otp = await redis_client.get(otp_key)
        # OTP expired or not found
        if not stored_otp:
            raise BadRequestError(OTP_INVALID)

        # Check attempts
        attempts = await redis_client.get(attempt_key)
        if attempts and int(attempts) >= OTP_MAX_ATTEMPTS:
            await redis_client.delete(otp_key, attempt_key, cooldown_key)
            raise TooManyRequestsError(OTP_RATE_LIMITED)

        # Hash incoming OTP for comparison
        hashed_input = hashlib.sha256(otp.encode()).hexdigest()

        # Constant-time comparison
        if not hmac.compare_digest(stored_otp, hashed_input):
            await redis_client.incr(attempt_key)
            await asyncio.sleep(0.5)

            raise BadRequestError(OTP_INVALID)

        await redis_client.delete(otp_key, attempt_key, cooldown_key)

        return True
