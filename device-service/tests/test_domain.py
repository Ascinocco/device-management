"""Domain model unit tests — no I/O, no mocks, pure logic."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.contracts import ValidationError
from app.domain.devices import Device, DeviceStatus, normalize_mac

TENANT = uuid4()
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
LATER = datetime(2026, 1, 2, tzinfo=timezone.utc)


def _active_device(**overrides) -> Device:
    defaults = dict(
        id=uuid4(),
        tenant_id=TENANT,
        mac_address="aa:bb:cc:dd:ee:ff",
        status=DeviceStatus.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
        version=1,
    )
    return Device(**{**defaults, **overrides})


# ── normalize_mac ─────────────────────────────────────────────────


class TestNormalizeMac:
    def test_colon_format(self):
        assert normalize_mac("AA:BB:CC:DD:EE:FF") == "aa:bb:cc:dd:ee:ff"

    def test_dash_format(self):
        assert normalize_mac("AA-BB-CC-DD-EE-FF") == "aa:bb:cc:dd:ee:ff"

    def test_raw_hex(self):
        assert normalize_mac("aabbccddeeff") == "aa:bb:cc:dd:ee:ff"

    def test_strips_whitespace(self):
        assert normalize_mac("  AA:BB:CC:DD:EE:FF  ") == "aa:bb:cc:dd:ee:ff"

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="required"):
            normalize_mac("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError, match="required"):
            normalize_mac("   ")

    def test_invalid_hex_raises(self):
        with pytest.raises(ValidationError, match="Invalid"):
            normalize_mac("ZZZZZZZZZZZZ")

    def test_short_raises(self):
        with pytest.raises(ValidationError, match="Invalid"):
            normalize_mac("aabb")


# ── Device.retire ────────────────────────────────────────────────


class TestDeviceRetire:
    def test_retire_active_device(self):
        device = _active_device()
        retired = device.retire("End of life", LATER)

        assert retired.status == DeviceStatus.RETIRED
        assert retired.updated_at == LATER
        assert retired.id == device.id
        assert retired.mac_address == device.mac_address

    def test_retire_already_retired_raises(self):
        device = _active_device(status=DeviceStatus.RETIRED)
        with pytest.raises(ValidationError, match="already retired"):
            device.retire("reason", LATER)

    def test_retire_empty_reason_raises(self):
        device = _active_device()
        with pytest.raises(ValidationError, match="reason"):
            device.retire("", LATER)

    def test_retire_whitespace_reason_raises(self):
        device = _active_device()
        with pytest.raises(ValidationError, match="reason"):
            device.retire("   ", LATER)


# ── Device.activate ──────────────────────────────────────────────


class TestDeviceActivate:
    def test_activate_retired_device(self):
        device = _active_device(status=DeviceStatus.RETIRED)
        active = device.activate("Back in service", LATER)

        assert active.status == DeviceStatus.ACTIVE
        assert active.updated_at == LATER

    def test_activate_already_active_raises(self):
        device = _active_device()
        with pytest.raises(ValidationError, match="already active"):
            device.activate("reason", LATER)

    def test_activate_empty_reason_raises(self):
        device = _active_device(status=DeviceStatus.RETIRED)
        with pytest.raises(ValidationError, match="reason"):
            device.activate("", LATER)


# ── Device is frozen ─────────────────────────────────────────────


class TestDeviceImmutability:
    def test_device_is_frozen(self):
        device = _active_device()
        with pytest.raises(AttributeError):
            device.status = DeviceStatus.RETIRED  # type: ignore[misc]
