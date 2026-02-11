import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from worker.circuit_breaker import CircuitBreaker, CircuitOpenError
from worker.projector import project_event
from worker.sagas import DeviceRetirementSaga
from worker.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Circuit breakers (one per external dependency) ────────────────
email_breaker = CircuitBreaker(
    failure_threshold=settings.cb_failure_threshold,
    recovery_timeout=settings.cb_recovery_timeout,
    name="resend",
)
tenancy_breaker = CircuitBreaker(
    failure_threshold=settings.cb_failure_threshold,
    recovery_timeout=settings.cb_recovery_timeout,
    name="tenancy",
)


def _http_client() -> httpx.AsyncClient:
    """Create an httpx client with configured timeouts."""
    return httpx.AsyncClient(
        timeout=httpx.Timeout(
            settings.http_timeout,
            connect=settings.http_connect_timeout,
        )
    )


async def resolve_user_email(user_id: str) -> str | None:
    async def _call() -> str | None:
        async with _http_client() as client:
            res = await client.get(
                f"{settings.tenancy_service_url}/internal/user-email/{user_id}",
                headers={"x-internal-token": settings.tenancy_service_token},
            )
            if res.status_code != 200:
                return None
            data = res.json()
            return data.get("email")

    return await tenancy_breaker.call(_call)


async def send_email(to_email: str, subject: str, body: str) -> None:
    async def _call() -> None:
        async with _http_client() as client:
            res = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={
                    "from": settings.resend_from,
                    "to": [to_email],
                    "subject": subject,
                    "html": body,
                },
            )
            res.raise_for_status()

    await email_breaker.call(_call)


async def handle_event(
    conn: AsyncConnection,
    event_type: str,
    payload: dict[str, Any],
    tenant_id: UUID,
) -> None:
    user_id = payload.get("user_id")
    if not user_id:
        return

    if event_type == "device.retired":
        saga = DeviceRetirementSaga(conn)
        await saga.start(
            tenant_id=tenant_id,
            device_id=payload["device_id"],
            user_id=user_id,
            reason=payload.get("reason", ""),
        )
        return

    # Non-saga events: simple email notification
    email = await resolve_user_email(user_id)
    if not email:
        return

    if event_type == "device.activated":
        await send_email(email, "Device activated", "Your device is active.")
    elif event_type == "device.created":
        await send_email(email, "Device registered", "Your device has been registered.")


def _backoff_delay(attempt: int) -> float:
    """Exponential backoff with full jitter."""
    delay = min(
        settings.retry_base_delay * (2 ** attempt),
        settings.retry_max_delay,
    )
    return random.uniform(0, delay)


async def poll_loop() -> None:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    max_attempts = settings.retry_max_attempts
    logger.info("Worker started, polling every %ds", settings.poll_interval_seconds)

    while True:
        async with engine.begin() as conn:
            rows = await conn.execute(
                text(
                    """
                    SELECT id, event_type, payload, attempts, tenant_id
                    FROM outbox
                    WHERE processed_at IS NULL
                    ORDER BY created_at ASC
                    LIMIT 10
                    FOR UPDATE SKIP LOCKED
                    """
                )
            )
            events = rows.fetchall()

            if events:
                logger.info("Polled %d event(s) from outbox", len(events))

            for row in events:
                attempts = int(row.attempts)
                try:
                    logger.info("Processing outbox id=%s event_type=%s", row.id, row.event_type)
                    await handle_event(conn, row.event_type, row.payload, row.tenant_id)
                    await project_event(conn, row.event_type, row.payload)
                    await conn.execute(
                        text(
                            """
                            UPDATE outbox
                            SET processed_at = :now
                            WHERE id = :id
                            """
                        ),
                        {"id": row.id, "now": datetime.now(timezone.utc)},
                    )
                    logger.info("Outbox id=%s processed OK", row.id)
                except CircuitOpenError as exc:
                    logger.warning(
                        "Outbox id=%s skipped — circuit open: %s",
                        row.id, exc,
                    )
                except Exception as exc:
                    attempts += 1
                    delay = _backoff_delay(attempts)
                    logger.warning(
                        "Outbox id=%s failed (attempt %d/%d, next backoff %.1fs): %s",
                        row.id, attempts, max_attempts, delay, exc,
                    )
                    await conn.execute(
                        text(
                            """
                            UPDATE outbox
                            SET attempts = :attempts, last_error = :err
                            WHERE id = :id
                            """
                        ),
                        {"id": row.id, "attempts": attempts, "err": str(exc)[:512]},
                    )
                    if attempts >= max_attempts:
                        logger.error("Outbox id=%s dead-lettered after %d attempts", row.id, max_attempts)
                        await conn.execute(
                            text("UPDATE outbox SET processed_at = :now WHERE id = :id"),
                            {"id": row.id, "now": datetime.now(timezone.utc)},
                        )

        await asyncio.sleep(settings.poll_interval_seconds)


def main() -> None:
    asyncio.run(poll_loop())


if __name__ == "__main__":
    main()
