from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.devices import DeviceStatus


@dataclass(frozen=True)
class CreateDeviceCommand:
    mac_address: str


@dataclass(frozen=True)
class ChangeDeviceStatusCommand:
    reason: str
    expected_version: int


@dataclass(frozen=True)
class ListDevicesQuery:
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class DeviceView:
    id: UUID
    mac_address: str
    status: DeviceStatus
    created_at: datetime
    updated_at: datetime
    version: int