FROM python:3.13-slim

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies only (skip building the project itself)
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY README.md ./
COPY app/ app/
COPY infra/ infra/
COPY alembic/ alembic/
COPY alembic.ini ./

# Now install the project itself
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
