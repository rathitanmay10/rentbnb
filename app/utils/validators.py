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


def validate_amenity_name(v: str) -> str:
    """
    Validate amenity name.

    Rules:
    - Minimum 2 characters
    - Normalized to lowercase
    """
    v = v.strip().lower()
    if len(v) < 2:
        raise ValueError("Amenity name must be at least 2 characters long")
    return v


def validate_first_name(v: str | None) -> str | None:
    """
    Validate first name.

    Rules:
    - Stripped of whitespace
    - Cannot be empty if provided
    - Maximum 150 characters
    """
    if v is None:
        return None
    v = v.strip()
    if not v:
        raise ValueError("First name cannot be empty")
    if len(v) > 150:
        raise ValueError("First name must be at most 150 characters long")
    return v


def validate_last_name(v: str | None) -> str | None:
    """
    Validate last name.

    Rules:
    - Stripped of whitespace
    - Maximum 150 characters
    """
    if v is None:
        return None
    v = v.strip()
    if not v:
        return None
    if len(v) > 150:
        raise ValueError("Last name must be at most 150 characters long")
    return v
