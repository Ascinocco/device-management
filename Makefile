.PHONY: run docker-up docker-down install test

# Run all services locally (requires pnpm, uv)
run:
	./run-all.sh

# Start all services via Docker Compose
docker-up:
	docker compose up --build -d

# Stop all Docker Compose services
docker-down:
	docker compose down

# Install dependencies for all services
install:
	cd api-gateway     && pnpm install
	cd tenancy-service && pnpm install
	cd device-ui       && pnpm install
	cd device-service  && uv sync
	cd device-worker   && uv sync

# Run tests for all services that have them
test:
	cd api-gateway     && pnpm test
	cd tenancy-service && pnpm test
	cd device-worker   && uv run pytest
