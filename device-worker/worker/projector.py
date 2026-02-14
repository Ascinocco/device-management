import logging
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from worker.circuit_breaker import CircuitBreaker
from worker.settings import settings

logger = logging.getLogger(__name__)


def _http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(
            settings.http_timeout,
            connect=settings.http_connect_timeout,
        )
    )


async def resolve_user_email(
    user_id: str,
    tenancy_breaker: CircuitBreaker,
) -> str | None:
    """Resolve email from Tenancy Service via circuit breaker. Returns None if not found."""

    async def _call() -> str | None:
        async with _http_client() as client:
            res = await client.get(
                f"{settings.tenancy_service_url}/internal/user-email/{user_id}",
                headers={"x-internal-token": settings.tenancy_service_token},
            )
            if res.status_code != 200:
                return None
            return res.json().get("email")

    return await tenancy_breaker.call(_call)


async def project_event(
    conn: AsyncConnection,
    event_type: str,
    payload: dict[str, Any],
    tenancy_breaker: CircuitBreaker,
) -> None:
    """Update the device_read_model based on an outbox event."""

    device_id = payload.get("device_id")
    if not device_id:
        return

    if event_type == "device.created":
        user_id = payload.get("user_id")
        owner_email = await resolve_user_email(user_id, tenancy_breaker) if user_id else None

        await conn.execute(
            text(
                """
                INSERT INTO device_read_model (id, tenant_id, mac_address, status, owner_email, created_at, updated_at, version)
                SELECT d.id, d.tenant_id, d.mac_address, d.status, :owner_email, d.created_at, d.updated_at, d.version
                FROM devices d
                WHERE d.id = :device_id
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    owner_email = COALESCE(:owner_email, device_read_model.owner_email),
                    updated_at = EXCLUDED.updated_at,
                    version = EXCLUDED.version
                """
            ),
            {"device_id": device_id, "owner_email": owner_email},
        )

    elif event_type in ("device.retired", "device.activated"):
        await conn.execute(
            text(
                """
                UPDATE device_read_model
                SET status = d.status, updated_at = d.updated_at, version = d.version
                FROM devices d
                WHERE device_read_model.id = :device_id
                  AND d.id = :device_id
                """
            ),
            {"device_id": device_id},
        )
