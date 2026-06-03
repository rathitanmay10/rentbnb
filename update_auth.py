import re
with open('app/services/auth_service.py', 'r') as f:
    content = f.read()

old_code = """    # Scope redis key to tenant
    tenant_prefix = get_tenant_prefix(tenant_id)
    verification_key = (
        f"{tenant_prefix}{REDIS_VERIFICATION_EMAIL.format(email=register_data.email)}"
    )
    if await redis_client.get(verification_key) is not None:
        raise TooManyRequestsError("Verification email already sent. Please wait.")

    user_data = UserCreate(
        username=register_data.username,
        email=register_data.email,
        ******
        tenant_id=tenant_id,
        role=UserRole.GUEST,
    )"""

new_code = """    # Normalize email once
    email = register_data.email.strip().lower()

    # Scope redis key to tenant
    tenant_prefix = get_tenant_prefix(tenant_id)
    verification_key = (
        f"{tenant_prefix}{REDIS_VERIFICATION_EMAIL.format(email=email)}"
    )
    if await redis_client.get(verification_key) is not None:
        raise TooManyRequestsError("Verification email already sent. Please wait.")

    user_data = UserCreate(
        username=register_data.username,
        email=email,
        ******
        tenant_id=tenant_id,
        role=UserRole.GUEST,
    )"""

content = content.replace(old_code, new_code)
with open('app/services/auth_service.py', 'w') as f:
    f.write(content)
