import re

from sqlalchemy.exc import IntegrityError


def extract_pg_error(e: IntegrityError) -> str:
    """
    Parse ANY IntegrityError from SQLAlchemy + asyncpg (async mode).
    Works for:
    - Unique constraint
    - Not-null constraint
    - Foreign key constraint
    - Check constraints
    - ANY other PostgreSQL constraint errors
    """

    text = str(e.orig) if hasattr(e, "orig") else str(e)

    # ----- UNIQUE -----
    if "duplicate key value" in text or "UniqueViolationError" in text:
        m = re.search(r"Key \((.+?)\)=\((.+?)\)", text)
        if m:
            col, val = m.groups()
            return f"{col.capitalize()} '{val}' already exists."
        return "Value already exists."

    # ----- NOT NULL -----
    if "NotNullViolationError" in text or "null value in column" in text:
        m = re.search(r'null value in column "(.+?)"', text, re.IGNORECASE)
        if m:
            col = m.group(1)
            return f"Field '{col}' cannot be null."
        return "A required field is missing."

    # ----- FOREIGN KEY -----
    if "ForeignKeyViolationError" in text or "violates foreign key constraint" in text:
        m = re.search(r"Key \((.+?)\)=\((.+?)\)", text)
        if m:
            col, val = m.groups()
            return f"Related {col} '{val}' does not exist."
        return "Foreign key constraint violated."

    # ----- CHECK CONSTRAINT -----
    if "CheckViolationError" in text or "check constraint" in text:
        return "Data did not meet required constraints."

    # ----- DEFAULT FALLBACK -----
    return text
