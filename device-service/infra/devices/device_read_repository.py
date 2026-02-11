from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DeviceReadRepository:
    """Read-only repository that queries the denormalized device_read_model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_tenant(
        self, tenant_id: UUID, limit: int, offset: int
    ) -> tuple[list[dict], int]:
        count_result = await self._session.execute(
            text("SELECT COUNT(*) FROM device_read_model WHERE tenant_id = :tid"),
            {"tid": tenant_id},
        )
        total = count_result.scalar_one()

        rows_result = await self._session.execute(
            text(
                """
                SELECT id, tenant_id, mac_address, status, owner_email, created_at, updated_at, version
                FROM device_read_model
                WHERE tenant_id = :tid
                ORDER BY created_at ASC, id ASC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"tid": tenant_id, "limit": limit, "offset": offset},
        )
        rows = rows_result.fetchall()

        data = [
            {
                "id": str(row.id),
                "mac_address": row.mac_address,
                "status": row.status,
                "owner_email": row.owner_email,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat(),
                "version": row.version,
            }
            for row in rows
        ]
        return data, total