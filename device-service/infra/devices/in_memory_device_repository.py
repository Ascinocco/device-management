from uuid import UUID

from app.domain.devices import Device
from app.devices.repository import DeviceRepository


class InMemoryDeviceRepository(DeviceRepository):
    def __init__(self) -> None:
        self._rows: list[Device] = []

    async def exists_by_mac(self, tenant_id: UUID, mac_address: str) -> bool:
        return any(
            row.tenant_id == tenant_id and row.mac_address == mac_address
            for row in self._rows
        )

    async def add(self, device: Device) -> None:
        self._rows.append(device)

    async def count_by_tenant(self, tenant_id: UUID) -> int:
        return sum(1 for row in self._rows if row.tenant_id == tenant_id)

    async def list_by_tenant(self, tenant_id: UUID, limit: int, offset: int) -> list[Device]:
        matches = [row for row in self._rows if row.tenant_id == tenant_id]
        matches.sort(key=lambda row: (row.created_at, row.id))
        return matches[offset : offset + limit]

    async def get_by_id(self, tenant_id: UUID, device_id: UUID) -> Device | None:
        for row in self._rows:
            if row.tenant_id == tenant_id and row.id == device_id:
                return row
        return None

    async def update(self, device: Device, expected_version: int) -> bool:
        for idx, row in enumerate(self._rows):
            if row.tenant_id == device.tenant_id and row.id == device.id:
                if row.version != expected_version:
                    return False
                self._rows[idx] = device
                return True
        return False