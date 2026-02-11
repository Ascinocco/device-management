"""Service layer tests — mocked repository, no I/O."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.contracts import ConflictError, NotFoundError, RequestContext, ValidationError
from app.devices.dto import ChangeDeviceStatusCommand, CreateDeviceCommand, ListDevicesQuery
from app.devices.service import DevicesApplicationService
from app.domain.devices import Device, DeviceStatus

TENANT = uuid4()
USER = uuid4()
CTX = RequestContext(tenant_id=TENANT, user_id=USER)
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _device(device_id: UUID | None = None, **overrides) -> Device:
    defaults = dict(
        id=device_id or uuid4(),
        tenant_id=TENANT,
        mac_address="aa:bb:cc:dd:ee:ff",
        status=DeviceStatus.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
        version=1,
    )
    return Device(**{**defaults, **overrides})


def _make_service():
    repo = AsyncMock()
    outbox = AsyncMock()
    svc = DevicesApplicationService(repo, outbox)
    return svc, repo, outbox


# ── create ────────────────────────────────────────────────────────


class TestCreateDevice:
    @pytest.mark.asyncio
    async def test_create_success(self):
        svc, repo, outbox = _make_service()
        repo.exists_by_mac.return_value = False

        result = await svc.create(CTX, CreateDeviceCommand(mac_address="AA:BB:CC:DD:EE:FF"))

        assert result.data.mac_address == "aa:bb:cc:dd:ee:ff"
        assert result.data.status == DeviceStatus.ACTIVE
        repo.add.assert_awaited_once()
        outbox.add.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_mac_raises(self):
        svc, repo, _ = _make_service()
        repo.exists_by_mac.return_value = True

        with pytest.raises(ValidationError, match="already exists"):
            await svc.create(CTX, CreateDeviceCommand(mac_address="AA:BB:CC:DD:EE:FF"))

    @pytest.mark.asyncio
    async def test_create_emits_outbox_event(self):
        svc, repo, outbox = _make_service()
        repo.exists_by_mac.return_value = False

        await svc.create(CTX, CreateDeviceCommand(mac_address="AA:BB:CC:DD:EE:FF"))

        event = outbox.add.call_args[0][0]
        assert event.event_type == "device.created"
        assert event.tenant_id == TENANT


# ── get ───────────────────────────────────────────────────────────


class TestGetDevice:
    @pytest.mark.asyncio
    async def test_get_found(self):
        svc, repo, _ = _make_service()
        device = _device()
        repo.get_by_id.return_value = device

        result = await svc.get(CTX, device.id)

        assert result.data.id == device.id

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        svc, repo, _ = _make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await svc.get(CTX, uuid4())


# ── list ──────────────────────────────────────────────────────────


class TestListDevices:
    @pytest.mark.asyncio
    async def test_list_returns_page_meta(self):
        svc, repo, _ = _make_service()
        repo.count_by_tenant.return_value = 1
        repo.list_by_tenant.return_value = [_device()]

        result = await svc.list(CTX, ListDevicesQuery(limit=10, offset=0))

        assert result.page.total == 1
        assert result.page.has_next is False
        assert len(result.data) == 1


# ── retire ────────────────────────────────────────────────────────


class TestRetireDevice:
    @pytest.mark.asyncio
    async def test_retire_success(self):
        svc, repo, outbox = _make_service()
        device = _device()
        repo.get_by_id.return_value = device
        repo.update.return_value = True

        cmd = ChangeDeviceStatusCommand(reason="EOL", expected_version=1)
        result = await svc.retire(CTX, device.id, cmd)

        assert result.data.status == DeviceStatus.RETIRED
        outbox.add.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_retire_not_found(self):
        svc, repo, _ = _make_service()
        repo.get_by_id.return_value = None

        cmd = ChangeDeviceStatusCommand(reason="EOL", expected_version=1)
        with pytest.raises(NotFoundError):
            await svc.retire(CTX, uuid4(), cmd)

    @pytest.mark.asyncio
    async def test_retire_version_conflict(self):
        svc, repo, _ = _make_service()
        device = _device()
        repo.get_by_id.return_value = device
        repo.update.return_value = False

        cmd = ChangeDeviceStatusCommand(reason="EOL", expected_version=1)
        with pytest.raises(ConflictError):
            await svc.retire(CTX, device.id, cmd)

    @pytest.mark.asyncio
    async def test_retire_emits_event_with_reason(self):
        svc, repo, outbox = _make_service()
        device = _device()
        repo.get_by_id.return_value = device
        repo.update.return_value = True

        cmd = ChangeDeviceStatusCommand(reason="No longer needed", expected_version=1)
        await svc.retire(CTX, device.id, cmd)

        event = outbox.add.call_args[0][0]
        assert event.event_type == "device.retired"
        assert event.payload["reason"] == "No longer needed"


# ── activate ──────────────────────────────────────────────────────


class TestActivateDevice:
    @pytest.mark.asyncio
    async def test_activate_success(self):
        svc, repo, outbox = _make_service()
        device = _device(status=DeviceStatus.RETIRED)
        repo.get_by_id.return_value = device
        repo.update.return_value = True

        cmd = ChangeDeviceStatusCommand(reason="Back in service", expected_version=1)
        result = await svc.activate(CTX, device.id, cmd)

        assert result.data.status == DeviceStatus.ACTIVE
        outbox.add.assert_awaited_once()
