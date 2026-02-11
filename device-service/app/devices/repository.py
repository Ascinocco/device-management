from typing import Protocol
from uuid import UUID

from app.domain.devices import Device


class DeviceRepository(Protocol):
    async def exists_by_mac(self, tenant_id: UUID, mac_address: str) -> bool:
        ...

    async def add(self, device: Device) -> None:
        ...

    async def count_by_tenant(self, tenant_id: UUID) -> int:
        ...

    async def list_by_tenant(self, tenant_id: UUID, limit: int, offset: int) -> list[Device]:
        """Must order by created_at ASC, id ASC for stable pagination."""
        ...

    async def get_by_id(self, tenant_id: UUID, device_id: UUID) -> Device | None:
        ...

    async def update(self, device: Device, expected_version: int) -> bool:
        """Return True if update succeeded, False on version conflict."""
        ...