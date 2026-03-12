# ── Stage 1: builder ────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies into /app/.venv
RUN uv sync --frozen --no-dev --no-editable

# ── Stage 2: runtime ────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

# Install runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the pre-built virtualenv from builder
COPY --from=builder /app/.venv /app/.venv

# Make venv binaries available without activation
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy application source
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY static ./static
COPY uploads ./uploads

# Create log directory
RUN mkdir -p logs

EXPOSE 8000

# Default command: run FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
