import json
import logging
from datetime import datetime, timezone
from html import escape as html_escape
from typing import Any
from urllib.parse import quote as url_quote
from uuid import UUID, uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from worker.circuit_breaker import CircuitBreaker
from worker.settings import settings

logger = logging.getLogger(__name__)


def _http_client() -> httpx.AsyncClient:
    """Create an httpx client with configured timeouts."""
    return httpx.AsyncClient(
        timeout=httpx.Timeout(
            settings.http_timeout,
            connect=settings.http_connect_timeout,
        )
    )


class DeviceRetirementSaga:
    """Orchestrates post-retirement side effects with compensation."""

    SAGA_TYPE = "device.retirement"

    def __init__(
        self,
        conn: AsyncConnection,
        tenancy_breaker: CircuitBreaker,
        email_breaker: CircuitBreaker,
    ) -> None:
        self._conn = conn
        self._tenancy_breaker = tenancy_breaker
        self._email_breaker = email_breaker

    async def start(
        self,
        tenant_id: UUID,
        device_id: str,
        user_id: str,
        reason: str,
    ) -> None:
        saga_id = uuid4()
        now = datetime.now(timezone.utc)
        payload = {
            "device_id": device_id,
            "user_id": user_id,
            "reason": reason,
        }

        # Persist saga state
        await self._conn.execute(
            text(
                """
                INSERT INTO saga_state (id, tenant_id, saga_type, status, current_step, payload, created_at, updated_at)
                VALUES (:id, :tenant_id, :saga_type, 'running', 'notify', :payload, :now, :now)
                """
            ),
            {
                "id": saga_id,
                "tenant_id": tenant_id,
                "saga_type": self.SAGA_TYPE,
                "payload": json.dumps(payload),
                "now": now,
            },
        )

        # Execute steps
        try:
            logger.info("Saga %s starting notify step", saga_id)
            await self._step_notify(payload)
            await self._update_status(saga_id, "completed", "done")
            logger.info("Saga %s completed", saga_id)
        except Exception as exc:
            logger.warning("Saga %s notify failed: %s", saga_id, exc)
            await self._update_status(saga_id, "compensating", "reactivate", str(exc))
            try:
                logger.info("Saga %s compensating — reactivating device", saga_id)
                await self._step_compensate(tenant_id, device_id, reason)
                await self._update_status(saga_id, "compensated", "done")
                logger.info("Saga %s compensated", saga_id)
            except Exception as comp_exc:
                logger.error("Saga %s compensation failed: %s", saga_id, comp_exc)
                await self._update_status(saga_id, "failed", "reactivate", str(comp_exc))

    async def _step_notify(self, payload: dict[str, Any]) -> None:
        """Send retirement notification email. Raises on failure."""
        user_id = payload["user_id"]
        device_id = payload["device_id"]
        reason = payload.get("reason", "No reason provided")

        # Resolve email via circuit breaker
        async def _resolve() -> str:
            async with _http_client() as client:
                res = await client.get(
                    f"{settings.tenancy_service_url}/internal/user-email/{user_id}",
                    headers={"x-internal-token": settings.tenancy_service_token},
                )
                if res.status_code != 200:
                    raise RuntimeError(f"Could not resolve email for user {user_id}")
                email = res.json().get("email")
                if not email:
                    raise RuntimeError(f"No email found for user {user_id}")
                return email

        email = await self._tenancy_breaker.call(_resolve)

        # Send email via circuit breaker
        async def _send() -> None:
            async with _http_client() as client:
                res = await client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                    json={
                        "from": settings.resend_from,
                        "to": [email],
                        "subject": "Device retired",
                        "html": f"<p>Device <code>{html_escape(device_id)}</code> was retired.</p><p>Reason: {html_escape(reason)}</p>",
                    },
                )
                res.raise_for_status()

        await self._email_breaker.call(_send)

    async def _step_compensate(
        self, tenant_id: UUID, device_id: str, reason: str
    ) -> None:
        """Reactivate the device to undo the retirement."""
        async with _http_client() as client:
            res = await client.post(
                f"{settings.device_service_url}/api/v1/devices/{url_quote(device_id, safe='')}/activate",
                headers={
                    "x-user-id": "system",
                    "x-tenant-id": str(tenant_id),
                    "x-internal-token": settings.device_service_token,
                },
                json={
                    "reason": f"Saga compensation: notification failed after retirement (original reason: {reason})",
                },
            )
            res.raise_for_status()

    async def _update_status(
        self, saga_id: UUID, status: str, step: str, error: str | None = None
    ) -> None:
        await self._conn.execute(
            text(
                """
                UPDATE saga_state
                SET status = :status, current_step = :step, error = :error, updated_at = :now
                WHERE id = :id
                """
            ),
            {
                "id": saga_id,
                "status": status,
                "step": step,
                "error": error[:512] if error else None,
                "now": datetime.now(timezone.utc),
            },
        )
