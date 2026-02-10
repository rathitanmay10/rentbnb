import re

USERNAME_REGEX = r"^[a-z0-9_]{5,150}$"


def validate_username(v: str) -> str:
    """
    Validate username format.

    Rules:
    - Must be 5-150 characters
    - Only lowercase letters, numbers, and underscores
    - No spaces allowed
    """
    v = v.strip().lower()

    if " " in v:
        raise ValueError("Username cannot contain spaces.")

    if not re.fullmatch(USERNAME_REGEX, v):
        raise ValueError(
            "Username must be 5-150 characters and contain only letters, numbers, and underscores"
        )
    return v


def validate_password(v: str) -> str:
    """
    Validate password strength.

    Rules:
    - Minimum 8 characters
    - Must contain both letters and numbers
    - No spaces allowed
    """
    v = v.strip()

    if " " in v:
        raise ValueError("Password cannot contain spaces.")

    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    if not (re.search(r"[a-zA-Z]", v) and re.search(r"[0-9]", v)):
        raise ValueError("Password must contain both letters and numbers.")

    return v


def validate_tenant_name(v: str | None) -> str | None:
    """
    Validate tenant name.

    Rules:
    - Minimum 5 characters
    - Normalized to lowercase
    """
    if v is None:
        raise ValueError("Tenant name cannot be null")
    v = v.strip().lower()
    if len(v) < 5:
        raise ValueError("Tenant name must be at least 5 characters long")
    return v
