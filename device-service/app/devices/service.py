from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.contracts import (
    ConflictError,
    DataResponse,
    ListResponse,
    PageMeta,
    RequestContext,
    ValidationError,
    NotFoundError,
)
from app.devices.dto import ChangeDeviceStatusCommand, CreateDeviceCommand, DeviceView, ListDevicesQuery
from app.devices.mapper import to_device_view
from app.devices.repository import DeviceRepository
from app.domain.devices import Device, DeviceStatus, normalize_mac
from app.outbox.events import OutboxEvent
from app.outbox.repository import OutboxRepository


class DevicesApplicationService:
    def __init__(self, repo: DeviceRepository, outbox: OutboxRepository) -> None:
        self._repo = repo
        self._outbox = outbox

    async def create(self, ctx: RequestContext, cmd: CreateDeviceCommand) -> DataResponse[DeviceView]:
        mac = normalize_mac(cmd.mac_address)
        if await self._repo.exists_by_mac(ctx.tenant_id, mac):
            raise ValidationError("MAC address already exists for tenant")

        now = datetime.now(timezone.utc)
        device = Device(
            id=uuid4(),
            tenant_id=ctx.tenant_id,
            mac_address=mac,
            status=DeviceStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            version=1,
        )
        await self._repo.add(device)
        await self._outbox.add(
            OutboxEvent(
                id=uuid4(),
                tenant_id=ctx.tenant_id,
                event_type="device.created",
                payload={"device_id": str(device.id), "user_id": str(ctx.user_id)},
                created_at=datetime.now(timezone.utc),
            )
        )
        return DataResponse(data=to_device_view(device))

    async def get(self, ctx: RequestContext, device_id: UUID) -> DataResponse[DeviceView]:
        device = await self._repo.get_by_id(ctx.tenant_id, device_id)
        if not device:
            raise NotFoundError("Device not found")
        return DataResponse(data=to_device_view(device))

    async def list(self, ctx: RequestContext, query: ListDevicesQuery) -> ListResponse[DeviceView]:
        total = await self._repo.count_by_tenant(ctx.tenant_id)
        devices = await self._repo.list_by_tenant(
            ctx.tenant_id,
            limit=query.limit,
            offset=query.offset,
        )
        data = [to_device_view(d) for d in devices]
        page = PageMeta(
            limit=query.limit,
            offset=query.offset,
            total=total,
            has_next=query.offset + len(data) < total,
            order_by=["created_at", "id"],
        )
        return ListResponse(data=data, page=page)

    async def retire(
        self, ctx: RequestContext, device_id: UUID, cmd: ChangeDeviceStatusCommand
    ) -> DataResponse[DeviceView]:
        device = await self._repo.get_by_id(ctx.tenant_id, device_id)
        if not device:
            raise NotFoundError("Device not found")

        retired = device.retire(cmd.reason, datetime.now(timezone.utc))
        updated = await self._repo.update(retired, cmd.expected_version)
        if not updated:
            still_exists = await self._repo.get_by_id(ctx.tenant_id, device_id)
            if not still_exists:
                raise NotFoundError("Device not found")
            raise ConflictError("Device was updated by another request")
        await self._outbox.add(
            OutboxEvent(
                id=uuid4(),
                tenant_id=ctx.tenant_id,
                event_type="device.retired",
                payload={
                    "device_id": str(device.id),
                    "user_id": str(ctx.user_id),
                    "reason": cmd.reason,
                },
                created_at=datetime.now(timezone.utc),
            )
        )
        return DataResponse(data=to_device_view(retired))

    async def activate(
        self, ctx: RequestContext, device_id: UUID, cmd: ChangeDeviceStatusCommand
    ) -> DataResponse[DeviceView]:
        device = await self._repo.get_by_id(ctx.tenant_id, device_id)
        if not device:
            raise NotFoundError("Device not found")

        active = device.activate(cmd.reason, datetime.now(timezone.utc))
        updated = await self._repo.update(active, cmd.expected_version)
        if not updated:
            still_exists = await self._repo.get_by_id(ctx.tenant_id, device_id)
            if not still_exists:
                raise NotFoundError("Device not found")
            raise ConflictError("Device was updated by another request")
        await self._outbox.add(
            OutboxEvent(
                id=uuid4(),
                tenant_id=ctx.tenant_id,
                event_type="device.activated",
                payload={
                    "device_id": str(device.id),
                    "user_id": str(ctx.user_id),
                    "reason": cmd.reason,
                },
                created_at=datetime.now(timezone.utc),
            )
        )
        return DataResponse(data=to_device_view(active))