import asyncio
import logging
import os
import sys

# Add the project root to the python path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.crud.user_crud import create_user, get_user_by_email_ci
from app.database.session import async_session
from app.enums.user_role import UserRole
from app.utils.password import hash_password

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_super_admin():
    """Seeds a super admin user if not already present."""
    email = os.getenv("SUPER_ADMIN_EMAIL", "superadmin@yopmail.com")
    password = os.getenv("SUPER_ADMIN_PASSWORD", "Admin@123")
    username = os.getenv("SUPER_ADMIN_USERNAME", "superadmin")

    async with async_session() as db:
        try:
            user = await get_user_by_email_ci(db, email)
            if user:
                logger.info(f"Super admin with email {email} already exists.")
                return

            logger.info(f"Creating super admin with email {email}...")

            hashed_password = hash_password(password)

            user_data = {
                "email": email,
                "username": username,
                "hashed_password": hashed_password,
                "role": UserRole.SUPER_ADMIN,
                "is_active": True,
                "is_verified": True,
                "tenant_id": None,  # Super admin is not bound to a tenant
            }

            await create_user(db, user_data)
            await db.commit()
            logger.info("Super admin created successfully.")

        except Exception as e:
            logger.error(f"Error seeding super admin: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_super_admin())
