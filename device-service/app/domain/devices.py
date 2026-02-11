from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID
import re

from app.contracts import ValidationError

MAC_HEX_PATTERN = re.compile(r"^[0-9a-f]{12}$")


class DeviceStatus(str, Enum):
    ACTIVE = "active"
    RETIRED = "retired"


def normalize_mac(value: str) -> str:
    raw = value.strip().lower()
    if not raw:
        raise ValidationError("MAC address is required")
    raw = raw.replace(":", "").replace("-", "")
    if not MAC_HEX_PATTERN.match(raw):
        raise ValidationError("Invalid MAC address format")
    return ":".join(raw[i : i + 2] for i in range(0, 12, 2))


@dataclass(frozen=True)
class Device:
    id: UUID
    tenant_id: UUID
    mac_address: str
    status: DeviceStatus
    created_at: datetime
    updated_at: datetime
    version: int

    def retire(self, reason: str, now: datetime) -> "Device":
        if self.status == DeviceStatus.RETIRED:
            raise ValidationError("Device already retired")
        if not reason.strip():
            raise ValidationError("Retire reason is required")
        return Device(
            id=self.id,
            tenant_id=self.tenant_id,
            mac_address=self.mac_address,
            status=DeviceStatus.RETIRED,
            created_at=self.created_at,
            updated_at=now,
            version=self.version,
        )

    def activate(self, reason: str, now: datetime) -> "Device":
        if self.status == DeviceStatus.ACTIVE:
            raise ValidationError("Device already active")
        if not reason.strip():
            raise ValidationError("Activation reason is required")
        return Device(
            id=self.id,
            tenant_id=self.tenant_id,
            mac_address=self.mac_address,
            status=DeviceStatus.ACTIVE,
            created_at=self.created_at,
            updated_at=now,
            version=self.version,
        )