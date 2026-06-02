import razorpay
from starlette.concurrency import run_in_threadpool

from app.core import settings
from app.exceptions import BadRequestError, InternalError


class RazorpayClient:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
                raise ValueError("Razorpay credentials not configured")
            cls._client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
        return cls._client

    @classmethod
    async def create_order(cls, data: dict) -> dict:
        """Create a Razorpay order asynchronously."""
        client = cls.get_client()
        return await run_in_threadpool(client.order.create, data=data)

    @classmethod
    async def fetch_order(cls, order_id: str) -> dict:
        """Fetch a Razorpay order asynchronously."""
        client = cls.get_client()
        return await run_in_threadpool(client.order.fetch, order_id)

    @classmethod
    async def fetch_order_payments(cls, order_id: str) -> dict:
        """Fetch payments for a Razorpay order asynchronously."""
        client = cls.get_client()
        return await run_in_threadpool(client.order.payments, order_id)

    @classmethod
    async def fetch_payment(cls, payment_id: str) -> dict:
        """Fetch a Razorpay payment asynchronously."""
        client = cls.get_client()
        return await run_in_threadpool(client.payment.fetch, payment_id)

    @classmethod
    async def refund_payment(cls, payment_id: str, amount: int) -> dict:
        """Refund a Razorpay payment asynchronously."""
        client = cls.get_client()
        return await run_in_threadpool(client.payment.refund, payment_id, amount)

    @classmethod
    def verify_payment_signature(cls, data: dict):
        try:
            client = cls.get_client()
            return client.utility.verify_payment_signature(data)
        except razorpay.errors.SignatureVerificationError:
            raise BadRequestError("Invalid payment signature")
        except Exception as e:
            raise InternalError(str(e))

    @classmethod
    def verify_webhook_signature(
        cls, body: bytes | str, signature: str, webhook_secret: str
    ):
        """Verify webhook signature."""
        client = cls.get_client()
        if isinstance(body, bytes):
            body = body.decode("utf-8")

        client.utility.verify_webhook_signature(body, signature, webhook_secret)
