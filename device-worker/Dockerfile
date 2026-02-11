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
COPY worker/ worker/

# Now install the project itself
RUN uv sync --frozen --no-dev

CMD ["uv", "run", "worker"]
